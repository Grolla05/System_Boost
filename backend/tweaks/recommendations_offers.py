"""Reversible tweak: turns off every switch in Settings > Privacy & security > Recommendations & offers."""
try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from backend.logger import get_logger

from .base import Tweak

log = get_logger("tweaks.recommendations_offers")

_CURRENT_VERSION = "Software\\Microsoft\\Windows\\CurrentVersion"
_CDM = _CURRENT_VERSION + "\\ContentDeliveryManager"

# (switch name shown in Settings, [(HKCU subkey, DWORD name, value that turns it off)]).
# Windows moves these around between builds, so a switch may list several candidate values;
# writing the extra ones is harmless.
SWITCHES = (
    ("Personalized offers", [
        (_CURRENT_VERSION + "\\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 0),
    ]),
    ("Allow websites to access my language list", [
        ("Control Panel\\International\\User Profile", "HttpAcceptLanguageOptOut", 1),
    ]),
    ("Improve Start and search results", [
        (_CURRENT_VERSION + "\\Explorer\\Advanced", "Start_TrackProgs", 0),
    ]),
    ("Show notifications in Settings", [
        (_CURRENT_VERSION + "\\SystemSettings\\AccountNotifications", "EnableAccountNotifications", 0),
        (_CDM, "SubscribedContent-338389Enabled", 0),
    ]),
    ("Recommendations and offers in Settings", [
        (_CDM, "SubscribedContent-338393Enabled", 0),
        (_CDM, "SubscribedContent-353694Enabled", 0),
        (_CDM, "SubscribedContent-353696Enabled", 0),
    ]),
    ("Advertising ID", [
        (_CURRENT_VERSION + "\\AdvertisingInfo", "Enabled", 0),
    ]),
)


def _read(path, name):
    """Returns the DWORD's current value, or None if the key or value doesn't exist."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
    except OSError:
        return None
    try:
        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None
    finally:
        winreg.CloseKey(key)


def _write(path, name, value):
    """Writes a DWORD, or deletes the value when value is None. Raises OSError on failure."""
    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
    try:
        if value is None:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass
        else:
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
    finally:
        winreg.CloseKey(key)


class RecommendationsOffersTweak(Tweak):
    """Turns off Windows' personalized offers, tracking-based suggestions and ads in the user's settings."""

    id = "recommendations_offers"
    label = "Recomendações e ofertas do Windows: desligar"
    description = "Desliga todos os switches de Configurações > Privacidade e segurança > Recomendações e ofertas."
    requires_admin = False

    def get_current_value(self):
        """Returns the JSON-safe list of every value this tweak writes, with its current value (None = absent)."""
        return [
            {"path": path, "name": name, "previous": _read(path, name)}
            for _, targets in SWITCHES
            for path, name, _ in targets
        ]

    def apply(self):
        """Turns each switch off; returns [{'name': switch}] for the switches that actually changed."""
        changed = []
        for switch, targets in SWITCHES:
            switch_changed = False
            for path, name, target in targets:
                before = _read(path, name)
                try:
                    _write(path, name, target)
                except OSError as exc:
                    log.warning("'%s' (%s): não foi possível escrever: %s", switch, name, exc)
                    continue
                switch_changed = switch_changed or before != target
            if switch_changed:
                log.info("'%s': desligado", switch)
                changed.append({"name": switch})
        return changed

    def undo(self, previous_value):
        """Restores each value (deleting the ones that didn't exist before)."""
        for item in previous_value or []:
            try:
                _write(item["path"], item["name"], item["previous"])
            except OSError as exc:
                log.warning("'%s': não foi possível restaurar: %s", item["name"], exc)
        return previous_value
