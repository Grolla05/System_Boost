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


_OTHER_PATH = _TASK_PATH + " Exp"


def _with_fallback():
    return ScheduledTaskTweak("compat_appraiser", "x", "x", task_path=_OTHER_PATH, fallback_paths=(_TASK_PATH,))


def _only_task_exists(module, monkeypatch, existing):
    calls = []

    class Result:
        stdout = _XML_ENABLED
        stderr = b""

        def __init__(self, returncode):
            self.returncode = returncode

    def run(cmd, **kwargs):
        calls.append(cmd)
        return Result(1 if cmd[1] == "/Query" and cmd[3] != existing else 0)

    monkeypatch.setattr(module.subprocess, "run", run)
    return calls


def test_fallback_name_is_used_when_first_task_does_not_exist(monkeypatch, fake_run):
    module = _patch(monkeypatch, fake_run)
    calls = _only_task_exists(module, monkeypatch, _TASK_PATH)
    tweak = _with_fallback()

    assert tweak.get_current_value() == "Enabled"
    tweak.apply()

    assert calls[-1][1:4] == ["/Change", "/TN", _TASK_PATH]


def test_undo_finds_the_task_by_its_fallback_name(monkeypatch, fake_run):
    module = _patch(monkeypatch, fake_run)
    calls = _only_task_exists(module, monkeypatch, _TASK_PATH)

    _with_fallback().undo("Enabled")

    assert calls[-1][1:5] == ["/Change", "/TN", _TASK_PATH, "/Enable"]


def test_error_when_no_name_exists(monkeypatch, fake_run):
    module = _patch(monkeypatch, fake_run)
    _only_task_exists(module, monkeypatch, "nenhuma")

    with pytest.raises(TweakError):
        _with_fallback().get_current_value()
