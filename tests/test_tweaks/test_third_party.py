import pytest

from backend.tweaks import third_party


@pytest.fixture(autouse=True)
def _windows_root(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")


def test_extract_executable_handles_quotes_and_arguments():
    assert third_party.extract_executable(r'"C:\Program Files\App\app.exe" --silent') == r"C:\Program Files\App\app.exe"
    assert third_party.extract_executable(r"C:\Tools\tool.exe /min") == r"C:\Tools\tool.exe"
    assert third_party.extract_executable("") == ""


def test_extract_executable_expands_environment_variables(monkeypatch):
    monkeypatch.setenv("APPDATA", r"C:\Users\x\AppData\Roaming")
    assert third_party.extract_executable(r"%APPDATA%\Foo\foo.exe -x") == r"C:\Users\x\AppData\Roaming\Foo\foo.exe"


def test_ordinary_user_app_is_third_party():
    assert third_party.is_third_party("Spotify", r'"C:\Users\x\AppData\Roaming\Spotify\Spotify.exe" --autostart')


@pytest.mark.parametrize("name,command", [
    ("SecurityHealth", r"C:\Windows\System32\SecurityHealthSystray.exe"),
    ("Edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ("svc", r"C:\Windows\system32\svchost.exe -k netsvcs"),
])
def test_windows_and_microsoft_items_are_never_third_party(name, command):
    assert not third_party.is_third_party(name, command)


@pytest.mark.parametrize("name,command", [
    ("Avast Antivirus", r"C:\Program Files\Avast Software\Avast\AvastUI.exe"),
    ("RtkAudUService", r"C:\Program Files\Realtek\Audio\RtkAudUService64.exe"),
    ("NVIDIA Overlay", r"C:\Program Files\NVIDIA Corporation\NvContainer\nvcontainer.exe"),
    ("Logitech", r"C:\Program Files\Logitech\LogiOptions\logioptions.exe"),
    ("OneDrive", r"C:\Users\x\AppData\Local\Microsoft\OneDrive\OneDrive.exe"),
    ("NordVPN", r"C:\Program Files\NordVPN\NordVPN.exe"),
    ("Windscribe", r"C:\Program Files\Windscribe\Windscribe.exe"),
])
def test_exceptions_list_protects_security_drivers_and_essentials(name, command):
    assert not third_party.is_third_party(name, command)


def test_unknown_command_is_left_alone():
    assert not third_party.is_third_party("Mystery", "")


def test_short_exception_names_do_not_match_inside_other_words():
    # 'amd' must not protect a ramdisk tool.
    assert third_party.is_third_party("RamDisk", r"C:\Tools\ramdisk\ramdisk.exe")
