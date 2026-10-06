import pytest

from backend.tweaks.power_plan import PowerPlanTweak, _POWER_SCHEMES_KEY
from backend.tweaks.base import TweakError

_BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
_HIGH_PERF_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"


def _patch(monkeypatch, fake_winreg, fake_run):
    import backend.tweaks.power_plan as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return module


def test_get_current_value_reads_active_scheme(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    fake_winreg.seed(fake_winreg.HKEY_LOCAL_MACHINE, _POWER_SCHEMES_KEY, "ActivePowerScheme", _BALANCED_GUID)
    tweak = PowerPlanTweak()

    assert tweak.get_current_value() == _BALANCED_GUID


def test_get_current_value_raises_when_key_missing(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = PowerPlanTweak()

    with pytest.raises(TweakError):
        tweak.get_current_value()


def test_apply_activates_high_performance_scheme(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = PowerPlanTweak()

    result = tweak.apply()

    assert result == _HIGH_PERF_GUID
    assert fake_run.calls[-1] == ["powercfg", "/setactive", _HIGH_PERF_GUID]


def test_undo_restores_previous_scheme(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = PowerPlanTweak()

    tweak.undo(_BALANCED_GUID)

    assert fake_run.calls[-1] == ["powercfg", "/setactive", _BALANCED_GUID]


def test_apply_raises_on_nonzero_exit(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    fake_run.returncode = 1
    tweak = PowerPlanTweak()

    with pytest.raises(TweakError):
        tweak.apply()
