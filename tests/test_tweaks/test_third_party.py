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
])
def test_exceptions_list_protects_security_drivers_and_essentials(name, command):
    assert not third_party.is_third_party(name, command)


def test_unknown_command_is_left_alone():
    assert not third_party.is_third_party("Mystery", "")


def test_short_exception_names_do_not_match_inside_other_words():
    # 'amd' must not protect a ramdisk tool.
    assert third_party.is_third_party("RamDisk", r"C:\Tools\ramdisk\ramdisk.exe")


PROTECTED = [
    # databases
    ("MySQL Workbench", r"C:\Program Files\MySQL\MySQL Workbench 8.0\MySQLWorkbench.exe"),
    ("MySQL80", r'"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe"'),
    ("postgresql-x64-16", r'"C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe"'),
    ("pgAdmin 4", r"C:\Program Files\PostgreSQL\16\pgAdmin 4\runtime\pgAdmin4.exe"),
    ("MongoDB Compass", r"C:\Users\x\AppData\Local\MongoDBCompass\MongoDBCompass.exe"),
    ("Redis", r"C:\Tools\redis\redis-server.exe"),
    ("DBeaver", r"C:\Program Files\DBeaver\dbeaver.exe"),
    # backup / cloud sync / passwords
    ("Dropbox", r"C:\Program Files (x86)\Dropbox\Client\Dropbox.exe"),
    ("Google Drive", r"C:\Program Files\Google\Drive File Stream\GoogleDriveFS.exe"),
    ("Veeam Agent", r"C:\Program Files\Veeam\Endpoint Backup\Veeam.EndPoint.Tray.exe"),
    ("Bitwarden", r"C:\Users\x\AppData\Local\Programs\Bitwarden\Bitwarden.exe"),
    ("1Password", r"C:\Users\x\AppData\Local\1Password\app\8\1Password.exe"),
    # VPN
    ("OpenVPNService", r"C:\Program Files\OpenVPN\bin\openvpnserv.exe"),
    ("WireGuardManager", r"C:\Program Files\WireGuard\wireguard.exe"),
    ("Tailscale", r"C:\Program Files\Tailscale\tailscaled.exe"),
    # security
    ("CSFalconService", r"C:\Program Files\CrowdStrike\CSFalconService.exe"),
    ("Avira.Spotlight", r"C:\Program Files\Avira\Security\Avira.exe"),
    ("TrendMicroX", r"C:\Program Files\TrendMicro\svc.exe"),
    # licensing
    ("AdskLicensingService", r"C:\Program Files (x86)\Common Files\Autodesk Shared\AdskLicensing\svc.exe"),
    ("FlexNet Licensing", r"C:\Program Files\Common Files\Macrovision Shared\lmgrd.exe"),
    # updaters
    ("GoogleUpdaterTaskSystem", r"C:\Program Files\Google\GoogleUpdater\updater.exe"),
    ("Firefox Background Update", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
]


@pytest.mark.parametrize("name,command", PROTECTED)
def test_protected_software_is_never_third_party(name, command):
    assert not third_party.is_third_party(name, command)


def test_ordinary_apps_stay_flagged():
    assert third_party.is_third_party("Discord", r"C:\Users\x\AppData\Local\Discord\Discord.exe")
    assert third_party.is_third_party("RamDisk", r"C:\Tools\ramdisk\ramdisk.exe")
