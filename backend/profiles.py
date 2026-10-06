"""Predefined optimization levels bundling temp cleanup with reversible tweaks."""
from . import cleaner
from .logger import get_logger
from .privileges import is_admin
from .tweaks import manager as tweaks_manager
from .tweaks import catalog as tweaks_catalog
from .tweaks.base import TweakAlreadyApplied, TweakError

log = get_logger("profiles")

LEVELS = {
    "leve": {
        "id": "leve",
        "label": "Leve",
        "description": "Limpeza da pasta temporária do usuário e ajuste leve de efeitos visuais.",
        "clean_paths": ("User Temp",),
        "tweak_ids": ("visual_effects",),
    },
    "mediana": {
        "id": "mediana",
        "label": "Mediana",
        "description": "Leve + limpeza do temp do sistema e plano de energia de alto desempenho.",
        "clean_paths": ("User Temp", "System Temp"),
        "tweak_ids": ("visual_effects", "power_plan"),
    },
    "alta": {
        "id": "alta",
        "label": "Alta",
        "description": "Mediana + Prefetch, hibernação e indexação de pesquisa desativadas.",
        "clean_paths": ("User Temp", "System Temp", "Prefetch"),
        "tweak_ids": ("visual_effects", "power_plan", "hibernation", "indexing"),
    },
    "extrema": {
        "id": "extrema",
        "label": "Extrema",
        "description": "Alta + telemetria mínima, SysMain e tarefa de compatibilidade desativados.",
        "clean_paths": ("User Temp", "System Temp", "Prefetch"),
        "tweak_ids": (
            "visual_effects", "power_plan", "hibernation", "indexing",
            "telemetry", "sysmain", "compat_appraiser",
        ),
    },
}

LEVEL_ORDER = ("leve", "mediana", "alta", "extrema")


def resolve_clean_paths(level_id):
    """Returns {name: path} for the level's clean_paths, filtered to admin scope and to what exists."""
    all_paths = cleaner.get_temp_paths()
    admin = is_admin()
    allowed = all_paths if admin else {k: v for k, v in all_paths.items() if k == "User Temp"}
    level = LEVELS[level_id]
    resolved = {k: v for k, v in allowed.items() if k in level["clean_paths"]}
    log.info("nível '%s': admin=%s, pastas de limpeza=%s", level_id, admin, resolved)
    return resolved


def resolve_tweak_plan(level_id):
    """Returns (applicable_ids, skipped_ids) for the level given the current elevation."""
    admin = is_admin()
    applicable = []
    skipped = []
    for tweak_id in LEVELS[level_id]["tweak_ids"]:
        tweak = tweaks_catalog.get_tweak(tweak_id)
        if tweak.requires_admin and not admin:
            skipped.append(tweak_id)
        else:
            applicable.append(tweak_id)
    log.info("nível '%s': ajustes aplicáveis=%s, pulados (admin)=%s", level_id, applicable, skipped)
    return applicable, skipped


def apply_level_tweaks(level_id, state_path=None):
    """Applies every applicable tweak in the level, collecting (id, status, note) per tweak.

    status is True (applied), "already" (already applied earlier — not a failure),
    False (failed), or None (skipped — requires admin).
    """
    applicable, skipped = resolve_tweak_plan(level_id)
    results = []
    for tweak_id in applicable:
        log.info("ajuste '%s': aplicando", tweak_id)
        try:
            tweaks_manager.apply_tweak(tweak_id, state_path=state_path)
            results.append((tweak_id, True, None))
            log.info("ajuste '%s': aplicado", tweak_id)
        except TweakAlreadyApplied as exc:
            results.append((tweak_id, "already", "já aplicado"))
            log.info("ajuste '%s': já aplicado (%s)", tweak_id, exc)
        except TweakError as exc:
            results.append((tweak_id, False, str(exc)))
            log.error("ajuste '%s': FALHOU: %s", tweak_id, exc)
    for tweak_id in skipped:
        results.append((tweak_id, None, "requer administrador"))
        log.warning("ajuste '%s': pulado (requer administrador)", tweak_id)
    return results
