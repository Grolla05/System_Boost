import re
from pathlib import Path

import pytest

import build

ROOT = Path(__file__).resolve().parent.parent


def test_build_command_requests_uac_admin_manifest():
    cmd = build.build_command("version_info.txt")

    assert "--uac-admin" in cmd


def test_build_command_keeps_existing_flags():
    cmd = build.build_command("version_info.txt")

    for flag in ("--onefile", "--console", "--name=System Boost", "--clean", "--noconfirm", "--distpath=./dist"):
        assert flag in cmd
    assert cmd[0] == "pyinstaller"
    assert cmd[-1] == "main.py"


def test_build_command_embeds_version_resource():
    cmd = build.build_command("somewhere/version_info.txt")

    assert "--version-file=somewhere/version_info.txt" in cmd


def test_project_version_matches_pyproject():
    declared = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)

    assert build.project_version() == declared


@pytest.mark.parametrize("version,expected", [
    ("0.1.0", (0, 1, 0, 0)),
    ("1.2.3", (1, 2, 3, 0)),
    ("2.0", (2, 0, 0, 0)),
    ("1.2.3rc1", (1, 2, 3, 0)),   # pre-release suffix must not break the 4-int Windows version
])
def test_version_tuple(version, expected):
    assert build.version_tuple(version) == expected


def test_version_file_carries_publisher_identity(tmp_path):
    path = build.write_version_file(tmp_path / "version_info.txt", "0.1.0")

    text = Path(path).read_text(encoding="utf-8")
    assert "System Boost by Felipe Grolla" in text
    assert "StringStruct('CompanyName', 'Felipe Grolla')" in text
    assert "StringStruct('ProductName', 'System Boost')" in text
    assert "StringStruct('OriginalFilename', 'System Boost.exe')" in text
    assert "filevers=(0, 1, 0, 0)" in text
    assert "prodvers=(0, 1, 0, 0)" in text
    assert "StringStruct('FileVersion', '0.1.0')" in text


def test_version_file_is_valid_python_for_pyinstaller(tmp_path):
    """PyInstaller exec()s this file; it must parse and build a VSVersionInfo."""
    from PyInstaller.utils.win32.versioninfo import (  # noqa: F401  (names used by exec)
        FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo,
    )

    path = build.write_version_file(tmp_path / "version_info.txt", "0.1.0")
    namespace = dict(locals())
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), namespace)

    assert namespace["VSVersionInfo"] is VSVersionInfo


# --- optional code signing (what makes the UAC "Publisher" line real) -------

def test_sign_command_uses_thumbprint_and_publisher_description():
    cmd = build.sign_command("dist/System Boost.exe", "ABC123")

    assert cmd[0] == "signtool"
    assert cmd[1] == "sign"
    assert "/sha1" in cmd and cmd[cmd.index("/sha1") + 1] == "ABC123"
    assert cmd[cmd.index("/fd") + 1] == "SHA256"
    assert "/tr" in cmd and "/td" in cmd
    assert cmd[cmd.index("/d") + 1] == "System Boost by Felipe Grolla"
    assert cmd[-1] == "dist/System Boost.exe"


def test_signing_is_skipped_without_thumbprint(monkeypatch):
    monkeypatch.delenv(build.SIGN_ENV_VAR, raising=False)
    calls = []
    monkeypatch.setattr(build.subprocess, "check_call", lambda cmd, **k: calls.append(cmd))

    assert build.sign_if_configured("dist/System Boost.exe") is False
    assert calls == []


def test_signing_runs_signtool_when_thumbprint_set(monkeypatch):
    monkeypatch.setenv(build.SIGN_ENV_VAR, "ABC123")
    calls = []
    monkeypatch.setattr(build.subprocess, "check_call", lambda cmd, **k: calls.append(cmd))

    assert build.sign_if_configured("dist/System Boost.exe") is True
    assert calls[0][0] == "signtool"
    assert "ABC123" in calls[0]


def _fake_tasklist(monkeypatch, stdout="", returncode=0, raises=None):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if raises:
            raise raises
        return build.subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(build.subprocess, "run", fake_run)
    return calls


def test_running_exe_detected_when_tasklist_lists_it(monkeypatch):
    calls = _fake_tasklist(monkeypatch, stdout='"System Boost.exe","1234","Console","1","50,000 K"\n')

    assert build.is_exe_running() is True
    assert calls[0][0].lower() == "tasklist"
    assert "System Boost.exe" in " ".join(calls[0])


def test_running_exe_not_detected_when_tasklist_has_no_match(monkeypatch):
    # tasklist prints a localized "no tasks" message, which must not match the exe name
    _fake_tasklist(monkeypatch, stdout="INFORMACAO: nenhuma tarefa em execucao.\n")

    assert build.is_exe_running() is False


@pytest.mark.parametrize("raises", [OSError("no tasklist"), build.subprocess.TimeoutExpired("tasklist", 10)])
def test_running_exe_check_never_blocks_build_on_failure(monkeypatch, raises):
    _fake_tasklist(monkeypatch, raises=raises)

    assert build.is_exe_running() is False


def test_build_aborts_before_pyinstaller_when_exe_is_running(monkeypatch, capsys):
    monkeypatch.setattr(build, "is_exe_running", lambda: True)
    called = []
    monkeypatch.setattr(build.subprocess, "check_call", lambda *a, **k: called.append(a))

    build.build()

    assert called == []
    assert "System Boost.exe" in capsys.readouterr().out
