import pytest

from backend.tweaks import manager
from backend.tweaks.base import Tweak, TweakError


class StubTweak(Tweak):
    """Test double: records call order and lets tests script get_current_value/apply/undo."""

    def __init__(self, tweak_id, requires_admin=False, current_value="before", applied_value="after"):
        self.id = tweak_id
        self.label = tweak_id
        self.description = tweak_id
        self.requires_admin = requires_admin
        self.current_value = current_value
        self.applied_value = applied_value
        self.calls = []
        self.fail_undo = False

    def get_current_value(self):
        self.calls.append("get_current_value")
        return self.current_value

    def apply(self):
        self.calls.append("apply")
        return self.applied_value

    def undo(self, previous_value):
        self.calls.append(("undo", previous_value))
        if self.fail_undo:
            raise TweakError(f"undo failed for {self.id}")
        return previous_value


def _get_tweak(tweaks_by_id, tid):
    try:
        return tweaks_by_id[tid]
    except KeyError:
        raise TweakError(f"Ajuste desconhecido: '{tid}'.") from None


def _patch_catalog(monkeypatch, tweaks_by_id):
    monkeypatch.setattr(manager.catalog, "get_tweak", lambda tid: _get_tweak(tweaks_by_id, tid))
    monkeypatch.setattr(manager.catalog, "list_tweaks", lambda: list(tweaks_by_id.values()))


def test_apply_saves_previous_value_before_mutating(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    tweak = StubTweak("t1", current_value="before", applied_value="after")
    _patch_catalog(monkeypatch, {"t1": tweak})
    monkeypatch.setattr(manager, "is_admin", lambda: True)

    manager.apply_tweak("t1", state_path=state_path)

    assert tweak.calls == ["get_current_value", "apply"]
    record = manager.state_store.get_applied("t1", path=state_path)
    assert record["previous_value"] == "before"
    assert record["applied_value"] == "after"


def test_apply_unknown_id_raises(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch, {})

    with pytest.raises(TweakError):
        manager.apply_tweak("nonexistent", state_path=tmp_path / "state.json")


def test_apply_admin_required_but_not_elevated_never_calls_apply(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    tweak = StubTweak("t1", requires_admin=True)
    _patch_catalog(monkeypatch, {"t1": tweak})
    monkeypatch.setattr(manager, "is_admin", lambda: False)

    with pytest.raises(TweakError):
        manager.apply_tweak("t1", state_path=state_path)

    assert "apply" not in tweak.calls
    assert manager.state_store.get_applied("t1", path=state_path) is None


def test_reapplying_an_already_applied_tweak_raises_and_keeps_original_value(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    tweak = StubTweak("t1", current_value="original", applied_value="after")
    _patch_catalog(monkeypatch, {"t1": tweak})
    monkeypatch.setattr(manager, "is_admin", lambda: True)
    manager.apply_tweak("t1", state_path=state_path)

    tweak.current_value = "after"  # simulate the tweak now reflecting the applied state
    with pytest.raises(TweakError):
        manager.apply_tweak("t1", state_path=state_path)

    record = manager.state_store.get_applied("t1", path=state_path)
    assert record["previous_value"] == "original"


def test_undo_restores_exact_saved_previous_value(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    tweak = StubTweak("t1", current_value="before", applied_value="after")
    _patch_catalog(monkeypatch, {"t1": tweak})
    monkeypatch.setattr(manager, "is_admin", lambda: True)
    manager.apply_tweak("t1", state_path=state_path)

    manager.undo_tweak("t1", state_path=state_path)

    assert tweak.calls[-1] == ("undo", "before")
    assert manager.state_store.get_applied("t1", path=state_path) is None


def test_undo_unknown_id_raises_gracefully(monkeypatch, tmp_path):
    _patch_catalog(monkeypatch, {})

    with pytest.raises(TweakError):
        manager.undo_tweak("nonexistent", state_path=tmp_path / "state.json")


def test_undo_nothing_applied_raises(monkeypatch, tmp_path):
    tweak = StubTweak("t1")
    _patch_catalog(monkeypatch, {"t1": tweak})
    monkeypatch.setattr(manager, "is_admin", lambda: True)

    with pytest.raises(TweakError):
        manager.undo_tweak("t1", state_path=tmp_path / "state.json")


def test_undo_admin_required_but_not_elevated_keeps_record(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    tweak = StubTweak("t1", requires_admin=True, current_value="before", applied_value="after")
    _patch_catalog(monkeypatch, {"t1": tweak})
    monkeypatch.setattr(manager, "is_admin", lambda: True)
    manager.apply_tweak("t1", state_path=state_path)

    monkeypatch.setattr(manager, "is_admin", lambda: False)
    with pytest.raises(TweakError):
        manager.undo_tweak("t1", state_path=state_path)

    assert manager.state_store.get_applied("t1", path=state_path) is not None


def test_undo_all_replays_most_recent_first_and_survives_one_failure(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    t1 = StubTweak("t1", current_value="v1", applied_value="a1")
    t2 = StubTweak("t2", current_value="v2", applied_value="a2")
    t3 = StubTweak("t3", current_value="v3", applied_value="a3")
    _patch_catalog(monkeypatch, {"t1": t1, "t2": t2, "t3": t3})
    monkeypatch.setattr(manager, "is_admin", lambda: True)

    manager.apply_tweak("t1", state_path=state_path)
    manager.apply_tweak("t2", state_path=state_path)
    manager.apply_tweak("t3", state_path=state_path)
    t2.fail_undo = True

    results = manager.undo_all(state_path=state_path)

    order = [tid for tid, _, _ in results]
    assert order == ["t3", "t2", "t1"]
    outcomes = {tid: success for tid, success, _ in results}
    assert outcomes == {"t1": True, "t2": False, "t3": True}
    assert manager.state_store.get_applied("t2", path=state_path) is not None
    assert manager.state_store.get_applied("t1", path=state_path) is None
    assert manager.state_store.get_applied("t3", path=state_path) is None
