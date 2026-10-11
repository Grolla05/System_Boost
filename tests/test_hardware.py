import json

import pytest

from backend import hardware
from backend._powershell import PowerShellError

_NT = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
_CPU = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"


class _Key:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeWinReg:
    """Minimal in-memory stand-in for the winreg read API used by hardware.py."""

    HKEY_LOCAL_MACHINE = "HKLM"

    def __init__(self, data):
        self.data = data

    def OpenKey(self, root, path, *args, **kwargs):
        if not any(p == path for p, _ in self.data):
            raise FileNotFoundError(path)
        return _Key(path)

    def QueryValueEx(self, key, name):
        try:
            return self.data[(key.path, name)], 1
        except KeyError:
            raise FileNotFoundError(name)


def _windows_data():
    return {
        (_NT, "ProductName"): "Windows 10 Pro",
        (_NT, "DisplayVersion"): "23H2",
        (_NT, "CurrentBuildNumber"): "22631",
        (_NT, "UBR"): 4460,
        (_CPU, "ProcessorNameString"): "  AMD Ryzen 5 5600  6-Core Processor   ",
    }


def _cim(gpus=("NVIDIA GeForce RTX 3060",), disk=None, chassis=(3,), battery=False):
    return json.dumps({
        "gpus": list(gpus),
        "disk": disk if disk is not None else {
            "model": "Samsung SSD 980", "media": "SSD", "bus": "NVMe", "size": 500107862016,
        },
        "chassis": list(chassis),
        "battery": battery,
    })


@pytest.fixture
def machine(monkeypatch):
    """Healthy desktop: everything resolves. Tests override single pieces."""
    monkeypatch.setattr(hardware, "winreg", FakeWinReg(_windows_data()))
    monkeypatch.setattr(hardware, "run_powershell", lambda script, timeout: _cim())
    monkeypatch.setattr(hardware, "_installed_ram_kb", lambda: 16 * 1024 * 1024)
    monkeypatch.setattr(hardware.os, "cpu_count", lambda: 12)


# --- Windows -------------------------------------------------------------

def test_windows_11_detected_from_build_even_if_product_name_says_10(machine):
    info = hardware.get_machine_info()

    assert info.windows == "Windows 11 Pro"
    assert info.version == "23H2"
    assert info.build == "22631.4460"


def test_windows_10_name_kept_below_build_22000(machine, monkeypatch):
    data = _windows_data()
    data[(_NT, "CurrentBuildNumber")] = "19045"
    monkeypatch.setattr(hardware, "winreg", FakeWinReg(data))

    info = hardware.get_machine_info()

    assert info.windows == "Windows 10 Pro"
    assert info.build == "19045.4460"


def test_windows_build_without_ubr(machine, monkeypatch):
    data = _windows_data()
    del data[(_NT, "UBR")]
    monkeypatch.setattr(hardware, "winreg", FakeWinReg(data))

    assert hardware.get_machine_info().build == "22631"


def test_windows_version_falls_back_to_release_id(machine, monkeypatch):
    data = _windows_data()
    del data[(_NT, "DisplayVersion")]
    data[(_NT, "ReleaseId")] = "2009"
    monkeypatch.setattr(hardware, "winreg", FakeWinReg(data))

    assert hardware.get_machine_info().version == "2009"


def test_registry_failure_leaves_windows_and_cpu_none(machine, monkeypatch):
    monkeypatch.setattr(hardware, "winreg", FakeWinReg({}))

    info = hardware.get_machine_info()

    assert info.windows is None
    assert info.version is None
    assert info.build is None
    assert info.cpu is None
    # other fields are unaffected by the registry failing
    assert info.form_factor == "Desktop"


# --- CPU -----------------------------------------------------------------

def test_cpu_name_whitespace_collapsed_and_threads_reported(machine):
    info = hardware.get_machine_info()

    assert info.cpu == "AMD Ryzen 5 5600 6-Core Processor"
    assert info.threads == 12


# --- RAM -----------------------------------------------------------------

def test_ram_uses_physically_installed_memory(machine):
    assert hardware.get_machine_info().ram_gb == 16.0


def test_ram_falls_back_to_total_physical_when_installed_unavailable(machine, monkeypatch):
    def unavailable():
        raise OSError("GetPhysicallyInstalledSystemMemory failed")

    monkeypatch.setattr(hardware, "_installed_ram_kb", unavailable)
    monkeypatch.setattr(hardware, "_total_ram_bytes", lambda: 17_000_000_000)

    assert hardware.get_machine_info().ram_gb == pytest.approx(15.8, abs=0.05)


def test_ram_none_when_every_source_fails(machine, monkeypatch):
    def unavailable():
        raise OSError("nope")

    monkeypatch.setattr(hardware, "_installed_ram_kb", unavailable)
    monkeypatch.setattr(hardware, "_total_ram_bytes", unavailable)

    assert hardware.get_machine_info().ram_gb is None


# --- GPU -----------------------------------------------------------------

def test_gpus_listed_and_deduplicated(machine, monkeypatch):
    monkeypatch.setattr(
        hardware, "run_powershell",
        lambda s, t: _cim(gpus=["Intel(R) UHD Graphics", "NVIDIA GeForce RTX 3060", "Intel(R) UHD Graphics"]),
    )

    assert hardware.get_machine_info().gpus == ["Intel(R) UHD Graphics", "NVIDIA GeForce RTX 3060"]


def test_single_gpu_serialised_as_plain_string_is_accepted(machine, monkeypatch):
    # ConvertTo-Json collapses 1-item arrays in some PowerShell paths
    payload = json.loads(_cim())
    payload["gpus"] = "NVIDIA GeForce RTX 3060"
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: json.dumps(payload))

    assert hardware.get_machine_info().gpus == ["NVIDIA GeForce RTX 3060"]


# --- Disk ----------------------------------------------------------------

@pytest.mark.parametrize("media,bus,expected", [
    ("SSD", "SATA", "SSD"),
    ("HDD", "SATA", "HDD"),
    ("Unspecified", "NVMe", "SSD"),   # NVMe is always flash even if MediaType is blank
    ("Unspecified", "SATA", None),
    ("4", "SATA", "SSD"),             # numeric enum leaking from older PowerShell
    ("3", "SATA", "HDD"),
])
def test_disk_type_classification(machine, monkeypatch, media, bus, expected):
    disk = {"model": "Some Disk", "media": media, "bus": bus, "size": 1}
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: _cim(disk=disk))

    info = hardware.get_machine_info()

    assert info.disk_type == expected
    assert info.disk_model == "Some Disk"
    assert info.disk_bus == bus


def test_disk_missing_in_cim_leaves_disk_fields_none(machine, monkeypatch):
    payload = json.loads(_cim())
    payload["disk"] = None
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: json.dumps(payload))

    info = hardware.get_machine_info()

    assert info.disk_type is None
    assert info.disk_model is None


# --- Notebook vs desktop -------------------------------------------------

@pytest.mark.parametrize("chassis,battery,expected", [
    ([10], False, "Notebook"),
    ([9], False, "Notebook"),
    ([31], False, "Notebook"),        # convertible
    ([3], False, "Desktop"),
    ([3], True, "Desktop"),           # UPS/battery must not flip a tower to notebook
    ([1], True, "Notebook"),          # "Other" chassis: battery is the tiebreaker
    ([1], False, "Desktop"),
    ([2], False, "Desktop"),
    ([], False, None),                # nothing to go on
])
def test_form_factor(machine, monkeypatch, chassis, battery, expected):
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: _cim(chassis=chassis, battery=battery))

    assert hardware.get_machine_info().form_factor == expected


def test_single_chassis_value_not_wrapped_in_list_is_accepted(machine, monkeypatch):
    payload = json.loads(_cim())
    payload["chassis"] = 10
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: json.dumps(payload))

    assert hardware.get_machine_info().form_factor == "Notebook"


# --- PowerShell unavailable ----------------------------------------------

@pytest.mark.parametrize("failure", [
    PowerShellError("tempo esgotado"),
    PowerShellError("não foi possível executar o PowerShell"),
])
def test_powershell_failure_degrades_only_cim_fields(machine, monkeypatch, failure):
    def boom(script, timeout):
        raise failure

    monkeypatch.setattr(hardware, "run_powershell", boom)

    info = hardware.get_machine_info()

    assert info.gpus == []
    assert info.disk_type is None
    assert info.disk_model is None
    assert info.form_factor is None
    # registry/ctypes-backed fields still resolve
    assert info.windows == "Windows 11 Pro"
    assert info.cpu == "AMD Ryzen 5 5600 6-Core Processor"
    assert info.ram_gb == 16.0


def test_invalid_json_from_powershell_degrades_cim_fields(machine, monkeypatch):
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: "not json {{")

    info = hardware.get_machine_info()

    assert info.gpus == []
    assert info.form_factor is None
    assert info.windows == "Windows 11 Pro"


def test_empty_powershell_output_degrades_cim_fields(machine, monkeypatch):
    monkeypatch.setattr(hardware, "run_powershell", lambda s, t: "")

    assert hardware.get_machine_info().gpus == []


def test_get_machine_info_never_raises_when_everything_fails(monkeypatch):
    def boom(*a, **k):
        raise OSError("everything is on fire")

    monkeypatch.setattr(hardware, "winreg", FakeWinReg({}))
    monkeypatch.setattr(hardware, "run_powershell", boom)
    monkeypatch.setattr(hardware, "_installed_ram_kb", boom)
    monkeypatch.setattr(hardware, "_total_ram_bytes", boom)
    monkeypatch.setattr(hardware.os, "cpu_count", lambda: None)

    info = hardware.get_machine_info()

    assert info.windows is None
    assert info.cpu is None
    assert info.threads is None
    assert info.ram_gb is None
    assert info.gpus == []
    assert info.disk_type is None
    assert info.form_factor is None
