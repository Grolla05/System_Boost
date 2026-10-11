import json

import pytest

from backend.tweaks import mouse_acceleration as mod
from backend.tweaks.mouse_acceleration import MouseAccelerationTweak

_MOUSE = "Control Panel\\Mouse"


@pytest.fixture
def notified(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "_notify", lambda t1, t2, speed: calls.append((t1, t2, speed)))
    return calls


@pytest.fixture
def tweak(monkeypatch, fake_winreg, notified):
    monkeypatch.setattr(mod, "winreg", fake_winreg)
    return MouseAccelerationTweak()


def _seed_enabled(fake_winreg):
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _MOUSE, "MouseSpeed", "1")
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _MOUSE, "MouseThreshold1", "6")
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _MOUSE, "MouseThreshold2", "10")


def _read(fake_winreg, name):
    return fake_winreg.QueryValueEx((fake_winreg.HKEY_CURRENT_USER, _MOUSE), name)[0]


def test_metadata_is_user_scope_no_admin(tweak):
    assert tweak.id == "mouse_acceleration"
    assert tweak.label
    assert tweak.requires_admin is False


def test_get_current_value_reports_existing_and_missing(tweak, fake_winreg):
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _MOUSE, "MouseSpeed", "1")

    value = tweak.get_current_value()

    assert value == {"MouseSpeed": "1", "MouseThreshold1": None, "MouseThreshold2": None}
    json.dumps(value)


def test_apply_writes_zero_strings_and_notifies_system(tweak, fake_winreg, notified):
    _seed_enabled(fake_winreg)

    items = tweak.apply()

    for name in ("MouseSpeed", "MouseThreshold1", "MouseThreshold2"):
        assert _read(fake_winreg, name) == "0"
    assert notified == [(0, 0, 0)]
    assert items == [{"name": "Enhance pointer precision"}]


def test_apply_returns_empty_when_already_off(tweak, fake_winreg):
    fake_winreg.seed(fake_winreg.HKEY_CURRENT_USER, _MOUSE, "MouseSpeed", "0")

    assert tweak.apply() == []


def test_undo_restores_original_values_and_notifies(tweak, fake_winreg, notified):
    _seed_enabled(fake_winreg)
    previous = tweak.get_current_value()
    tweak.apply()
    notified.clear()

    tweak.undo(previous)

    assert _read(fake_winreg, "MouseSpeed") == "1"
    assert _read(fake_winreg, "MouseThreshold1") == "6"
    assert _read(fake_winreg, "MouseThreshold2") == "10"
    assert notified == [(6, 10, 1)]


def test_undo_deletes_values_that_did_not_exist(tweak, fake_winreg):
    tweak.apply()

    tweak.undo({"MouseSpeed": None, "MouseThreshold1": None, "MouseThreshold2": None})

    for name in ("MouseSpeed", "MouseThreshold1", "MouseThreshold2"):
        assert not fake_winreg.has_value(fake_winreg.HKEY_CURRENT_USER, _MOUSE, name)


def test_notify_failure_does_not_raise(monkeypatch):
    class _Boom:
        class windll:
            class user32:
                @staticmethod
                def SystemParametersInfoW(*args):
                    raise OSError("boom")

    monkeypatch.setattr(mod, "ctypes", _Boom)

    mod._notify(0, 0, 0)
