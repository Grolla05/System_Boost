import ctypes
import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import winreg
except ImportError:  # non-Windows (e.g. docs/tooling); every reader degrades to None
    winreg = None

from backend._powershell import PS_PRELUDE, PowerShellError, run_powershell
from backend.logger import get_logger

log = get_logger("hardware")

CIM_TIMEOUT = 30

_NT_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
_CPU_KEY = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"

# First Windows 11 build. ProductName in the registry still says "Windows 10" there.
_WIN11_MIN_BUILD = 22000

# Win32_SystemEnclosure.ChassisTypes: 8 Portable, 9 Laptop, 10 Notebook, 11 Handheld,
# 14 Sub Notebook, 30 Tablet, 31 Convertible, 32 Detachable. 1/2 are "Other"/"Unknown".
_PORTABLE_CHASSIS = frozenset({8, 9, 10, 11, 14, 30, 31, 32})
_UNINFORMATIVE_CHASSIS = frozenset({1, 2})

# One PowerShell round-trip for everything that has no cheap registry/ctypes source.
# Each block is isolated so one failing query doesn't take the others down. Enum-ish
# values (MediaType, BusType) are cast to string: the names aren't localized.
_CIM_SCRIPT = PS_PRELUDE + (
    "$o=@{gpus=@();disk=$null;chassis=@();battery=$false};"
    "try{$o.gpus=@(Get-CimInstance Win32_VideoController|ForEach-Object{$_.Name})}catch{};"
    "try{$n=(Get-Partition -DriveLetter ($env:SystemDrive.Substring(0,1))).DiskNumber;"
    "$d=Get-PhysicalDisk|Where-Object{$_.DeviceId -eq \"$n\"}|Select-Object -First 1;"
    "if($d){$o.disk=@{model=$d.FriendlyName;media=[string]$d.MediaType;"
    "bus=[string]$d.BusType;size=[int64]$d.Size}}}catch{};"
    "try{$o.chassis=@((Get-CimInstance Win32_SystemEnclosure).ChassisTypes)}catch{};"
    "try{$o.battery=[bool](Get-CimInstance Win32_Battery)}catch{};"
    "ConvertTo-Json -InputObject $o -Compress -Depth 4"
)


@dataclass
class MachineInfo:
    windows: Optional[str] = None
    version: Optional[str] = None
    build: Optional[str] = None
    cpu: Optional[str] = None
    threads: Optional[int] = None
    ram_gb: Optional[float] = None
    gpus: List[str] = field(default_factory=list)
    disk_type: Optional[str] = None
    disk_model: Optional[str] = None
    disk_bus: Optional[str] = None
    form_factor: Optional[str] = None


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _reg_value(path, name):
    """Reads one HKLM value; returns None if the key/value is missing or unreadable."""
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def _read_windows():
    """Returns (name, version, build) from the registry; each is None if unavailable."""
    name = _reg_value(_NT_KEY, "ProductName")
    version = _reg_value(_NT_KEY, "DisplayVersion") or _reg_value(_NT_KEY, "ReleaseId")
    build_number = _reg_value(_NT_KEY, "CurrentBuildNumber")
    ubr = _reg_value(_NT_KEY, "UBR")

    build = None
    if build_number:
        build = f"{build_number}.{ubr}" if ubr is not None else str(build_number)
        try:
            if name and int(build_number) >= _WIN11_MIN_BUILD:
                name = name.replace("Windows 10", "Windows 11")
        except ValueError:
            pass
    return (str(name) if name else None, str(version) if version else None, build)


def _read_cpu():
    name = _reg_value(_CPU_KEY, "ProcessorNameString")
    return " ".join(str(name).split()) if name else None


def _installed_ram_kb():
    """Physically installed RAM in KB (what the sticks add up to, not what Windows can use)."""
    kb = ctypes.c_ulonglong(0)
    if not ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(kb)):
        raise OSError("GetPhysicallyInstalledSystemMemory falhou")
    return kb.value


def _total_ram_bytes():
    status = _MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx falhou")
    return status.ullTotalPhys


def _read_ram_gb():
    try:
        return round(_installed_ram_kb() / 1024 / 1024, 1)
    except Exception as exc:
        log.debug("ram: instalada indisponível (%s), usando total utilizável", exc)
    try:
        return round(_total_ram_bytes() / 1024 ** 3, 1)
    except Exception as exc:
        log.warning("ram: indisponível: %s", exc)
        return None


def _as_list(value):
    """PowerShell collapses 1-item arrays to scalars and empty ones to null."""
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _read_cim():
    """Returns the parsed CIM payload dict, or {} when PowerShell/JSON fails."""
    try:
        text = run_powershell(_CIM_SCRIPT, CIM_TIMEOUT)
    except (PowerShellError, OSError) as exc:
        log.warning("cim: PowerShell indisponível: %s", exc)
        return {}
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        log.warning("cim: resposta inválida: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def _classify_disk(media, bus):
    media = (media or "").strip().upper()
    bus = (bus or "").strip().upper()
    if media in ("SSD", "4"):
        return "SSD"
    if media in ("HDD", "3"):
        return "HDD"
    if bus == "NVME":  # NVMe is flash even when MediaType comes back Unspecified
        return "SSD"
    return None


def _classify_chassis(chassis, battery):
    types = set()
    for item in _as_list(chassis):
        try:
            types.add(int(item))
        except (TypeError, ValueError):
            continue
    if types & _PORTABLE_CHASSIS:
        return "Notebook"
    if types - _UNINFORMATIVE_CHASSIS:
        return "Desktop"
    if not types:
        return "Notebook" if battery else None
    return "Notebook" if battery else "Desktop"


def get_machine_info():
    """Collects the machine's hardware/OS summary. Never raises; unknown fields stay None/[]."""
    info = MachineInfo()
    info.windows, info.version, info.build = _read_windows()
    info.cpu = _read_cpu()
    info.threads = os.cpu_count() or None
    info.ram_gb = _read_ram_gb()

    cim = _read_cim()

    seen = []
    for gpu in _as_list(cim.get("gpus")):
        gpu = str(gpu).strip()
        if gpu and gpu not in seen:
            seen.append(gpu)
    info.gpus = seen

    disk = cim.get("disk")
    if isinstance(disk, dict):
        info.disk_type = _classify_disk(disk.get("media"), disk.get("bus"))
        info.disk_model = disk.get("model") or None
        info.disk_bus = disk.get("bus") or None

    info.form_factor = _classify_chassis(cim.get("chassis"), bool(cim.get("battery")))
    log.info("ficha da máquina: %s", info)
    return info
