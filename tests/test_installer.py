from pathlib import Path

import pytest

import installer


ROOT = Path(__file__).resolve().parent.parent


def test_installer_script_packages_executable_and_user_shortcuts():
    script = (ROOT / "installer.iss").read_text(encoding="utf-8")

    assert 'Source: "{#SourceDir}\\System Boost.exe"; DestDir: "{app}"' in script
    assert "PrivilegesRequired=lowest" in script
    assert "DefaultDirName={localappdata}\\Programs\\System Boost" in script
    assert "Uninstallable=yes" in script
    assert "[Icons]" in script
    assert 'Name: "{autoprograms}\\System Boost"' in script


def test_installer_command_uses_project_version_and_dist_output(tmp_path):
    command = installer.compiler_command("C:/Inno Setup/ISCC.exe", "0.1.0", tmp_path)

    assert command[0] == "C:/Inno Setup/ISCC.exe"
    assert "/DAppVersion=0.1.0" in command
    assert f"/O{tmp_path}" in command
    assert command[-1].endswith("installer.iss")


def test_resolve_compiler_reports_missing_compiler(monkeypatch, tmp_path):
    monkeypatch.delenv(installer.COMPILER_ENV_VAR, raising=False)
    monkeypatch.setattr(installer.shutil, "which", lambda _: None)
    monkeypatch.setattr(installer, "_default_compiler_paths", lambda: [])

    with pytest.raises(installer.InstallerError, match="Inno Setup.*ISCC.exe"):
        installer.resolve_compiler()


def test_resolve_compiler_finds_per_user_inno_setup(monkeypatch, tmp_path):
    compiler = tmp_path / "Programs" / "Inno Setup 6" / "ISCC.exe"
    compiler.parent.mkdir(parents=True)
    compiler.write_bytes(b"compiler")
    monkeypatch.delenv(installer.COMPILER_ENV_VAR, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    # CI images may have a machine-wide Inno Setup install, which the resolver
    # correctly checks first. Keep this test focused on the per-user fallback.
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "Program Files (x86)"))
    monkeypatch.setattr(installer.shutil, "which", lambda _: None)

    assert installer.resolve_compiler() == str(compiler)


def test_build_installer_reports_missing_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, "ROOT", tmp_path)
    monkeypatch.setattr(installer, "EXECUTABLE_PATH", tmp_path / "dist" / "System Boost.exe")
    monkeypatch.setattr(installer, "resolve_compiler", lambda: "ISCC.exe")
    (tmp_path / "dist").mkdir()

    with pytest.raises(installer.InstallerError, match="System Boost.exe.*python build.py"):
        installer.build_installer(build_executable=False)


def test_build_runs_executable_then_installer_build(monkeypatch, tmp_path):
    monkeypatch.setattr(installer, "ROOT", tmp_path)
    monkeypatch.setattr(installer, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(installer, "EXECUTABLE_PATH", tmp_path / "dist" / "System Boost.exe")
    monkeypatch.setattr(installer, "INSTALLER_SCRIPT", tmp_path / "installer.iss")
    monkeypatch.setattr(installer, "resolve_compiler", lambda: "ISCC.exe")
    dist = tmp_path / "dist"
    dist.mkdir()
    (tmp_path / "installer.iss").write_text("", encoding="utf-8")
    (dist / "System Boost.exe").write_bytes(b"exe")
    calls = []

    def fake_check_call(command, **kwargs):
        calls.append(command)
        if command[0] == "ISCC.exe":
            (dist / "System Boost Setup.exe").write_bytes(b"setup")

    monkeypatch.setattr(installer.subprocess, "check_call", fake_check_call)

    installer.build_installer(build_executable=True)

    assert len(calls) == 2
    assert calls[0][-1].endswith("build.py")
    assert calls[1][0] == "ISCC.exe"


def test_build_installer_without_build_requires_existing_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, "ROOT", tmp_path)
    monkeypatch.setattr(installer, "EXECUTABLE_PATH", tmp_path / "dist" / "System Boost.exe")
    monkeypatch.setattr(installer, "resolve_compiler", lambda: "ISCC.exe")
    (tmp_path / "dist").mkdir()

    with pytest.raises(installer.InstallerError, match="System Boost.exe"):
        installer.build_installer(build_executable=False)


def test_installer_script_creates_desktop_shortcut():
    script = (ROOT / "installer.iss").read_text(encoding="utf-8")

    assert 'Name: "{autodesktop}\System Boost"; Filename: "{app}\{#AppExeName}"' in script
    # Always created (no optional [Tasks] entry), so the post-install launch can rely on it.
    assert "[Tasks]" not in script


def test_installer_script_launches_app_through_shortcut_after_install():
    script = (ROOT / "installer.iss").read_text(encoding="utf-8")
    run = script.split("[Run]")[1]

    # The exe requires Administrator (--uac-admin) while the setup runs unelevated, so a plain
    # CreateProcess fails with error 740; going through the .lnk with shellexec triggers UAC.
    assert 'Filename: "{autodesktop}\System Boost.lnk"' in run
    assert "postinstall" in run and "shellexec" in run and "nowait" in run
