"""Reversible tweak mechanism for a single DWORD registry value."""
try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from backend.logger import get_logger

from .base import Tweak, TweakError

log = get_logger("tweaks.registry")


class RegistryValueTweak(Tweak):
    """Reads/writes one DWORD registry value, restoring or deleting it on undo."""

    def __init__(self, tweak_id, label, description, hive, key_path, value_name, target_value, requires_admin=False):
        """Stores the registry location and target value for this tweak instance."""
        self.id = tweak_id
        self.label = label
        self.description = description
        self.hive = hive
        self.key_path = key_path
        self.value_name = value_name
        self.target_value = target_value
        self.requires_admin = requires_admin

    def get_current_value(self):
        """Returns the current DWORD value, or None if the key or value doesn't exist."""
        try:
            key = winreg.OpenKey(self.hive, self.key_path)
        except (FileNotFoundError, OSError) as exc:
            log.debug("registro: chave '%s' ausente/ilegível: %s", self.key_path, exc)
            return None
        try:
            value, _ = winreg.QueryValueEx(key, self.value_name)
            log.debug("registro: leu '%s' [%s] = %r", self.key_path, self.value_name, value)
            return value
        except (FileNotFoundError, OSError):
            log.debug("registro: valor '%s' ausente em '%s'", self.value_name, self.key_path)
            return None
        finally:
            winreg.CloseKey(key)

    def apply(self):
        """Writes target_value to the registry, creating the key if it doesn't exist."""
        try:
            key = winreg.CreateKeyEx(self.hive, self.key_path)
        except OSError as exc:
            log.error("registro: falha ao abrir/criar '%s': %s", self.key_path, exc)
            raise TweakError(f"Não foi possível abrir/criar a chave '{self.key_path}': {exc}") from exc
        try:
            winreg.SetValueEx(key, self.value_name, 0, winreg.REG_DWORD, self.target_value)
        except OSError as exc:
            log.error("registro: falha ao escrever '%s': %s", self.value_name, exc)
            raise TweakError(f"Não foi possível escrever '{self.value_name}': {exc}") from exc
        finally:
            winreg.CloseKey(key)
        log.debug("registro: escreveu '%s' [%s] = %r", self.key_path, self.value_name, self.target_value)
        return self.target_value

    def undo(self, previous_value):
        """Restores previous_value, deleting the value entirely if it was None."""
        try:
            key = winreg.CreateKeyEx(self.hive, self.key_path)
        except OSError as exc:
            raise TweakError(f"Não foi possível abrir a chave '{self.key_path}': {exc}") from exc
        try:
            if previous_value is None:
                try:
                    winreg.DeleteValue(key, self.value_name)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(key, self.value_name, 0, winreg.REG_DWORD, previous_value)
        except OSError as exc:
            raise TweakError(f"Não foi possível restaurar '{self.value_name}': {exc}") from exc
        finally:
            winreg.CloseKey(key)
        return previous_value
