"""Reversible tweak for the active Windows power plan."""
import subprocess
try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from backend.logger import get_logger

from .base import Tweak, TweakError

log = get_logger("tweaks.power_plan")

_HIGH_PERFORMANCE_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
_POWER_SCHEMES_KEY = "SYSTEM\\CurrentControlSet\\Control\\Power\\User\\PowerSchemes"


class PowerPlanTweak(Tweak):
    """Switches the active Windows power plan to High Performance."""

    id = "power_plan"
    label = "Plano de energia: Alto desempenho"
    description = "Ativa o plano de energia Alto Desempenho."
    requires_admin = False

    def __init__(self, target_guid=_HIGH_PERFORMANCE_GUID):
        """Stores the target power scheme GUID to switch to on apply()."""
        self.target_guid = target_guid

    def get_current_value(self):
        """Reads the active power scheme GUID from the registry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _POWER_SCHEMES_KEY)
        except (FileNotFoundError, OSError) as exc:
            raise TweakError(f"Não foi possível ler o plano de energia ativo: {exc}") from exc
        try:
            value, _ = winreg.QueryValueEx(key, "ActivePowerScheme")
        except (FileNotFoundError, OSError) as exc:
            raise TweakError(f"Não foi possível ler o plano de energia ativo: {exc}") from exc
        finally:
            winreg.CloseKey(key)
        return value

    def apply(self):
        """Activates the target power scheme via powercfg."""
        self._set_active(self.target_guid)
        return self.target_guid

    def undo(self, previous_value):
        """Restores the previously active power scheme."""
        self._set_active(previous_value)
        return previous_value

    def _set_active(self, guid):
        """Runs powercfg /setactive for the given scheme GUID."""
        result = subprocess.run(["powercfg", "/setactive", guid], capture_output=True, check=False)
        log.debug("powercfg /setactive %s: returncode=%s", guid, result.returncode)
        if result.returncode != 0:
            log.error("powercfg /setactive: stdout=%r stderr=%r", result.stdout, result.stderr)
            raise TweakError(f"Falha ao ativar plano de energia '{guid}'.")
