"""NVIDIA GPU driver updates, which Windows Update does not offer (or offers late).

Flow: detect an NVIDIA GPU and its installed driver, ask NVIDIA's public (unofficial) lookup
service for the newest Game Ready WHQL driver, and if it is newer download NVIDIA's official
package, check its Authenticode signature and run it silently. Every network/parse failure
surfaces as NvidiaDriverError so the caller can skip this step without aborting the others.
"""
import json
import re
import shutil
import subprocess
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from backend._powershell import PS_PRELUDE, PowerShellError, run_powershell
from backend.logger import get_logger

log = get_logger("nvidia_driver")

LOOKUP_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 60
INSTALL_TIMEOUT = 3600
POWERSHELL_TIMEOUT = 60

FLICKER_WARNING = (
    "Atenção: durante a instalação do driver NVIDIA a tela pode piscar ou ficar preta por "
    "alguns segundos. É normal — não desligue o computador."
)

_SERIES_URL = "https://www.nvidia.com/Download/API/lookupValueSearch.aspx?TypeID=2&ParentID=1"
_PRODUCTS_URL = "https://www.nvidia.com/Download/API/lookupValueSearch.aspx?TypeID=3&ParentID={psid}"
# osID=57: Windows 10/11 64-bit; upCRD=0: Game Ready (1 would be Studio); dch=1: DCH driver.
_DRIVER_URL = (
    "https://gfwsl.geforce.com/services_toolkit/services/com/nvidia/services/AjaxDriverService.php"
    "?func=DriverManualLookup&psid={psid}&pfid={pfid}&osID=57&languageCode=1033&beta=0&isWHQL=1"
    "&dltype=-1&dch=1&upCRD=0&qnf=0&sort1=1&numberOfResults=1"
)

_GPU_SCRIPT = PS_PRELUDE + (
    "ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_VideoController|"
    "ForEach-Object{[pscustomobject]@{name=$_.Name;driver_version=$_.DriverVersion}})"
)

_SIGNATURE_SCRIPT = PS_PRELUDE + (
    "$s=Get-AuthenticodeSignature -LiteralPath '{path}';"
    "ConvertTo-Json -Compress -InputObject @{{status=[string]$s.Status;"
    "subject=[string]$s.SignerCertificate.Subject}}"
)

_WINDOWS_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.\d{4}$")


class NvidiaDriverError(Exception):
    """Raised when the NVIDIA lookup, download, signature check or install fails."""


@dataclass(frozen=True)
class NvidiaUpdate:
    gpu: str
    installed: str
    latest: str
    url: str

    @property
    def title(self):
        return f"{self.gpu} → {self.latest}"


# --- versions ---------------------------------------------------------------------

def windows_to_nvidia_version(windows_version):
    """Maps Windows' driver version (31.0.15.5123) to NVIDIA's (551.23); None if unparsable."""
    if not isinstance(windows_version, str) or not _WINDOWS_VERSION_RE.match(windows_version.strip()):
        return None
    parts = windows_version.strip().split(".")
    digits = (parts[-2] + parts[-1])[-5:]
    if len(digits) < 5:
        return None
    return f"{digits[:3]}.{digits[3:]}"


def _version_key(version):
    major, _, minor = str(version).partition(".")
    return int(major), int(minor or 0)


def is_newer(latest, installed):
    """True if NVIDIA version string `latest` is greater than `installed`."""
    return _version_key(latest) > _version_key(installed)


# --- GPU detection -------------------------------------------------------------------

def get_nvidia_gpus():
    """Returns [{'name', 'driver_version'}] for every NVIDIA video controller."""
    text = run_powershell(_GPU_SCRIPT, POWERSHELL_TIMEOUT)
    if not text:
        return []
    data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    return [
        {"name": str(g.get("name") or ""), "driver_version": str(g.get("driver_version") or "")}
        for g in data if "nvidia" in str(g.get("name") or "").lower()
    ]


# --- NVIDIA lookup -----------------------------------------------------------------------

def _fetch(url, timeout=LOOKUP_TIMEOUT):
    """GET over HTTPS, returns the body bytes."""
    if not url.lower().startswith("https://"):
        raise NvidiaDriverError(f"URL não permitida: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "SystemBoost"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _lookup_values(xml_bytes):
    root = ET.fromstring(xml_bytes)
    return [
        ((node.findtext("Name") or "").strip(), (node.findtext("Value") or "").strip())
        for node in root.iter("LookupValue")
    ]


def _normalize_gpu_name(name):
    name = re.sub(r"\s+", " ", name.strip().lower())
    return name[len("nvidia "):] if name.startswith("nvidia ") else name


def find_product(gpu_name):
    """Resolves a Win32_VideoController name to NVIDIA's (series id, product id)."""
    wanted = _normalize_gpu_name(gpu_name)
    notebook = "laptop" in wanted or "notebook" in wanted
    model = re.search(r"\b(\d{2})\d{2}\b", wanted)
    prefix = f"{model.group(1)} series" if model else None

    series = [
        (name, value) for name, value in _lookup_values(_fetch(_SERIES_URL))
        if ("notebook" in name.lower()) == notebook
    ]
    # Series whose name carries the model's generation (e.g. 4070 -> "40 Series") go first.
    series.sort(key=lambda item: 0 if prefix and prefix in item[0].lower() else 1)

    for _, psid in series:
        for name, pfid in _lookup_values(_fetch(_PRODUCTS_URL.format(psid=psid))):
            if _normalize_gpu_name(name) == wanted:
                return psid, pfid
    raise NvidiaDriverError(f"GPU {gpu_name} não encontrada no catálogo da NVIDIA")


def validate_download_url(url):
    """Only https downloads of .exe files hosted on nvidia.com are accepted."""
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "nvidia.com" or host.endswith(".nvidia.com")):
        raise NvidiaDriverError(f"URL de download não confiável: {url}")
    if not parsed.path.lower().endswith(".exe"):
        raise NvidiaDriverError(f"URL de download inesperada (não é .exe): {url}")


def lookup_latest(psid, pfid):
    """Returns (version, download url) of the newest Game Ready WHQL driver for the product."""
    data = json.loads(_fetch(_DRIVER_URL.format(psid=psid, pfid=pfid)))
    try:
        info = data["IDS"][0]["downloadInfo"]
        version, url = info["Version"], info["DownloadURL"]
    except (KeyError, IndexError, TypeError):
        raise NvidiaDriverError("a NVIDIA não retornou driver para esta GPU")
    validate_download_url(url)
    return str(version), url


def check_update():
    """Returns an NvidiaUpdate if an NVIDIA GPU has a newer driver available, else None.

    No NVIDIA GPU (or GPU detection failing) is not an error: returns None. Raises
    NvidiaDriverError when the GPU exists but NVIDIA's service can't be queried.
    """
    try:
        gpus = get_nvidia_gpus()
    except (PowerShellError, ValueError) as exc:
        log.warning("nvidia: não foi possível listar as GPUs: %s", exc)
        return None
    if not gpus:
        return None

    gpu = gpus[0]
    installed = windows_to_nvidia_version(gpu["driver_version"])
    if installed is None:
        raise NvidiaDriverError(f"versão do driver instalado desconhecida ({gpu['driver_version']})")
    try:
        psid, pfid = find_product(gpu["name"])
        latest, url = lookup_latest(psid, pfid)
    except NvidiaDriverError:
        raise
    except (OSError, ValueError, ET.ParseError) as exc:
        log.error("nvidia: consulta falhou: %s", exc)
        raise NvidiaDriverError(f"não foi possível consultar a NVIDIA: {exc}")
    log.info("nvidia: %s instalado=%s mais novo=%s", gpu["name"], installed, latest)
    if not is_newer(latest, installed):
        return None
    return NvidiaUpdate(gpu["name"], installed, latest, url)


# --- install -------------------------------------------------------------------------------

def _download(url, dest):
    request = urllib.request.Request(url, headers={"User-Agent": "SystemBoost"})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out, 1024 * 1024)


def _verify_signature(path):
    """Raises NvidiaDriverError unless the file has a valid Authenticode signature by NVIDIA."""
    script = _SIGNATURE_SCRIPT.format(path=str(path).replace("'", "''"))
    try:
        result = json.loads(run_powershell(script, POWERSHELL_TIMEOUT) or "{}")
    except (PowerShellError, ValueError) as exc:
        raise NvidiaDriverError(f"não foi possível verificar a assinatura: {exc}")
    if result.get("status") != "Valid" or "NVIDIA Corporation" not in (result.get("subject") or ""):
        raise NvidiaDriverError("assinatura inválida no instalador da NVIDIA")


def install_update(update, workdir=None):
    """Downloads, verifies and silently installs the driver. Returns (ok, reboot_required, note)."""
    validate_download_url(update.url)
    own_dir = workdir is None
    folder = Path(tempfile.mkdtemp(prefix="systemboost-nvidia-")) if own_dir else Path(workdir)
    installer = folder / f"nvidia-{update.latest}.exe"
    try:
        log.info("nvidia: baixando %s", update.url)
        try:
            _download(update.url, installer)
        except OSError as exc:
            raise NvidiaDriverError(f"falha ao baixar o driver: {exc}")
        _verify_signature(installer)
        log.info("nvidia: instalando %s", update.latest)
        try:
            result = subprocess.run(
                [str(installer), "-s", "-noreboot", "-noeula"],
                capture_output=True, check=False, timeout=INSTALL_TIMEOUT, stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            raise NvidiaDriverError("tempo esgotado instalando o driver NVIDIA")
        except OSError as exc:
            raise NvidiaDriverError(f"não foi possível executar o instalador: {exc}")
        log.info("nvidia: instalador retornou %s", result.returncode)
        if result.returncode == 0:
            return True, False, "instalado"
        return False, False, f"falha na instalação (código {result.returncode})"
    finally:
        try:
            installer.unlink()
        except OSError:
            pass
        if own_dir:
            shutil.rmtree(folder, ignore_errors=True)
