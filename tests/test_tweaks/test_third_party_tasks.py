import json

import pytest

from backend.tweaks import third_party_tasks as mod
from backend.tweaks.third_party_tasks import ThirdPartyTasksTweak


def _task(path, command):
    return {"task": path, "command": command}


@pytest.fixture(autouse=True)
def _windows_root(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")


def test_metadata_requires_admin():
    tweak = ThirdPartyTasksTweak()
    assert tweak.id == "third_party_tasks"
    assert tweak.requires_admin is True


def test_get_current_value_keeps_only_third_party(monkeypatch):
    monkeypatch.setattr(mod, "discover_tasks", lambda: [
        _task(r"\GoogleUpdateTaskMachineCore", r"C:\Program Files\Google\Update\GoogleUpdate.exe"),
        _task(r"\MicrosoftEdgeUpdateTaskMachineCore", r"C:\Program Files (x86)\Microsoft\EdgeUpdate\MicrosoftEdgeUpdate.exe"),
        _task(r"\OneDrive Standalone Update Task", r"C:\Users\x\AppData\Local\Microsoft\OneDrive\OneDriveStandaloneUpdater.exe"),
        _task(r"\Avast\Scan", r"C:\Program Files\Avast Software\Avast\scan.exe"),
        _task(r"\Cleanup", r"C:\Windows\System32\cleanmgr.exe"),
    ])

    value = ThirdPartyTasksTweak().get_current_value()

    assert value == [{"task": r"\GoogleUpdateTaskMachineCore"}]
    json.dumps(value)


def test_apply_disables_each_task(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "discover_tasks", lambda: [_task(r"\A", r"C:\x\a.exe"), _task(r"\B", r"C:\x\b.exe")])
    monkeypatch.setattr(mod, "set_task_enabled", lambda t, e: calls.append((t, e)))

    assert ThirdPartyTasksTweak().apply() == [{"task": r"\A"}, {"task": r"\B"}]
    assert calls == [(r"\A", False), (r"\B", False)]


def test_apply_failure_does_not_abort(monkeypatch):
    def fake(task, enabled):
        if task == r"\A":
            raise OSError("x")

    monkeypatch.setattr(mod, "discover_tasks", lambda: [_task(r"\A", r"C:\x\a.exe"), _task(r"\B", r"C:\x\b.exe")])
    monkeypatch.setattr(mod, "set_task_enabled", fake)

    assert ThirdPartyTasksTweak().apply() == [{"task": r"\B"}]


def test_undo_reenables_tasks(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "set_task_enabled", lambda t, e: calls.append((t, e)))

    ThirdPartyTasksTweak().undo([{"task": r"\A"}, {"task": r"\B"}])

    assert calls == [(r"\A", True), (r"\B", True)]


def test_set_task_enabled_uses_schtasks(monkeypatch, fake_run):
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    mod.set_task_enabled(r"\A", False)
    mod.set_task_enabled(r"\A", True)

    assert fake_run.calls == [
        ["schtasks", "/Change", "/TN", r"\A", "/Disable"],
        ["schtasks", "/Change", "/TN", r"\A", "/Enable"],
    ]


def test_discover_tasks_parses_powershell_json(monkeypatch):
    payload = json.dumps([{"task": "\\A", "command": "C:\\x\\a.exe"}])
    monkeypatch.setattr(mod, "run_powershell", lambda script, timeout: payload)

    assert mod.discover_tasks() == [{"task": "\\A", "command": "C:\\x\\a.exe"}]


def test_discover_tasks_returns_empty_on_powershell_error(monkeypatch):
    from backend._powershell import PowerShellError

    def boom(script, timeout):
        raise PowerShellError("x")

    monkeypatch.setattr(mod, "run_powershell", boom)
    assert mod.discover_tasks() == []


def test_discover_tasks_empty_output(monkeypatch):
    monkeypatch.setattr(mod, "run_powershell", lambda script, timeout: "")
    assert mod.discover_tasks() == []
