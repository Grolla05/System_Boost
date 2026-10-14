"""Reversible tweak: moves third-party auto-start services to manual start and stops them.

Manual ('demand') rather than disabled, so the owning application can still start its
service on demand. Windows/Microsoft services, drivers and the exceptions list are skipped.
"""
import subprocess

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from backend.logger import get_logger

from . import third_party
from .base import Tweak

log = get_logger("tweaks.third_party_services")

_SERVICES_KEY = "SYSTEM\\CurrentControlSet\\Services"
_OWN_PROCESS, _SHARE_PROCESS = 0x10, 0x20
_AUTO_START = 2


def _query(key, name, default=None):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return default


def discover_services():
    """Lists Win32 services set to start automatically, with their command line and start type."""
    services = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _SERVICES_KEY)
    except OSError:
        return services
    try:
        index = 0
        while True:
            try:
                name = winreg.EnumKey(root, index)
            except OSError:
                break
            index += 1
            if "_" in name:  # per-user service instances (Name_1a2b3c)
                continue
            try:
                key = winreg.OpenKey(root, name)
            except OSError:
                continue
            try:
                svc_type = _query(key, "Type", 0)
                if svc_type not in (_OWN_PROCESS, _SHARE_PROCESS) or _query(key, "Start") != _AUTO_START:
                    continue
                command = _query(key, "ImagePath", "")
                if not isinstance(command, str):
                    continue
                delayed = _query(key, "DelayedAutostart", 0) == 1
                services.append({
                    "name": name,
                    "display": str(_query(key, "DisplayName", "")),
                    "command": command,
                    "start_type": "delayed-auto" if delayed else "auto",
                })
            finally:
                winreg.CloseKey(key)
    finally:
        winreg.CloseKey(root)
    return services


def set_start_type(name, start_type):
    """Runs sc config to set the service's start type; raises OSError on failure."""
    result = subprocess.run(["sc", "config", name, "start=", start_type], capture_output=True, check=False)
    log.debug("sc config %s start=%s: returncode=%s", name, start_type, result.returncode)
    if result.returncode != 0:
        raise OSError(f"sc config {name} start={start_type} retornou {result.returncode}")


def stop_service(name):
    """Stops the service (best effort: a service that won't stop is not an error)."""
    result = subprocess.run(["sc", "stop", name], capture_output=True, check=False)
    log.debug("sc stop %s: returncode=%s", name, result.returncode)


def start_service(name):
    """Starts the service (best effort)."""
    result = subprocess.run(["sc", "start", name], capture_output=True, check=False)
    log.debug("sc start %s: returncode=%s", name, result.returncode)


class ThirdPartyServicesTweak(Tweak):
    """Sets third-party auto-start services to manual and stops them."""

    id = "third_party_services"
    label = "Serviços de terceiros: iniciar só sob demanda"
    description = "Move serviços de terceiros de início automático para manual (serviços do Windows são preservados)."
    requires_admin = True

    def _candidates(self):
        return [
            s for s in discover_services()
            if third_party.is_third_party(s["name"], s["command"], s.get("display"))
        ]

    def get_current_value(self):
        """Returns the JSON-safe list of services apply() would change, with their original start type."""
        return [{"name": s["name"], "start_type": s["start_type"]} for s in self._candidates()]

    def apply(self):
        """Sets each candidate to manual start and stops it; returns the services changed."""
        changed = []
        for service in self._candidates():
            name = service["name"]
            try:
                set_start_type(name, "demand")
            except OSError as exc:
                log.warning("serviço '%s': não foi possível configurar: %s", name, exc)
                continue
            stop_service(name)
            log.info("serviço '%s': agora manual e parado", name)
            changed.append({"name": name})
        return changed

    def undo(self, previous_value):
        """Restores each service's original start type and starts it again."""
        for service in previous_value or []:
            name = service["name"]
            try:
                set_start_type(name, service["start_type"])
            except OSError as exc:
                log.warning("serviço '%s': não foi possível restaurar: %s", name, exc)
                continue
            start_service(name)
        return previous_value
