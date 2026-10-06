import pytest

from backend.tweaks.hibernation import HibernationTweak, _POWER_KEY
from backend.tweaks.base import TweakError


def _patch(monkeypatch, fake_winreg, fake_run):
    import backend.tweaks.hibernation as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return module


def test_get_current_value_reads_hibernate_enabled(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    fake_winreg.seed(fake_winreg.HKEY_LOCAL_MACHINE, _POWER_KEY, "HibernateEnabled", 1)
    tweak = HibernationTweak()

    assert tweak.get_current_value() == 1


def test_get_current_value_defaults_to_enabled_when_value_missing(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = HibernationTweak()

    assert tweak.get_current_value() == 1


def test_apply_turns_hibernation_off(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = HibernationTweak()

    result = tweak.apply()

    assert result == 0
    assert fake_run.calls[-1] == ["powercfg", "/hibernate", "off"]


def test_undo_restores_previous_state_on(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = HibernationTweak()

    tweak.undo(1)

    assert fake_run.calls[-1] == ["powercfg", "/hibernate", "on"]


def test_undo_restores_previous_state_off(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = HibernationTweak()

    tweak.undo(0)

    assert fake_run.calls[-1] == ["powercfg", "/hibernate", "off"]


def test_apply_raises_on_nonzero_exit(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    fake_run.returncode = 1
    tweak = HibernationTweak()

    with pytest.raises(TweakError):
        tweak.apply()
