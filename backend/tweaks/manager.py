"""Applies and undoes reversible tweaks, coordinating catalog, state, and admin checks."""
from backend.privileges import is_admin

from . import catalog
from . import state_store
from .base import TweakError


def _require_admin_if_needed(tweak):
    """Raises TweakError if tweak needs admin rights and the process isn't elevated."""
    if tweak.requires_admin and not is_admin():
        raise TweakError(
            f"'{tweak.label}' requer privilégios de administrador. "
            "Reabra o terminal como Administrador e tente novamente."
        )


def apply_tweak(tweak_id, state_path=None):
    """Applies tweak_id after checking admin and saving its current value for undo."""
    tweak = catalog.get_tweak(tweak_id)
    _require_admin_if_needed(tweak)
    if state_store.get_applied(tweak_id, path=state_path) is not None:
        raise TweakError(f"'{tweak_id}' já está aplicado. Rode `boost undo {tweak_id}` primeiro.")
    previous_value = tweak.get_current_value()
    applied_value = tweak.apply()
    state_store.save_applied(tweak_id, previous_value, applied_value, tweak.requires_admin, path=state_path)
    return applied_value


def undo_tweak(tweak_id, state_path=None):
    """Undoes a previously applied tweak, restoring its saved previous value."""
    tweak = catalog.get_tweak(tweak_id)
    _require_admin_if_needed(tweak)
    record = state_store.get_applied(tweak_id, path=state_path)
    if record is None:
        raise TweakError(f"'{tweak_id}' não está aplicado — nada para desfazer.")
    tweak.undo(record["previous_value"])
    state_store.clear_applied(tweak_id, path=state_path)
    return record["previous_value"]


def undo_all(state_path=None):
    """Undoes every applied tweak, most recently applied first, collecting per-tweak results."""
    results = []
    for record in state_store.list_applied(path=state_path):
        tweak_id = record["tweak_id"]
        try:
            undo_tweak(tweak_id, state_path=state_path)
            results.append((tweak_id, True, None))
        except TweakError as exc:
            results.append((tweak_id, False, str(exc)))
    return results


def list_status(state_path=None):
    """Returns (tweak, current_value, applied_record) for every tweak in the catalog."""
    statuses = []
    for tweak in catalog.list_tweaks():
        try:
            current_value = tweak.get_current_value()
        except TweakError:
            current_value = None
        record = state_store.get_applied(tweak.id, path=state_path)
        statuses.append((tweak, current_value, record))
    return statuses
