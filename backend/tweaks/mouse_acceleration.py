"""Reversible tweak: turns off "Enhance pointer precision" (mouse acceleration)."""
import ctypes

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from backend.logger import get_logger

from .base import Tweak, TweakError

log = get_logger("tweaks.mouse_acceleration")

_MOUSE_KEY = "Control Panel\\Mouse"
# Acceleration off = all three at "0". The defaults ("6"/"10"/"1") are what Windows ships with.
_OFF = "0"
_NAMES = ("MouseSpeed", "MouseThreshold1", "MouseThreshold2")

_SPI_SETMOUSE = 0x0004
_SPIF_UPDATEINIFILE_SENDCHANGE = 0x0003


def _read(name):
    """Returns the REG_SZ value as a string, or None if the key or value doesn't exist."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _MOUSE_KEY)
    except OSError:
        return None
    try:
        return str(winreg.QueryValueEx(key, name)[0])
    except OSError:
        return None
    finally:
        winreg.CloseKey(key)


def _write(key, name, value):
    """Writes a REG_SZ, or deletes the value when value is None."""
    if value is None:
        try:
            winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass
    else:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def _to_int(value):
    """Converts a stored string to int, 0 when absent or malformed."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _notify(threshold1, threshold2, speed):
    """Tells the running session to pick up the new acceleration now (no re-login needed)."""
    try:
        params = (ctypes.c_int * 3)(threshold1, threshold2, speed)
        ok = ctypes.windll.user32.SystemParametersInfoW(
            _SPI_SETMOUSE, 0, params, _SPIF_UPDATEINIFILE_SENDCHANGE
        )
        if not ok:
            log.warning("SPI_SETMOUSE retornou falha; vale a partir do próximo login")
    except Exception as exc:  # registry is already written; this only makes it immediate
        log.warning("não foi possível aplicar a precisão do ponteiro na sessão atual: %s", exc)


def _write_all(values):
    """Writes {name: value|None} under HKCU\\Control Panel\\Mouse, raising TweakError on failure."""
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _MOUSE_KEY, 0, winreg.KEY_SET_VALUE)
    except OSError as exc:
        raise TweakError(f"Não foi possível abrir a chave '{_MOUSE_KEY}': {exc}") from exc
    try:
        for name, value in values.items():
            _write(key, name, value)
    except OSError as exc:
        raise TweakError(f"Não foi possível gravar a precisão do ponteiro: {exc}") from exc
    finally:
        winreg.CloseKey(key)


class MouseAccelerationTweak(Tweak):
    """Disables pointer acceleration; the pointer speed slider is left untouched."""

    id = "mouse_acceleration"
    label = "Desativar precisão do ponteiro (aceleração do mouse)"
    description = "Desmarca 'Enhance pointer precision' (Configurações > Mouse), deixando o ponteiro com resposta linear."
    requires_admin = False

    def get_current_value(self):
        """Returns {value name: string or None (absent)} for the three acceleration values."""
        return {name: _read(name) for name in _NAMES}

    def apply(self):
        """Turns acceleration off; returns [{'name': ...}] if it was on, [] if already off."""
        before = self.get_current_value()
        _write_all({name: _OFF for name in _NAMES})
        _notify(0, 0, 0)
        if before["MouseSpeed"] == _OFF:
            return []
        log.info("precisão do ponteiro: desligada")
        return [{"name": "Enhance pointer precision"}]

    def undo(self, previous_value):
        """Restores each value (deleting the ones that didn't exist) and re-notifies the session."""
        previous = previous_value or {}
        _write_all({name: previous.get(name) for name in _NAMES})
        _notify(
            _to_int(previous.get("MouseThreshold1")),
            _to_int(previous.get("MouseThreshold2")),
            _to_int(previous.get("MouseSpeed")),
        )
        return previous_value
