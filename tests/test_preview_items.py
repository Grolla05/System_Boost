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


def test_preview_lists_item_names_of_aggregate_tweaks(monkeypatch, tmp_path):
    _catalog(monkeypatch, {
        "svc": _Aggregate([{"name": "Foo", "start_type": "auto"}]),
        "task": _Aggregate([{"task": "\\\\Vendor\\\\Sync"}]),
        "plain": _Plain(),
    })

    preview = profiles.preview_tweak_items(["svc", "task", "plain"], state_path=tmp_path / "s.json")

    assert preview == {"svc": ["Foo"], "task": ["Sync"]}


def test_preview_skips_already_applied(monkeypatch, tmp_path):
    state = tmp_path / "s.json"
    _catalog(monkeypatch, {"svc": _Aggregate([{"name": "Foo"}])})
    profiles.state_store.save_applied("svc", [], [], True, path=state)

    assert profiles.preview_tweak_items(["svc"], state_path=state) == {}


def test_preview_survives_a_failing_tweak(monkeypatch, tmp_path):
    _catalog(monkeypatch, {"svc": _Aggregate(TweakError("falhou"))})

    assert profiles.preview_tweak_items(["svc"], state_path=tmp_path / "s.json") == {}
