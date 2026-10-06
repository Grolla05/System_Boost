import pytest

from backend.tweaks.scheduled_tasks import ScheduledTaskTweak
from backend.tweaks.base import TweakError

_TASK_PATH = r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser"

_XML_ENABLED = b"""<?xml version="1.0" encoding="UTF-8"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Settings>
    <Enabled>true</Enabled>
  </Settings>
</Task>
"""

_XML_DISABLED = _XML_ENABLED.replace(b"true", b"false")


def _make_tweak():
    return ScheduledTaskTweak(
        tweak_id="compat_appraiser",
        label="Desativar Compatibility Appraiser",
        description="Desativa a tarefa agendada de verificação de compatibilidade do Windows.",
        task_path=_TASK_PATH,
    )


def _patch(monkeypatch, fake_run):
    import backend.tweaks.scheduled_tasks as module
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return module


def test_get_current_value_parses_enabled(monkeypatch, fake_run):
    _patch(monkeypatch, fake_run)
    fake_run.stdout = _XML_ENABLED
    tweak = _make_tweak()

    assert tweak.get_current_value() == "Enabled"


def test_get_current_value_parses_disabled(monkeypatch, fake_run):
    _patch(monkeypatch, fake_run)
    fake_run.stdout = _XML_DISABLED
    tweak = _make_tweak()

    assert tweak.get_current_value() == "Disabled"


def test_get_current_value_raises_when_task_not_found(monkeypatch, fake_run):
    _patch(monkeypatch, fake_run)
    fake_run.returncode = 1
    tweak = _make_tweak()

    with pytest.raises(TweakError):
        tweak.get_current_value()


def test_apply_disables_task(monkeypatch, fake_run):
    _patch(monkeypatch, fake_run)
    tweak = _make_tweak()

    result = tweak.apply()

    assert result == "Disabled"
    assert fake_run.calls[-1] == ["schtasks", "/Change", "/TN", _TASK_PATH, "/Disable"]


def test_undo_restores_enabled_state(monkeypatch, fake_run):
    _patch(monkeypatch, fake_run)
    tweak = _make_tweak()

    tweak.undo("Enabled")

    assert fake_run.calls[-1] == ["schtasks", "/Change", "/TN", _TASK_PATH, "/Enable"]


def test_apply_raises_on_nonzero_exit(monkeypatch, fake_run):
    _patch(monkeypatch, fake_run)
    fake_run.returncode = 1
    tweak = _make_tweak()

    with pytest.raises(TweakError):
        tweak.apply()
