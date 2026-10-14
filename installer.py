"""Build the standalone executable and package it with Inno Setup."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

import build as executable_build


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
EXECUTABLE_PATH = DIST_DIR / "System Boost.exe"
INSTALLER_SCRIPT = ROOT / "installer.iss"
COMPILER_ENV_VAR = "INNO_SETUP_COMPILER"


class InstallerError(RuntimeError):
    """Raised when installer prerequisites are missing or packaging fails."""


def _default_compiler_paths():
    program_files = os.environ.get("ProgramFiles(x86)")
    if not program_files:
        program_files = os.environ.get("ProgramFiles")
    local_app_data = os.environ.get("LOCALAPPDATA")
    candidates = []
    if program_files:
        candidates.append(Path(program_files) / "Inno Setup 6" / "ISCC.exe")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Inno Setup 6" / "ISCC.exe")
    candidates.append(Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"))
    candidates.append(Path("C:/Program Files/Inno Setup 6/ISCC.exe"))
    return candidates


def resolve_compiler():
    """Find ISCC.exe via explicit environment setting, PATH, or standard locations."""
    configured = os.environ.get(COMPILER_ENV_VAR)
    if configured:
        candidate = Path(configured.strip('"'))
        if candidate.is_file():
            return str(candidate)
        raise InstallerError(
            f"Inno Setup compiler not found at {candidate}. Install Inno Setup 6 or "
            f"set {COMPILER_ENV_VAR} to the full path of ISCC.exe."
        )

    from_path = shutil.which("ISCC.exe") or shutil.which("ISCC")
    if from_path:
        return from_path
    for candidate in _default_compiler_paths():
        if candidate.is_file():
            return str(candidate)
    raise InstallerError(
        "Inno Setup compiler (ISCC.exe) was not found. Install Inno Setup 6, add "
        "ISCC.exe to PATH, or set INNO_SETUP_COMPILER to its full path."
    )


def compiler_command(compiler, version, output_dir):
    """Return the ISCC invocation; paths are passed as argv items, not shell text."""
    return [
        str(compiler),
        f"/DAppVersion={version}",
        f"/DSourceDir={DIST_DIR}",
        f"/O{output_dir}",
        str(INSTALLER_SCRIPT),
    ]


def build_installer(build_executable=True):
    """Build the PyInstaller exe (unless disabled), then compile the Setup.exe."""
    if not build_executable and not EXECUTABLE_PATH.is_file():
        raise InstallerError(
            f"Required file not found: {EXECUTABLE_PATH}. Run python build.py first "
            "or use the default python installer.py command."
        )
    compiler = resolve_compiler()
    if build_executable:
        subprocess.check_call([sys.executable, "build.py"], cwd=ROOT)

    if not EXECUTABLE_PATH.is_file():
        raise InstallerError(
            f"Required file not found: {EXECUTABLE_PATH}. Run python build.py first "
            "or use the default python installer.py command."
        )
    if not INSTALLER_SCRIPT.is_file():
        raise InstallerError(f"Inno Setup script not found: {INSTALLER_SCRIPT}")

    version = executable_build.project_version()
    try:
        subprocess.check_call(
            compiler_command(compiler, version, DIST_DIR), cwd=ROOT
        )
    except FileNotFoundError as exc:
        raise InstallerError(
            f"Could not run Inno Setup compiler: {compiler}. Check the installation "
            f"or {COMPILER_ENV_VAR}."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise InstallerError(f"Inno Setup failed with exit code {exc.returncode}.") from exc

    output = DIST_DIR / "System Boost Setup.exe"
    if not output.is_file():
        raise InstallerError(f"Inno Setup completed without producing {output}.")
    print(f"Installer created: {output}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the System Boost executable and its Windows installer."
    )
    parser.add_argument(
        "--skip-build", action="store_true",
        help="Package the existing dist/System Boost.exe without rebuilding it.",
    )
    args = parser.parse_args(argv)
    try:
        build_installer(build_executable=not args.skip_build)
    except InstallerError as exc:
        print(f"Installer build failed: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Installer build failed: command exited with code {exc.returncode}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
