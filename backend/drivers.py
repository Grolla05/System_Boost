import json
import re

from backend import nvidia_driver
from backend._powershell import PS_PRELUDE, PowerShellError, run_powershell
from backend.logger import get_logger
from backend.privileges import is_admin

log = get_logger("drivers")

SCAN_TIMEOUT = 600
INSTALL_TIMEOUT = 1800

_GUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")

# Windows Update Agent ResultCode: 2 = succeeded, 3 = succeeded with errors.
_OK_CODES = (2,)

_SCAN_SCRIPT = PS_PRELUDE + (
    "$s=New-Object -ComObject Microsoft.Update.Session;"
    "$r=$s.CreateUpdateSearcher().Search(\"IsInstalled=0 and Type='Driver'\");"
    "$o=@();"
    "foreach($u in $r.Updates){$o+=[pscustomobject]@{"
    "title=$u.Title;update_id=$u.Identity.UpdateID;"
    "manufacturer=$u.DriverManufacturer;model=$u.DriverModel;"
    "size=[int64]$u.MaxDownloadSize}};"
    "ConvertTo-Json -InputObject @($o) -Compress"
)

_INSTALL_SCRIPT = PS_PRELUDE + (
    "$s=New-Object -ComObject Microsoft.Update.Session;"
    "$r=$s.CreateUpdateSearcher().Search(\"UpdateID='{update_id}'\");"
    "if($r.Updates.Count -eq 0){{throw 'update nao encontrado'}};"
    "$c=New-Object -ComObject Microsoft.Update.UpdateColl;"
    "[void]$c.Add($r.Updates.Item(0));"
    "$d=$s.CreateUpdateDownloader();$d.Updates=$c;[void]$d.Download();"
    "$i=$s.CreateUpdateInstaller();$i.Updates=$c;$res=$i.Install();"
    "ConvertTo-Json -Compress -InputObject @{{result=[int]$res.ResultCode;"
    "reboot=[bool]$res.RebootRequired}}"
)


class DriverError(Exception):
    """Raised when scanning or installing a driver update fails."""


def _run_powershell(script, timeout):
    try:
        return run_powershell(script, timeout)
    except PowerShellError as exc:
        raise DriverError(str(exc)) from exc


def _parse_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise DriverError(f"resposta inválida do Windows Update: {exc}")


def scan_drivers():
    """Returns pending driver updates offered by Windows Update, as a list of dicts."""
    data = _parse_json(_run_powershell(_SCAN_SCRIPT, SCAN_TIMEOUT))
    if data is None:
        return []
    return [data] if isinstance(data, dict) else list(data)


def install_driver(update_id):
    """Downloads and installs one driver update. Returns (ok, reboot_required, note)."""
    if not _GUID_RE.match(update_id or ""):
        raise DriverError(f"UpdateID inválido: {update_id!r}")
    data = _parse_json(_run_powershell(_INSTALL_SCRIPT.format(update_id=update_id), INSTALL_TIMEOUT))
    if not isinstance(data, dict):
        raise DriverError("resposta vazia do instalador")
    code = data.get("result")
    reboot = bool(data.get("reboot"))
    if code in _OK_CODES:
        return True, reboot, "reinicie para concluir" if reboot else "instalado"
    return False, reboot, f"falha na instalação (código {code})"


def update_all_drivers(progress_callback=None, on_scan=None, dry_run=False, on_result=None, on_notice=None):
    """Scans devices and updates drivers one at a time: Windows Update first, then NVIDIA.

    Returns (results, reboot_required); results is a list of (title, status, note)
    where status is True (updated), False (failed) or None (skipped / dry-run).
    One failing driver never aborts the rest. on_result(title, status, note), if given, is
    called as soon as each driver finishes (after the install attempt). on_notice(message), if
    given, receives warnings the user should see before a long step starts (NVIDIA screen flicker).
    """
    log.info("drivers: iniciando (dry_run=%s)", dry_run)
    if not is_admin():
        log.warning("drivers: pulado, requer administrador")
        return [("Drivers", None, "requer administrador")], False

    results = []
    reboot_required = False

    def record(title, status, note):
        results.append((title, status, note))
        if on_result:
            on_result(title, status, note)

    def install_one(title, install, error, notice=None):
        nonlocal reboot_required
        if progress_callback:
            progress_callback(title)
        if dry_run:
            record(title, None, "dry-run")
            return
        if notice and on_notice:
            on_notice(notice)
        try:
            ok, reboot, note = install()
        except error as exc:
            log.error("drivers: '%s' falhou: %s", title, exc)
            ok, reboot, note = False, False, str(exc)
        log.info("drivers: '%s' ok=%s reboot=%s nota=%s", title, ok, reboot, note)
        reboot_required = reboot_required or reboot
        record(title, ok, note)

    scan_failed = False
    try:
        found = scan_drivers()
    except DriverError as exc:
        log.error("drivers: falha no scan: %s", exc)
        results.append(("Drivers", False, str(exc)))
        found, scan_failed = [], True
    log.info("drivers: %d atualização(ões) pendente(s)", len(found))

    nvidia_update = None
    try:
        nvidia_update = nvidia_driver.check_update()
    except nvidia_driver.NvidiaDriverError as exc:
        log.error("drivers: NVIDIA não verificada: %s", exc)
        record("NVIDIA", None, str(exc))

    if on_scan and not scan_failed:
        on_scan(len(found) + (1 if nvidia_update else 0))

    for item in found:
        title = item.get("title") or item.get("model") or "Driver"
        install_one(title, lambda item=item: install_driver(item.get("update_id")), DriverError)

    if nvidia_update:
        install_one(
            nvidia_update.title, lambda: nvidia_driver.install_update(nvidia_update),
            nvidia_driver.NvidiaDriverError, notice=nvidia_driver.FLICKER_WARNING,
        )
    return results, reboot_required
