import pytest

from backend import profiles
from backend.tweaks.base import TweakError


class _FakeTweak:
    def __init__(self, tweak_id, requires_admin):
        self.id = tweak_id
        self.label = tweak_id
        self.requires_admin = requires_admin


_ADMIN_BY_ID = {
    "visual_effects": False,
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

    assert applicable == ["visual_effects", "power_plan"]
    assert skipped == ["hibernation", "indexing", "telemetry", "sysmain", "compat_appraiser"]


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

    assert applicable == ["visual_effects"]
    assert skipped == []


def test_apply_level_tweaks_calls_only_applicable_ids(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch)
    monkeypatch.setattr(profiles, "is_admin", lambda: False)
    calls = []
    monkeypatch.setattr(profiles.tweaks_manager, "apply_tweak", lambda tid, state_path=None: calls.append(tid))

    profiles.apply_level_tweaks("extrema", state_path=tmp_path / "state.json")

    assert calls == ["visual_effects", "power_plan"]


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
