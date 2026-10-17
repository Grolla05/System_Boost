"""Predefined optimization levels bundling temp cleanup with reversible tweaks."""
from . import cleaner
from .logger import get_logger
from .privileges import is_admin
from .tweaks import manager as tweaks_manager
from .tweaks import catalog as tweaks_catalog
from .tweaks.base import TweakAlreadyApplied, TweakError

log = get_logger("profiles")

def _extend(previous_id, level_id, label, description, clean_paths=(), tweak_ids=(), clean_commands=()):
    """Builds a stage as the previous stage plus extras (union, previous order first, no repeats)."""
    previous = LEVELS[previous_id]
    return {
        "id": level_id,
        "label": label,
        "description": description,
        "clean_paths": previous["clean_paths"] + tuple(p for p in clean_paths if p not in previous["clean_paths"]),
        "clean_commands": previous["clean_commands"] + tuple(
            c for c in clean_commands if c not in previous["clean_commands"]),
        "tweak_ids": previous["tweak_ids"] + tuple(t for t in tweak_ids if t not in previous["tweak_ids"]),
    }


# Each stage is the previous one + its extras; descriptions read "STAGE N + [extras]".
LEVELS = {
    "leve": {
        "id": "leve",
        "label": "Leve",
        "description": (
            "Limpa o temp do usuário, esvazia a Lixeira e desativa apps, serviços e tarefas "
            "de terceiros que sobem com o sistema."
        ),
        "clean_paths": ("User Temp",),
        "clean_commands": ("recycle-bin",),
        "tweak_ids": ("startup_apps", "third_party_services", "third_party_tasks"),
    },
}
LEVELS["mediana"] = _extend(
    "leve", "mediana", "Mediana",
    "STAGE 1 + limpeza do Temp do Windows e de caches (Squirrel, npm, uv, Gradle, Go, .cache), "
    "hibernação desativada (apaga o hiberfil.sys; perde hibernação e "
    "inicialização rápida), plano de energia Alto Desempenho, ofertas/recomendações do Windows "
    "desligadas e precisão do ponteiro desativada.",
    clean_paths=("System Temp", "SquirrelTemp", "Gradle Cache", "Go Build Cache", "User Cache"),
    clean_commands=("npm-cache", "uv-cache"),
    tweak_ids=("power_plan", "recommendations_offers", "mouse_acceleration", "hibernation"),
)
LEVELS["alta"] = _extend(
    "mediana", "alta", "Alta",
    "STAGE 2 + efeitos visuais no modo melhor desempenho, "
    "indexação de pesquisa desativada e limpeza do Prefetch.",
    clean_paths=("Prefetch",), tweak_ids=("visual_effects", "indexing"),
)
LEVELS["extrema"] = _extend(
    "alta", "extrema", "Extrema",
    "STAGE 3 + ",
    tweak_ids=("telemetry", "sysmain", "compat_appraiser"),
)

LEVEL_ORDER = ("leve", "mediana", "alta", "extrema")


def resolve_clean_paths(level_id):
    """Returns {name: path} for the level's clean_paths, filtered to admin scope and to what exists."""
    all_paths = cleaner.get_temp_paths()
    admin = is_admin()
    allowed = all_paths if admin else {k: v for k, v in all_paths.items() if k not in cleaner.ADMIN_ONLY_PATHS}
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


def _item_label(item):
    """Display name for one item an aggregate tweak changed ({'name'|'task': ...})."""
    if isinstance(item, dict):
        if item.get("name"):
            return str(item["name"])
        if item.get("task"):
            return str(item["task"]).rsplit("\\", 1)[-1]
    return str(item)


def apply_level_tweaks(level_id, state_path=None, on_event=None):
    """Applies every applicable tweak in the level, collecting (id, status, note) per tweak.

    status is True (applied), "already" (already applied earlier — not a failure),
    False (failed), or None (skipped — requires admin).

    on_event(tweak_id, status, note), if given, is called live: "running" before each tweak,
    then its final status (same values as above), then one "item" event per individual item an
    aggregate tweak changed (note = the item's name).
    """
    def emit(tweak_id, status, note=None):
        if on_event:
            on_event(tweak_id, status, note)

    applicable, skipped = resolve_tweak_plan(level_id)
    results = []
    for tweak_id in applicable:
        log.info("ajuste '%s': aplicando", tweak_id)
        emit(tweak_id, "running")
        try:
            applied_value = tweaks_manager.apply_tweak(tweak_id, state_path=state_path)
            results.append((tweak_id, True, None))
            log.info("ajuste '%s': aplicado", tweak_id)
        except TweakAlreadyApplied as exc:
            results.append((tweak_id, "already", "já aplicado"))
            log.info("ajuste '%s': já aplicado (%s)", tweak_id, exc)
            emit(tweak_id, "already", "já aplicado")
            continue
        except TweakError as exc:
            results.append((tweak_id, False, str(exc)))
            log.error("ajuste '%s': FALHOU: %s", tweak_id, exc)
            emit(tweak_id, False, str(exc))
            continue
        if isinstance(applied_value, list):
            summary = f"{len(applied_value)} item(ns)" if applied_value else "nenhum item de terceiros"
            emit(tweak_id, True, summary)
            for item in applied_value:
                emit(tweak_id, "item", _item_label(item))
        else:
            emit(tweak_id, True)
    for tweak_id in skipped:
        results.append((tweak_id, None, "requer administrador"))
        log.warning("ajuste '%s': pulado (requer administrador)", tweak_id)
        emit(tweak_id, None, "requer administrador")
    return results
