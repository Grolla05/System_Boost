import pytest

from backend import profiles
from backend.tweaks.base import TweakAlreadyApplied, TweakError


class _FakeTweak:
    def __init__(self, tweak_id, requires_admin):
        self.id = tweak_id
        self.label = tweak_id
        self.requires_admin = requires_admin


_ADMIN_BY_ID = {
    "visual_effects": False,
    "startup_apps": False,
    "recommendations_offers": False,
    "mouse_acceleration": False,
    "third_party_services": True,
    "third_party_tasks": True,
    "power_plan": False,
    "hibernation": True,
    "indexing": True,
    "telemetry": True,
    "sysmain": True,
    "compat_appraiser": True,
}


def _fake_get_tweak(tweak_id):
    return _FakeTweak(tweak_id, _ADMIN_BY_ID[tweak_id])


def _patch_catalog(monkeypatch):
    monkeypatch.setattr(profiles.tweaks_catalog, "get_tweak", _fake_get_tweak)


def _patch_temp_paths(monkeypatch, paths):
    monkeypatch.setattr(profiles.cleaner, "get_temp_paths", lambda: dict(paths))


_ALL_TEMP_PATHS = {"User Temp": r"C:\Users\x\AppData\Local\Temp", "System Temp": r"C:\Windows\Temp", "Prefetch": r"C:\Windows\Prefetch"}


def test_resolve_clean_paths_leve_only_user_temp(monkeypatch):
    _patch_temp_paths(monkeypatch, _ALL_TEMP_PATHS)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    assert set(profiles.resolve_clean_paths("leve")) == {"User Temp"}


def test_resolve_clean_paths_mediana_adds_system_temp(monkeypatch):
    _patch_temp_paths(monkeypatch, _ALL_TEMP_PATHS)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    assert set(profiles.resolve_clean_paths("mediana")) == {"User Temp", "System Temp"}


def test_resolve_clean_paths_alta_and_extrema_add_prefetch(monkeypatch):
    _patch_temp_paths(monkeypatch, _ALL_TEMP_PATHS)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    assert set(profiles.resolve_clean_paths("alta")) == {"User Temp", "System Temp", "Prefetch"}
    assert set(profiles.resolve_clean_paths("extrema")) == {"User Temp", "System Temp", "Prefetch"}


def test_resolve_clean_paths_non_admin_drops_system_and_prefetch(monkeypatch):
    _patch_temp_paths(monkeypatch, _ALL_TEMP_PATHS)
    monkeypatch.setattr(profiles, "is_admin", lambda: False)

    assert set(profiles.resolve_clean_paths("extrema")) == {"User Temp"}


def test_resolve_clean_paths_filters_to_existing_paths(monkeypatch):
    _patch_temp_paths(monkeypatch, {"User Temp": _ALL_TEMP_PATHS["User Temp"]})
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    assert set(profiles.resolve_clean_paths("extrema")) == {"User Temp"}


def test_resolve_tweak_plan_non_admin_splits_applicable_and_skipped(monkeypatch):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: False)

    applicable, skipped = profiles.resolve_tweak_plan("extrema")

    assert applicable == ["startup_apps", "power_plan", "recommendations_offers", "mouse_acceleration", "visual_effects"]
    assert skipped == [
        "third_party_services", "third_party_tasks",
        "hibernation", "indexing", "telemetry", "sysmain", "compat_appraiser",
    ]


def test_resolve_tweak_plan_admin_everything_applicable(monkeypatch):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    applicable, skipped = profiles.resolve_tweak_plan("extrema")

    assert applicable == list(profiles.LEVELS["extrema"]["tweak_ids"])
    assert skipped == []


def test_resolve_tweak_plan_leve_has_no_admin_tweaks_even_when_not_elevated(monkeypatch):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: False)

    applicable, skipped = profiles.resolve_tweak_plan("leve")

    assert applicable == ["startup_apps"]
    assert skipped == ["third_party_services", "third_party_tasks"]


def test_apply_level_tweaks_calls_only_applicable_ids(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: False)
    calls = []
    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", lambda tid, state_path=None: calls.append(tid))

    profiles.apply_level_tweaks("extrema", state_path=tmp_path / "state.json")

    assert calls == ["startup_apps", "power_plan", "recommendations_offers", "mouse_acceleration", "visual_effects"]


def test_apply_level_tweaks_collects_success_and_failure(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    def fake_apply(tid, state_path=None):
        if tid == "hibernation":
            raise TweakError("boom")

    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", fake_apply)

    results = profiles.apply_level_tweaks("alta", state_path=tmp_path / "state.json")
    by_id = {tid: (status, note) for tid, status, note in results}

    assert by_id["visual_effects"] == (True, None)
    assert by_id["hibernation"] == (False, "boom")


def test_apply_level_tweaks_includes_skipped_without_calling_apply(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: False)
    calls = []
    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", lambda tid, state_path=None: calls.append(tid))

    results = profiles.apply_level_tweaks("extrema", state_path=tmp_path / "state.json")
    by_id = {tid: (status, note) for tid, status, note in results}

    assert by_id["hibernation"][0] is None
    assert "hibernation" not in calls


def test_apply_level_tweaks_already_applied_is_not_a_failure(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    def fake_apply(tid, state_path=None):
        if tid == "startup_apps":
            raise TweakAlreadyApplied("já aplicado")

    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", fake_apply)

    results = profiles.apply_level_tweaks("leve", state_path=tmp_path / "state.json")

    assert results[0] == ("startup_apps", "already", "já aplicado")
    assert all(status is True for _, status, _ in results[1:])


def test_apply_level_tweaks_real_failure_still_false_alongside_already(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)

    def fake_apply(tid, state_path=None):
        if tid == "startup_apps":
            raise TweakAlreadyApplied("já aplicado")
        if tid == "power_plan":
            raise TweakError("falha real")

    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", fake_apply)

    results = profiles.apply_level_tweaks("mediana", state_path=tmp_path / "state.json")
    by_id = {tid: status for tid, status, _ in results}

    assert by_id["startup_apps"] == "already"
    assert by_id["power_plan"] is False
    assert by_id["third_party_services"] is True


def test_apply_level_tweaks_logs_each_step(monkeypatch, tmp_path, caplog):
    import logging
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)
    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", lambda tid, state_path=None: None)

    with caplog.at_level(logging.DEBUG, logger="system_boost"):
        profiles.apply_level_tweaks("leve", state_path=tmp_path / "state.json")

    assert "startup_apps" in caplog.text


def test_leve_includes_third_party_startup_management():
    ids = profiles.LEVELS["leve"]["tweak_ids"]
    assert {"startup_apps", "third_party_services", "third_party_tasks"} <= set(ids)


def test_each_stage_contains_the_previous_one_plus_extras():
    order = profiles.LEVEL_ORDER
    for prev_id, cur_id in zip(order, order[1:]):
        prev, cur = profiles.LEVELS[prev_id], profiles.LEVELS[cur_id]
        assert set(prev["tweak_ids"]) < set(cur["tweak_ids"]) or set(prev["clean_paths"]) < set(cur["clean_paths"])
        assert set(prev["tweak_ids"]) <= set(cur["tweak_ids"])
        assert set(prev["clean_paths"]) <= set(cur["clean_paths"])
        assert cur["tweak_ids"][:len(prev["tweak_ids"])] == prev["tweak_ids"]


def test_stage_descriptions_are_cumulative_labels():
    assert profiles.LEVELS["mediana"]["description"].startswith("STAGE 1 + ")
    assert profiles.LEVELS["alta"]["description"].startswith("STAGE 2 + ")
    assert profiles.LEVELS["extrema"]["description"].startswith("STAGE 3 + ")


# --- on_event (live mission log) ------------------------------------------

def _events_for(monkeypatch, tmp_path, level, admin, apply_impl):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: admin)
    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", apply_impl)
    events = []
    profiles.apply_level_tweaks(level, state_path=tmp_path / "s.json", on_event=lambda *e: events.append(e))
    return events


def test_on_event_emits_running_then_result_per_tweak(monkeypatch, tmp_path):
    events = _events_for(monkeypatch, tmp_path, "leve", True, lambda tid, state_path=None: None)

    assert events[0] == ("startup_apps", "running", None)
    assert events[1][:2] == ("startup_apps", True)


def test_on_event_lists_each_changed_item_on_its_own_line(monkeypatch, tmp_path):
    def apply(tid, state_path=None):
        if tid == "startup_apps":
            return [{"scope": "hkcu_run", "name": "Spotify"}, {"scope": "hkcu_run", "name": "Opera"}]
        if tid == "third_party_tasks":
            return [{"task": r"\Google\Updater"}]
        return None

    events = _events_for(monkeypatch, tmp_path, "leve", True, apply)

    items = [(tid, note) for tid, status, note in events if status == "item"]
    assert items == [("startup_apps", "Spotify"), ("startup_apps", "Opera"), ("third_party_tasks", "Updater")]


def test_on_event_summarizes_item_count(monkeypatch, tmp_path):
    events = _events_for(monkeypatch, tmp_path, "leve", True,
                         lambda tid, state_path=None: [{"name": "A"}, {"name": "B"}] if tid == "third_party_services" else None)

    done = [e for e in events if e[0] == "third_party_services" and e[1] is True]
    assert done == [("third_party_services", True, "2 item(ns)")]


def test_on_event_empty_list_says_nothing_found(monkeypatch, tmp_path):
    events = _events_for(monkeypatch, tmp_path, "leve", True,
                         lambda tid, state_path=None: [] if tid == "startup_apps" else None)

    done = [e for e in events if e[0] == "startup_apps" and e[1] is True]
    assert done == [("startup_apps", True, "nenhum item de terceiros")]


def test_on_event_already_failed_and_skipped(monkeypatch, tmp_path):
    def apply(tid, state_path=None):
        if tid == "startup_apps":
            raise TweakAlreadyApplied("já aplicado")
        if tid == "power_plan":
            raise TweakError("falha real")

    events = _events_for(monkeypatch, tmp_path, "mediana", False, apply)
    by = {(tid, status) for tid, status, _ in events}

    assert ("startup_apps", "already") in by
    assert ("power_plan", False) in by
    assert ("third_party_services", None) in by  # needs admin, not elevated


def test_on_event_is_optional(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: True)
    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", lambda tid, state_path=None: None)

    assert profiles.apply_level_tweaks("leve", state_path=tmp_path / "s.json")


def test_mediana_adds_power_plan_offers_and_mouse_acceleration_over_leve():
    leve, mediana = profiles.LEVELS["leve"], profiles.LEVELS["mediana"]
    assert "mouse_acceleration" not in leve["tweak_ids"]
    assert mediana["tweak_ids"][len(leve["tweak_ids"]):] == ("power_plan", "recommendations_offers", "mouse_acceleration")


def test_visual_effects_only_from_alta_onwards():
    assert "visual_effects" not in profiles.LEVELS["leve"]["tweak_ids"]
    assert "visual_effects" not in profiles.LEVELS["mediana"]["tweak_ids"]
    assert "visual_effects" in profiles.LEVELS["alta"]["tweak_ids"]
    assert "visual_effects" in profiles.LEVELS["extrema"]["tweak_ids"]
