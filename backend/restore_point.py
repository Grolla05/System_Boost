"""Windows restore point taken before a run changes the system."""
from backend._powershell import PS_PRELUDE, PowerShellError, run_powershell
from backend.logger import get_logger
from backend.privileges import is_admin

log = get_logger("restore_point")

RESTORE_TIMEOUT = 300

_SCRIPT = PS_PRELUDE + "Checkpoint-Computer -Description 'System Boost' -RestorePointType 'MODIFY_SETTINGS'"


def create_restore_point():
    """Asks Windows for a restore point; returns (ok, note) and never raises.

    Windows silently skips it when another one was made in the last 24 hours.
    """
    if not is_admin():
        log.warning("ponto de restauração: pulado, requer administrador")
        return False, "requer administrador"
    try:
        run_powershell(_SCRIPT, RESTORE_TIMEOUT)
    except PowerShellError as exc:
        log.error("ponto de restauração: falhou: %s", exc)
        return False, "não criado; verifique a Proteção do Sistema"
    log.info("ponto de restauração: solicitado")
    return True, "criado (ou já existe um recente)"
