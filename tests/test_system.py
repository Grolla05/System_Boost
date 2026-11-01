import ntpath
import re
from pathlib import Path

import pytest

from backend import _system

ROOT = Path(__file__).resolve().parent.parent


def test_system_exe_ignores_the_environment(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Fake")

    path = _system.system_exe("sc")

    assert ntpath.isabs(path)
    assert path.lower().endswith(r"\system32\sc.exe")
    assert "fake" not in path.lower()


def test_powershell_exe_is_in_system32():
    assert _system.powershell_exe().lower().endswith(r"\system32\windowspowershell\v1.0\powershell.exe")


@pytest.mark.parametrize("folder", ["backend", "frontend"])
def test_no_bare_system_tool_in_subprocess_calls(folder):
    bare = re.compile(r'\[\s*"(sc|schtasks|powercfg|powershell(\.exe)?|cmd)"\s*,')
    offenders = [str(p) for p in (ROOT / folder).rglob("*.py") if bare.search(p.read_text(encoding="utf-8"))]

    assert offenders == []
