import os
import re
import subprocess
import sys
import tempfile

APP_NAME = "System Boost"
PUBLISHER = "Felipe Grolla"
DISPLAY_NAME = "System Boost by Felipe Grolla"

# Set to the SHA-1 thumbprint of a code-signing certificate in the Windows cert store to
# Authenticode-sign the exe after the build. Without a trusted certificate Windows UAC shows
# "Publisher: Unknown", whatever the version resource says.
SIGN_ENV_VAR = "SYSTEM_BOOST_SIGN_THUMBPRINT"
TIMESTAMP_URL = "http://timestamp.digicert.com"

_VERSION_TEMPLATE = """\
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={vers},
    prodvers={vers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', '{publisher}'),
        StringStruct('FileDescription', '{display_name}'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('InternalName', '{app_name}'),
        StringStruct('LegalCopyright', 'Copyright (c) {publisher}'),
        StringStruct('OriginalFilename', '{app_name}.exe'),
        StringStruct('ProductName', '{app_name}'),
        StringStruct('ProductVersion', '{version}')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def project_version():
    """Reads the version declared in pyproject.toml (single source of truth)."""
    root = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as f:
        match = re.search(r'^version\s*=\s*"([^"]+)"', f.read(), re.M)
    return match.group(1) if match else "0.0.0"


def version_tuple(version):
    """'1.2.3rc1' -> (1, 2, 3, 0): Windows file versions are exactly four integers."""
    parts = []
    for piece in version.split(".")[:4]:
        digits = re.match(r"\d+", piece)
        parts.append(int(digits.group()) if digits else 0)
    return tuple(parts + [0] * (4 - len(parts)))


def write_version_file(path, version):
    """Writes the PyInstaller version resource (publisher/product metadata) and returns its path."""
    content = _VERSION_TEMPLATE.format(
        vers=version_tuple(version), version=version, publisher=PUBLISHER,
        display_name=DISPLAY_NAME, app_name=APP_NAME,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def build_command(version_file):
    # --onefile: bundle into a single executable
    # --console: keep the console (rich UI)
    # --uac-admin: embed a manifest with requestedExecutionLevel=requireAdministrator, so
    #              Windows always shows the UAC prompt when the exe is launched
    # --version-file: embed publisher/product metadata (shown in file Properties)
    # --name: output filename
    # --clean: clean cache
    # --noconfirm: overwrite existing
    # --distpath: output directory
    return [
        "pyinstaller",
        "--onefile",
        "--console",
        "--uac-admin",
        f"--version-file={version_file}",
        f"--name={APP_NAME}",
        "--clean",
        "--noconfirm",
        "--distpath=./dist",
        "main.py",
    ]


def sign_command(exe_path, thumbprint):
    return [
        "signtool", "sign",
        "/sha1", thumbprint,
        "/fd", "SHA256",
        "/tr", TIMESTAMP_URL,
        "/td", "SHA256",
        "/d", DISPLAY_NAME,
        exe_path,
    ]


def sign_if_configured(exe_path):
    """Signs the exe when SYSTEM_BOOST_SIGN_THUMBPRINT is set. Returns True if it signed."""
    thumbprint = os.environ.get(SIGN_ENV_VAR)
    if not thumbprint:
        return False
    subprocess.check_call(sign_command(exe_path, thumbprint))
    return True


def is_exe_running():
    """True if a previous System Boost.exe is still running: Windows can't overwrite it then."""
    exe_name = f"{APP_NAME}.exe"
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return exe_name.lower() in (result.stdout or "").lower()


def build():
    print("Starting build process...")

    if is_exe_running():
        print(
            f"\nBuild aborted: {APP_NAME}.exe is still running and Windows cannot overwrite it.\n"
            f"Close its window (or run `Stop-Process -Name \"{APP_NAME}\" -Force` in an "
            "elevated PowerShell) and run build.py again."
        )
        return

    # Ensure dependencies are installed
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    try:
        # Outside ./build: `pyinstaller --clean` wipes that folder before it reads the file.
        with tempfile.TemporaryDirectory() as tmp:
            version_file = write_version_file(os.path.join(tmp, "version_info.txt"), project_version())
            subprocess.check_call(build_command(version_file))
        print("\nBuild successful! Executable located in /dist folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        return

    exe_path = os.path.join("dist", f"{APP_NAME}.exe")
    try:
        if sign_if_configured(exe_path):
            print(f"Signed {exe_path} as '{DISPLAY_NAME}'.")
        else:
            print(
                f"Not signed: set {SIGN_ENV_VAR} to a code-signing certificate thumbprint "
                "to show a verified publisher in the UAC prompt."
            )
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"\nSigning failed: {e}")


if __name__ == "__main__":
    build()
