import pytest

from backend import profiles
from backend.tweaks.base import TweakError


class _Aggregate:
    previews_items = True

    def __init__(self, items):
        self.items = items

    def get_current_value(self):
        if isinstance(self.items, Exception):
            raise self.items
        return self.items


class _Plain:
    previews_items = False

    def get_current_value(self):
        raise AssertionError("não deve consultar ajustes simples")


def _catalog(monkeypatch, tweaks):
    monkeypatch.setattr(profiles.tweaks_catalog, "get_tweak", tweaks.__getitem__)


def test_preview_lists_item_names_of_aggregate_tweaks(monkeypatch):
    _catalog(monkeypatch, {
        "svc": _Aggregate([{"name": "Foo", "start_type": "auto"}]),
        "task": _Aggregate([{"task": "\\\\Vendor\\\\Sync"}]),
        "plain": _Plain(),
    })

    preview = profiles.preview_tweak_items(["svc", "task", "plain"])

    assert preview == {"svc": ["Foo"], "task": ["Sync"]}




def test_preview_survives_a_failing_tweak(monkeypatch):
    _catalog(monkeypatch, {"svc": _Aggregate(TweakError("falhou"))})

    assert profiles.preview_tweak_items(["svc"]) == {}


class _Growing:
    id = "svc"
    label = "svc"
    requires_admin = False
    previews_items = True

    def __init__(self, items):
        self.items = items
        self.applied = []

    def get_current_value(self):
        return [dict(item) for item in self.items]

    def apply(self):
        changed = [{"name": item["name"]} for item in self.items]
        self.applied.extend(changed)
        self.items = []
        return changed


def _manager(monkeypatch, tweak):
    from backend.tweaks import catalog, manager

    monkeypatch.setattr(catalog, "get_tweak", lambda tweak_id: tweak)
    return manager


def test_reapplying_aggregate_handles_only_new_items(monkeypatch, tmp_path):
    state = tmp_path / "s.json"
    tweak = _Growing([{"name": "Foo"}])
    manager = _manager(monkeypatch, tweak)
    manager.apply_tweak("svc", state_path=state)
    tweak.items = [{"name": "Bar"}]

    assert manager.apply_tweak("svc", state_path=state) == [{"name": "Bar"}]

    record = manager.state_store.get_applied("svc", path=state)
    assert [i["name"] for i in record["previous_value"]] == ["Foo", "Bar"]
    assert [i["name"] for i in record["applied_value"]] == ["Foo", "Bar"]
    assert record["status"] == "applied"


def test_reapplying_aggregate_with_nothing_new_is_already_applied(monkeypatch, tmp_path):
    from backend.tweaks.base import TweakAlreadyApplied

    state = tmp_path / "s.json"
    manager = _manager(monkeypatch, _Growing([{"name": "Foo"}]))
    manager.apply_tweak("svc", state_path=state)

    with pytest.raises(TweakAlreadyApplied):
        manager.apply_tweak("svc", state_path=state)


def test_item_changed_back_keeps_its_original_value(monkeypatch, tmp_path):
    from backend.tweaks.base import TweakAlreadyApplied

    state = tmp_path / "s.json"
    tweak = _Growing([{"name": "Foo", "start": "auto"}])
    manager = _manager(monkeypatch, tweak)
    manager.apply_tweak("svc", state_path=state)
    tweak.items = [{"name": "Foo", "start": "demand"}]

    with pytest.raises(TweakAlreadyApplied):
        manager.apply_tweak("svc", state_path=state)

    assert manager.state_store.get_applied("svc", path=state)["previous_value"][0]["start"] == "auto"


def test_failed_extension_stays_listed_for_undo(monkeypatch, tmp_path):
    state = tmp_path / "s.json"
    tweak = _Growing([{"name": "Foo"}])
    manager = _manager(monkeypatch, tweak)
    manager.apply_tweak("svc", state_path=state)
    tweak.items = [{"name": "Bar"}]

    def boom():
        raise RuntimeError("queda")

    tweak.apply = boom
    with pytest.raises(RuntimeError):
        manager.apply_tweak("svc", state_path=state)

    assert [i["name"] for i in manager.state_store.get_applied("svc", path=state)["previous_value"]] == ["Foo", "Bar"]
