"""JSON-backed persistence for applied tweak state, used for apply/undo."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_VERSION = 1


def _default_state_path():
    """Returns the default state file path under %LOCALAPPDATA%\\WinCleaner."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "WinCleaner" / "tweaks_state.json"


def _empty_state():
    """Returns a fresh, empty state structure."""
    return {"_schema_version": _SCHEMA_VERSION, "_next_seq": 0, "tweaks": {}}


def load_state(path=None):
    """Loads the full state dict from disk, returning an empty structure if missing/corrupt."""
    path = Path(path) if path else _default_state_path()
    if not path.exists():
        return _empty_state()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _empty_state()
    data.setdefault("_schema_version", _SCHEMA_VERSION)
    data.setdefault("_next_seq", 0)
    data.setdefault("tweaks", {})
    return data


def _save_state(state, path=None):
    """Atomically writes the full state dict to disk (temp file + os.replace)."""
    path = Path(path) if path else _default_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tweaks_state_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def save_applied(tweak_id, previous_value, applied_value, requires_admin, path=None):
    """Saves (or overwrites) the applied-state record for tweak_id."""
    state = load_state(path)
    state["_next_seq"] += 1
    state["tweaks"][tweak_id] = {
        "tweak_id": tweak_id,
        "applied_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "previous_value": previous_value,
        "applied_value": applied_value,
        "requires_admin": requires_admin,
        "_seq": state["_next_seq"],
    }
    _save_state(state, path)


def get_applied(tweak_id, path=None):
    """Returns the applied-state record for tweak_id, or None if not applied."""
    state = load_state(path)
    return state["tweaks"].get(tweak_id)


def clear_applied(tweak_id, path=None):
    """Removes the applied-state record for tweak_id, if present."""
    state = load_state(path)
    if tweak_id in state["tweaks"]:
        del state["tweaks"][tweak_id]
        _save_state(state, path)


def list_applied(path=None):
    """Returns all applied-state records, most recently applied first."""
    state = load_state(path)
    records = list(state["tweaks"].values())
    records.sort(key=lambda r: r.get("_seq", 0), reverse=True)
    return records
