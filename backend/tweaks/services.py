"""Reversible tweak mechanism for a Windows service's start type."""
import subprocess
try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from .base import Tweak, TweakError

_INT_TO_START_TYPE = {0: "boot", 1: "system", 2: "auto", 3: "demand", 4: "disabled"}
_STARTABLE_TYPES = ("boot", "system", "auto")


class ServiceStateTweak(Tweak):
    """Disables a Windows service by setting its start type via sc.exe."""

    def __init__(self, tweak_id, label, description, service_name, target_start_type="disabled", requires_admin=True):
        """Stores the service name and desired start type for this tweak instance."""
        self.id = tweak_id
        self.label = label
        self.description = description
        self.service_name = service_name
        self.target_start_type = target_start_type
        self.requires_admin = requires_admin

    def get_current_value(self):
        """Reads the service's Start DWORD from the registry (locale-independent)."""
        key_path = f"SYSTEM\\CurrentControlSet\\Services\\{self.service_name}"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        except (FileNotFoundError, OSError) as exc:
            raise TweakError(f"Serviço '{self.service_name}' não encontrado: {exc}") from exc
        try:
            value, _ = winreg.QueryValueEx(key, "Start")
        except (FileNotFoundError, OSError) as exc:
            raise TweakError(f"Não foi possível ler o serviço '{self.service_name}': {exc}") from exc
        finally:
            winreg.CloseKey(key)
        return _INT_TO_START_TYPE.get(value, str(value))

    def apply(self):
        """Sets the service's start type to target_start_type and stops it."""
        self._set_start_type(self.target_start_type)
        subprocess.run(["sc", "stop", self.service_name], capture_output=True, check=False)
        return self.target_start_type

    def undo(self, previous_value):
        """Restores the service's previous start type, restarting it if it used to auto-start."""
        self._set_start_type(previous_value)
        if previous_value in _STARTABLE_TYPES:
            subprocess.run(["sc", "start", self.service_name], capture_output=True, check=False)
        return previous_value

    def _set_start_type(self, start_type):
        """Runs sc config to set the service's start type, raising TweakError on failure."""
        result = subprocess.run(
            ["sc", "config", self.service_name, "start=", start_type],
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise TweakError(f"Falha ao configurar serviço '{self.service_name}' (start={start_type}).")
