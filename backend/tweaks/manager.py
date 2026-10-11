"""Applies and undoes reversible tweaks, coordinating catalog, state, and admin checks."""
from backend.logger import get_logger
from backend.privileges import is_admin

from . import catalog
from . import state_store
from .base import TweakAlreadyApplied, TweakError

log = get_logger("tweaks.manager")


def _require_admin_if_needed(tweak):
    """Raises TweakError if tweak needs admin rights and the process isn't elevated."""
    if tweak.requires_admin and not is_admin():
        log.warning("'%s' requer admin e o processo não está elevado", tweak.id)
        raise TweakError(
            f"'{tweak.label}' requer privilégios de administrador. "
            "Reabra o terminal como Administrador e tente novamente."
        )


def apply_tweak(tweak_id, state_path=None):
    """Applies tweak_id after checking admin and saving its current value for undo."""
    log.info("apply '%s': iniciando", tweak_id)
    tweak = catalog.get_tweak(tweak_id)
    _require_admin_if_needed(tweak)
    if state_store.get_applied(tweak_id, path=state_path) is not None:
        log.info("apply '%s': já consta como aplicado no state file", tweak_id)
        raise TweakAlreadyApplied(
            f"'{tweak_id}' já está aplicado. Rode `python main.py undo {tweak_id}` para desfazer."
        )
    previous_value = tweak.get_current_value()
    log.debug("apply '%s': valor atual=%r", tweak_id, previous_value)
    applied_value = tweak.apply()
    log.debug("apply '%s': valor aplicado=%r", tweak_id, applied_value)
    state_store.save_applied(tweak_id, previous_value, applied_value, tweak.requires_admin, path=state_path)
    log.info("apply '%s': concluído (%r -> %r)", tweak_id, previous_value, applied_value)
    return applied_value


def undo_tweak(tweak_id, state_path=None):
    """Undoes a previously applied tweak, restoring its saved previous value."""
    log.info("undo '%s': iniciando", tweak_id)
    tweak = catalog.get_tweak(tweak_id)
    _require_admin_if_needed(tweak)
    record = state_store.get_applied(tweak_id, path=state_path)
    if record is None:
        log.info("undo '%s': não aplicado, nada a fazer", tweak_id)
        raise TweakError(f"'{tweak_id}' não está aplicado — nada para desfazer.")
    tweak.undo(record["previous_value"])
    state_store.clear_applied(tweak_id, path=state_path)
    log.info("undo '%s': concluído (restaurado %r)", tweak_id, record["previous_value"])
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


def list_applied(state_path=None):
    """Returns (tweak, record) for every applied tweak, most recently applied first.

    Reads only the state file (no queries to Windows). Ids no longer in the catalog are skipped.
    """
    applied = []
    for record in state_store.list_applied(path=state_path):
        try:
            tweak = catalog.get_tweak(record["tweak_id"])
        except TweakError:
            log.warning("list_applied: '%s' consta no state file mas não está no catálogo", record["tweak_id"])
            continue
        applied.append((tweak, record))
    return applied


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
