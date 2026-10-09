import subprocess

import pytest

from backend import _powershell
from backend._powershell import PowerShellError, run_powershell


class _Completed:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_returns_decoded_stripped_stdout(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return _Completed(stdout="﻿  {\"a\": 1}\r\n".encode("utf-8"))

    monkeypatch.setattr(_powershell.subprocess, "run", fake_run)

    assert run_powershell("Get-Date", timeout=5) == '{"a": 1}'
    cmd, kwargs = calls[0]
    assert cmd[0] == "powershell.exe"
    assert "-NoProfile" in cmd and "-NonInteractive" in cmd
    assert cmd[-1] == "Get-Date"
    assert kwargs["timeout"] == 5
    assert kwargs["stdin"] == subprocess.DEVNULL


def test_nonzero_returncode_raises_with_stderr(monkeypatch):
    monkeypatch.setattr(
        _powershell.subprocess, "run",
        lambda *a, **k: _Completed(returncode=1, stderr=b"boom"),
    )

    with pytest.raises(PowerShellError, match="boom"):
        run_powershell("x", timeout=5)


def test_timeout_raises(monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="powershell.exe", timeout=5)

    monkeypatch.setattr(_powershell.subprocess, "run", fake_run)

    with pytest.raises(PowerShellError, match="tempo esgotado"):
        run_powershell("x", timeout=5)


def test_missing_executable_raises(monkeypatch):
    def fake_run(*a, **k):
        raise FileNotFoundError("powershell.exe")

    monkeypatch.setattr(_powershell.subprocess, "run", fake_run)

    with pytest.raises(PowerShellError):
        run_powershell("x", timeout=5)
