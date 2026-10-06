"""Instantiates the concrete reversible tweaks available in this tool."""
try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows dev machine
    winreg = None

from .base import TweakError
from .registry_value import RegistryValueTweak
from .services import ServiceStateTweak
from .scheduled_tasks import ScheduledTaskTweak
from .power_plan import PowerPlanTweak
from .hibernation import HibernationTweak

_VISUAL_EFFECTS_KEY = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects"
_TELEMETRY_KEY = "SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection"
# Confirmed via `schtasks /Query /FO CSV` on the dev machine — this build's task
# carries an "Exp" suffix not present on older Windows releases.
_COMPAT_APPRAISER_TASK = r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser Exp"


def _build_catalog():
    """Builds the id -> Tweak instance mapping for all available tweaks."""
    return {
        "power_plan": PowerPlanTweak(),
        "hibernation": HibernationTweak(),
        "visual_effects": RegistryValueTweak(
            tweak_id="visual_effects",
            label="Efeitos visuais: melhor desempenho",
            description="Ajusta os efeitos visuais do Windows para melhor desempenho.",
            hive=winreg.HKEY_CURRENT_USER,
            key_path=_VISUAL_EFFECTS_KEY,
            value_name="VisualFXSetting",
            target_value=2,
            requires_admin=False,
        ),
        "telemetry": RegistryValueTweak(
            tweak_id="telemetry",
            label="Minimizar telemetria",
            description="Restringe a coleta de telemetria do Windows ao mínimo.",
            hive=winreg.HKEY_LOCAL_MACHINE,
            key_path=_TELEMETRY_KEY,
            value_name="AllowTelemetry",
            target_value=0,
            requires_admin=True,
        ),
        "indexing": ServiceStateTweak(
            tweak_id="indexing",
            label="Desativar indexação de pesquisa",
            description="Desativa o serviço de indexação de pesquisa do Windows (WSearch).",
            service_name="WSearch",
        ),
        "sysmain": ServiceStateTweak(
            tweak_id="sysmain",
            label="Desativar SysMain (Superfetch)",
            description="Desativa o serviço SysMain (Superfetch).",
            service_name="SysMain",
        ),
        "compat_appraiser": ScheduledTaskTweak(
            tweak_id="compat_appraiser",
            label="Desativar Compatibility Appraiser",
            description="Desativa a tarefa agendada de verificação de compatibilidade do Windows.",
            task_path=_COMPAT_APPRAISER_TASK,
        ),
    }


def list_tweaks():
    """Returns all available tweaks as a list, sorted by id."""
    catalog = _build_catalog()
    return [catalog[key] for key in sorted(catalog)]


def get_tweak(tweak_id):
    """Returns the Tweak instance for tweak_id, raising TweakError if unknown."""
    catalog = _build_catalog()
    try:
        return catalog[tweak_id]
    except KeyError:
        raise TweakError(f"Ajuste desconhecido: '{tweak_id}'.") from None
