import json

import pytest

from backend.tweaks import recommendations_offers as mod
from backend.tweaks.recommendations_offers import RecommendationsOffersTweak

_CDM = "Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager"
_PRIVACY = "Software\\Microsoft\\Windows\\CurrentVersion\\Privacy"
_ADVANCED = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced"
_ADS = "Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo"
_ACCOUNT_NOTIFICATIONS = "Software\\Microsoft\\Windows\\CurrentVersion\\SystemSettings\\AccountNotifications"
_LANG = "Control Panel\\International\\User Profile"


@pytest.fixture
def tweak(monkeypatch, fake_winreg):
    monkeypatch.setattr(mod, "winreg", fake_winreg)
    return RecommendationsOffersTweak()


def test_metadata_is_user_scope_no_admin(tweak):
    assert tweak.id == "recommendations_offers"
    assert tweak.label
    assert tweak.requires_admin is False


def test_get_current_value_reports_existing_and_missing(tweak, fake_winreg):
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _PRIVACY, "TailoredExperiencesWithDiagnosticDataEnabled", 1)

    value = tweak.get_current_value()
    by_name = {(v["path"], v["name"]): v["previous"] for v in value}

    assert by_name[(_PRIVACY, "TailoredExperiencesWithDiagnosticDataEnabled")] == 1
    assert by_name[(_LANG, "HttpAcceptLanguageOptOut")] is None
    json.dumps(value)


def test_apply_writes_every_switch_target(tweak, fake_winreg):
    tweak.apply()

    def read(path, name):
        return fake_winreg.QueryValueEx((fake_winreg.HKEY_CURRENT_USER, path), name)[0]

    assert read(_PRIVACY, "TailoredExperiencesWithDiagnosticDataEnabled") == 0
    assert read(_LANG, "HttpAcceptLanguageOptOut") == 1
    assert read(_ADVANCED, "Start_TrackProgs") == 0
    assert read(_ADS, "Enabled") == 0
    assert read(_ACCOUNT_NOTIFICATIONS, "EnableAccountNotifications") == 0
    for name in ("SubscribedContent-338389Enabled", "SubscribedContent-338393Enabled",
                 "SubscribedContent-353694Enabled", "SubscribedContent-353696Enabled"):
        assert read(_CDM, name) == 0


def test_apply_returns_one_item_per_switch_that_changed(tweak, fake_winreg):
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _ADS, "Enabled", 0)  # already off

    items = tweak.apply()

    names = [i["name"] for i in items]
    assert len(names) == len(set(names))
    assert "Advertising ID" not in names
    assert "Personalized offers" in names
    assert "Recommendations and offers in Settings" in names
    json.dumps(items)


def test_apply_failure_on_one_value_does_not_abort_the_rest(monkeypatch, tweak, fake_winreg):
    real_set = fake_winreg.SetValueEx

    def flaky(handle, name, reserved, type_, value):
        if name == "Start_TrackProgs":
            raise OSError("denied")
        real_set(handle, name, reserved, type_, value)

    monkeypatch.setattr(fake_winreg, "SetValueEx", flaky)

    items = tweak.apply()

    names = [i["name"] for i in items]
    assert "Improve Start and search results" not in names
    assert "Personalized offers" in names


def test_undo_restores_previous_values_and_deletes_the_ones_that_did_not_exist(tweak, fake_winreg):
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _ADVANCED, "Start_TrackProgs", 1)
    previous = tweak.get_current_value()
    tweak.apply()

    tweak.undo(previous)

    assert fake_winreg.QueryValueEx((fake_winreg.HKEY_CURRENT_USER, _ADVANCED), "Start_TrackProgs")[0] == 1
    assert not fake_winreg.has_value(fake_winreg.HKEY_CURRENT_USER, _LANG, "HttpAcceptLanguageOptOut")
    assert not fake_winreg.has_value(fake_winreg.HKEY_CURRENT_USER, _CDM, "SubscribedContent-338393Enabled")


def test_undo_is_tolerant_of_missing_values(tweak):
    tweak.undo([{"path": _LANG, "name": "HttpAcceptLanguageOptOut", "previous": None}])
