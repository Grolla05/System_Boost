import pytest

from backend.tweaks.services import ServiceStateTweak
from backend.tweaks.base import TweakError


def _make_tweak():
    return ServiceStateTweak(
        tweak_id="sysmain",
        label="Desativar SysMain (Superfetch)",
        description="Desativa o serviço SysMain (Superfetch).",
        service_name="SysMain",
    )


def _patch(monkeypatch, fake_winreg, fake_run):
    import backend.tweaks.services as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return module


def test_get_current_value_reads_and_normalizes_start_type(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = _make_tweak()
    fake_winreg.seed(
        fake_winreg.HKEY_LOCAL_MACHINE,
        "SYSTEM\\CurrentControlSet\\Services\\SysMain",
        "Start",
        2,
    )

    assert tweak.get_current_value() == "auto"


def test_get_current_value_raises_when_service_missing(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = _make_tweak()

    with pytest.raises(TweakError):
        tweak.get_current_value()


def test_apply_configures_disabled_and_stops_service(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = _make_tweak()

    result = tweak.apply()

    assert result == "disabled"
    assert fake_run.calls[0] == ["sc", "config", "SysMain", "start=", "disabled"]
    assert fake_run.calls[1] == ["sc", "stop", "SysMain"]


def test_undo_restores_previous_start_type_and_starts_if_it_was_auto(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = _make_tweak()

    tweak.undo("auto")

    assert fake_run.calls[0] == ["sc", "config", "SysMain", "start=", "auto"]
    assert fake_run.calls[1] == ["sc", "start", "SysMain"]


def test_undo_does_not_start_service_if_previous_type_was_disabled(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    tweak = _make_tweak()

    tweak.undo("disabled")

    assert fake_run.calls == [["sc", "config", "SysMain", "start=", "disabled"]]


def test_apply_raises_on_nonzero_exit(monkeypatch, fake_winreg, fake_run):
    _patch(monkeypatch, fake_winreg, fake_run)
    fake_run.returncode = 1
    tweak = _make_tweak()

    with pytest.raises(TweakError):
        tweak.apply()
