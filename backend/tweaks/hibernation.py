"""Reversible tweak for Windows hibernation."""
import subprocess
try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from .base import Tweak, TweakError

_POWER_KEY = "SYSTEM\\CurrentControlSet\\Control\\Power"


class HibernationTweak(Tweak):
    """Disables Windows hibernation via powercfg."""

    id = "hibernation"
    label = "Desativar hibernação"
    description = "Desativa a hibernação do Windows (remove hiberfil.sys)."
    requires_admin = True

    def get_current_value(self):
        """Reads HibernateEnabled from the registry; absent means Windows' default (enabled)."""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _POWER_KEY)
        except (FileNotFoundError, OSError):
            return 1
        try:
            value, _ = winreg.QueryValueEx(key, "HibernateEnabled")
            return value
        except (FileNotFoundError, OSError):
            return 1
        finally:
            winreg.CloseKey(key)

    def apply(self):
        """Turns hibernation off."""
        self._set_hibernation(0)
        return 0

    def undo(self, previous_value):
        """Restores hibernation to its previous on/off state."""
        self._set_hibernation(previous_value)
        return previous_value

    def _set_hibernation(self, value):
        """Runs powercfg /hibernate on|off."""
        flag = "on" if value else "off"
        result = subprocess.run(["powercfg", "/hibernate", flag], capture_output=True, check=False)
        if result.returncode != 0:
            raise TweakError(f"Falha ao {'ativar' if value else 'desativar'} hibernação.")
