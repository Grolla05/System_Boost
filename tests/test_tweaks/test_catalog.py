import pytest

from backend.tweaks import catalog
from backend.tweaks.base import TweakError


def test_list_tweaks_returns_seven_unique_tweaks(monkeypatch, fake_winreg):
    monkeypatch.setattr(catalog, "winreg", fake_winreg)

    tweaks = catalog.list_tweaks()

    assert len(tweaks) == 7
    ids = [t.id for t in tweaks]
    assert len(set(ids)) == 7


def test_every_tweak_id_matches_its_catalog_key(monkeypatch, fake_winreg):
    monkeypatch.setattr(catalog, "winreg", fake_winreg)

    for tweak_id in ("power_plan", "hibernation", "visual_effects", "telemetry", "indexing", "sysmain", "compat_appraiser"):
        assert catalog.get_tweak(tweak_id).id == tweak_id


def test_get_tweak_raises_on_unknown_id(monkeypatch, fake_winreg):
    monkeypatch.setattr(catalog, "winreg", fake_winreg)

    with pytest.raises(TweakError):
        catalog.get_tweak("nonexistent")
