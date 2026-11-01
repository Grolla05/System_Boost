"""Shared filter deciding whether a startup item / service / task belongs to third-party software.

Anything owned by Windows or Microsoft, or matching the exceptions list (security software,
hardware drivers, VPNs, databases, backup, licensing, updaters), is never touched.
"""
import os
import re

# Case-insensitive; each name only matches at the start of a word (a preceding letter blocks it),
# so 'amd' protects 'amdrsserv' but not 'ramdisk'. Edit this tuple to protect more software.
EXCEPTION_NAMES = (
    # security
    "defender", "securityhealth", "windows security", "avast", "avg", "avira", "kaspersky", "norton",
    "mcafee", "bitdefender", "eset", "malwarebytes", "sophos", "trend micro", "webroot", "crowdstrike",
    "csfalcon", "sentinel", "cylance", "cisco", "fortinet", "forticlient", "paloalto", "f-secure",
    "fsecure", "comodo", "panda", "gdata", "zonealarm",
    # hardware drivers / peripherals / audio
    "nvidia", "nv", "amd", "radeon", "intel", "realtek", "rtk", "synaptics", "elan", "logitech",
    "logi", "razer", "corsair", "steelseries", "asus", "dell", "hp", "lenovo", "msi", "bluetooth",
    "touchpad", "fingerprint",
    # cloud sync
    "onedrive",
    # virtualization / WSL
    "wsl", "docker", "vmware", "virtualbox", "hyper",
    # Microsoft-branded
    "microsoft", "windows",
    # databases
    "mysql", "mariadb", "postgres", "pgadmin", "mssql", "sqlserver", "sqlagent", "sqlbrowser",
    "sqlwriter", "ssms", "mongod", "mongodb", "compass", "redis", "memurai", "oracle", "firebird",
    "cassandra", "elasticsearch", "influxdb", "couchdb", "neo4j", "clickhouse", "cockroach",
    "dbeaver", "heidisql", "datagrip", "navicat",
    # backup / cloud sync / password managers / 2FA
    "dropbox", "google drive", "googledrive", "nextcloud", "syncthing", "resilio", "mega", "veeam",
    "acronis", "backblaze", "bitwarden", "1password", "keepass", "yubico", "authy",
    # VPN
    "wireguard", "tailscale", "zerotier",
    # software licensing
    "autodesk", "adsk", "flexnet", "flexlm", "hasp", "codemeter", "wibu",
)

# Matched anywhere in a word: these usually come glued to a vendor name (OpenVPN, GoogleUpdater).
ANYWHERE_NAMES = ("vpn", "update", "trendmicro")


def _compile(names, anywhere=()):
    pattern = r"(?<![a-z])(?:" + "|".join(re.escape(n) for n in names) + ")"
    if anywhere:
        pattern += "|" + "|".join(re.escape(n) for n in anywhere)
    return re.compile(pattern, re.IGNORECASE)


_EXCEPTION_RE = _compile(EXCEPTION_NAMES, ANYWHERE_NAMES)


def extract_executable(command):
    """Returns the executable path from a command line (quoted or not), env vars expanded."""
    command = os.path.expandvars((command or "").strip())
    if not command:
        return ""
    if command.startswith('"'):
        end = command.find('"', 1)
        return command[1:end] if end != -1 else command[1:]
    match = re.search(r"\.exe", command, re.IGNORECASE)
    if match:
        return command[:match.end()]
    return command.split(" ", 1)[0]


def _is_windows_owned(path):
    """True if path lives under %SystemRoot% or any 'Microsoft*' directory."""
    normalized = os.path.normcase(path)
    system_root = os.path.normcase(os.environ.get("SystemRoot", r"C:\Windows"))
    if normalized.startswith(system_root + os.sep):
        return True
    return "\\microsoft" in normalized


def is_third_party(name, command, display=None):
    """True only for items clearly owned by third-party software and not on the exceptions list.

    An empty command means the owner is unknown, so the item is left alone.
    """
    executable = extract_executable(command)
    if not executable:
        return False
    if _is_windows_owned(executable):
        return False
    haystack = " ".join(part for part in (name, display, executable) if part)
    return _EXCEPTION_RE.search(haystack) is None
