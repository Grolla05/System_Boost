"""Predefined optimization levels bundling temp cleanup with reversible tweaks."""
from . import cleaner
from .privileges import is_admin
from .tweaks import manager as tweaks_manager
from .tweaks import catalog as tweaks_catalog
from .tweaks.base import TweakError

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
    return {k: v for k, v in allowed.items() if k in level["clean_paths"]}


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
    return applicable, skipped


def apply_level_tweaks(level_id, state_path=None):
    """Applies every applicable tweak in the level, collecting (id, status, note) per tweak.

    status is True (applied), False (failed), or None (skipped — requires admin).
    """
    applicable, skipped = resolve_tweak_plan(level_id)
    results = []
    for tweak_id in applicable:
        try:
            tweaks_manager.apply_tweak(tweak_id, state_path=state_path)
            results.append((tweak_id, True, None))
        except TweakError as exc:
            results.append((tweak_id, False, str(exc)))
    for tweak_id in skipped:
        results.append((tweak_id, None, "requer administrador"))
    return results
