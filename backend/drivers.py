import json
import re
import subprocess

from backend.privileges import is_admin

SCAN_TIMEOUT = 600
INSTALL_TIMEOUT = 1800

_GUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")

# Windows Update Agent ResultCode: 2 = succeeded, 3 = succeeded with errors.
_OK_CODES = (2,)

_PS_PRELUDE = "[Console]::OutputEncoding=[Text.Encoding]::UTF8;$ErrorActionPreference='Stop';"

_SCAN_SCRIPT = _PS_PRELUDE + (
    "$s=New-Object -ComObject Microsoft.Update.Session;"
    "$r=$s.CreateUpdateSearcher().Search(\"IsInstalled=0 and Type='Driver'\");"
    "$o=@();"
    "foreach($u in $r.Updates){$o+=[pscustomobject]@{"
    "title=$u.Title;update_id=$u.Identity.UpdateID;"
    "manufacturer=$u.DriverManufacturer;model=$u.DriverModel;"
    "size=[int64]$u.MaxDownloadSize}};"
    "ConvertTo-Json -InputObject @($o) -Compress"
)

_INSTALL_SCRIPT = _PS_PRELUDE + (
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
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-Command", script],
            capture_output=True, check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise DriverError("tempo esgotado aguardando o Windows Update")
    except OSError as exc:
        raise DriverError(f"não foi possível executar o PowerShell: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise DriverError(f"PowerShell retornou {result.returncode}: {detail}"[:300])
    return (result.stdout or b"").decode("utf-8-sig", errors="replace").strip()


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


def update_all_drivers(progress_callback=None, on_scan=None, dry_run=False):
    """Scans devices and updates drivers one at a time.

    Returns (results, reboot_required); results is a list of (title, status, note)
    where status is True (updated), False (failed) or None (skipped / dry-run).
    One failing driver never aborts the rest.
    """
    if not is_admin():
        return [("Drivers", None, "requer administrador")], False

    try:
        found = scan_drivers()
    except DriverError as exc:
        return [("Drivers", False, str(exc))], False

    if on_scan:
        on_scan(len(found))

    results = []
    reboot_required = False
    for item in found:
        title = item.get("title") or item.get("model") or "Driver"
        if progress_callback:
            progress_callback(title)
        if dry_run:
            results.append((title, None, "dry-run"))
            continue
        try:
            ok, reboot, note = install_driver(item.get("update_id"))
        except DriverError as exc:
            results.append((title, False, str(exc)))
            continue
        reboot_required = reboot_required or reboot
        results.append((title, ok, note))
    return results, reboot_required
