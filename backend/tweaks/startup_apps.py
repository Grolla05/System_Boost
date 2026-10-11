"""Reversible tweak: disables third-party programs that start with Windows.

Uses the same StartupApproved mechanism as Task Manager's "Startup" tab, so the Run entries
and Startup-folder shortcuts are never deleted — they are only flagged disabled, and undo
restores the exact bytes that were there before.
"""
import os

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from backend.logger import get_logger
from backend.privileges import is_admin

from . import third_party
from .base import Tweak

log = get_logger("tweaks.startup_apps")

_CURRENT_VERSION = "Software\\Microsoft\\Windows\\CurrentVersion"
_APPROVED = _CURRENT_VERSION + "\\Explorer\\StartupApproved\\"

# Disabled marker used by Explorer: first byte 03 (odd = disabled), then a FILETIME (zeroed here).
_DISABLED = bytes([3, 0, 0, 0]) + bytes(8)

# scope -> (hive name, approved subkey, requires admin)
_APPROVED_TARGETS = {
    "hkcu_run": ("HKEY_CURRENT_USER", _APPROVED + "Run", False),
    "hklm_run": ("HKEY_LOCAL_MACHINE", _APPROVED + "Run", True),
    "hklm_run32": ("HKEY_LOCAL_MACHINE", _APPROVED + "Run32", True),
    "user_folder": ("HKEY_CURRENT_USER", _APPROVED + "StartupFolder", False),
    "common_folder": ("HKEY_LOCAL_MACHINE", _APPROVED + "StartupFolder", True),
}

# scope -> (hive name, Run key)
_RUN_KEYS = {
    "hkcu_run": ("HKEY_CURRENT_USER", _CURRENT_VERSION + "\\Run"),
    "hklm_run": ("HKEY_LOCAL_MACHINE", _CURRENT_VERSION + "\\Run"),
    "hklm_run32": ("HKEY_LOCAL_MACHINE", "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run"),
}


def _startup_folders():
    """Returns {scope: folder path} for the per-user and all-users Startup folders."""
    folders = {}
    appdata = os.environ.get("APPDATA")
    if appdata:
        folders["user_folder"] = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    programdata = os.environ.get("PROGRAMDATA")
    if programdata:
        folders["common_folder"] = os.path.join(programdata, "Microsoft", "Windows", "Start Menu", "Programs", "StartUp")
    return folders


def _hive(name):
    return getattr(winreg, name)


def _read_approved(scope, name):
    """Returns the StartupApproved bytes for the item, or None if there is no record."""
    hive_name, subkey, _ = _APPROVED_TARGETS[scope]
    try:
        key = winreg.OpenKey(_hive(hive_name), subkey)
    except OSError:
        return None
    try:
        data, _ = winreg.QueryValueEx(key, name)
        return bytes(data)
    except OSError:
        return None
    finally:
        winreg.CloseKey(key)


def write_approved(scope, name, data):
    """Writes the StartupApproved bytes for the item; data=None removes the record."""
    hive_name, subkey, _ = _APPROVED_TARGETS[scope]
    key = winreg.CreateKeyEx(_hive(hive_name), subkey, 0, winreg.KEY_SET_VALUE)
    try:
        if data is None:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass
        else:
            winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, data)
    finally:
        winreg.CloseKey(key)


def _entry(scope, name, command):
    previous = _read_approved(scope, name)
    enabled = previous is None or (len(previous) > 0 and previous[0] % 2 == 0)
    return {
        "scope": scope, "name": name, "command": command,
        "enabled": enabled, "previous": previous.hex() if previous is not None else None,
    }


def _read_run_entries(scope):
    """Enumerates the name/command pairs under one Run key."""
    hive_name, run_key = _RUN_KEYS[scope]
    entries = []
    try:
        key = winreg.OpenKey(_hive(hive_name), run_key)
    except OSError:
        return entries
    try:
        index = 0
        while True:
            try:
                name, command, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1
            entries.append(_entry(scope, name, str(command)))
    finally:
        winreg.CloseKey(key)
    return entries


def discover_entries():
    """Lists every startup entry (Run keys + Startup folders) the current privileges can change."""
    admin = is_admin()
    entries = []
    for scope in _RUN_KEYS:
        if _APPROVED_TARGETS[scope][2] and not admin:
            continue
        entries.extend(_read_run_entries(scope))
    for scope, folder in _startup_folders().items():
        if _APPROVED_TARGETS[scope][2] and not admin:
            continue
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            if name.lower() == "desktop.ini":
                continue
            # The shortcut's target isn't resolved (needs COM); classify by file name only.
            entries.append(_entry(scope, name, "startup-folder\\" + name))
    return entries


class StartupAppsTweak(Tweak):
    """Disables third-party programs that launch at logon, without deleting their entries."""

    id = "startup_apps"
    label = "Apps de terceiros na inicialização: desativar"
    description = "Impede que programas de terceiros abram junto com o Windows (itens do sistema são preservados)."
    requires_admin = False

    def _candidates(self):
        """Enabled third-party entries."""
        return [
            e for e in discover_entries()
            if e["enabled"] and third_party.is_third_party(e["name"], e["command"])
        ]

    def get_current_value(self):
        """Returns the JSON-safe list of entries that apply() would disable, with their prior bytes."""
        return [
            {"scope": e["scope"], "name": e["name"], "previous": e["previous"]}
            for e in self._candidates()
        ]

    def apply(self):
        """Flags each candidate disabled; returns the entries actually changed."""
        changed = []
        for entry in self._candidates():
            try:
                write_approved(entry["scope"], entry["name"], _DISABLED)
            except OSError as exc:
                log.warning("startup '%s' (%s): não foi possível desativar: %s", entry["name"], entry["scope"], exc)
                continue
            log.info("startup '%s' (%s): desativado", entry["name"], entry["scope"])
            changed.append({"scope": entry["scope"], "name": entry["name"]})
        return changed

    def undo(self, previous_value):
        """Restores each entry's original StartupApproved bytes (or removes the record)."""
        for item in previous_value or []:
            data = bytes.fromhex(item["previous"]) if item.get("previous") else None
            try:
                write_approved(item["scope"], item["name"], data)
            except OSError as exc:
                log.warning("startup '%s' (%s): não foi possível restaurar: %s", item["name"], item["scope"], exc)
        return previous_value
