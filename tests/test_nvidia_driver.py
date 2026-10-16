import json

import pytest

from backend import nvidia_driver
from backend._powershell import PowerShellError

SERIES_XML = (
    '<?xml version="1.0"?><LookupValueSearch><LookupValues>'
    '<LookupValue ParentID="1"><Name>GeForce RTX 40 Series (Notebooks)</Name><Value>129</Value></LookupValue>'
    '<LookupValue ParentID="1"><Name>GeForce RTX 40 Series</Name><Value>127</Value></LookupValue>'
    '<LookupValue ParentID="1"><Name>GeForce GTX 16 Series</Name><Value>112</Value></LookupValue>'
    '</LookupValues></LookupValueSearch>'
).encode()

PRODUCTS = {
    "127": (
        '<LookupValueSearch><LookupValues>'
        '<LookupValue ParentID="127"><Name>NVIDIA GeForce RTX 4070 Ti</Name><Value>1001</Value></LookupValue>'
        '<LookupValue ParentID="127"><Name>NVIDIA GeForce RTX 4070</Name><Value>1015</Value></LookupValue>'
        '</LookupValues></LookupValueSearch>'
    ).encode(),
    "129": (
        '<LookupValueSearch><LookupValues>'
        '<LookupValue ParentID="129"><Name>GeForce RTX 4060 Laptop GPU</Name><Value>1007</Value></LookupValue>'
        '</LookupValues></LookupValueSearch>'
    ).encode(),
    "112": b"<LookupValueSearch><LookupValues></LookupValues></LookupValueSearch>",
}

GOOD_URL = "https://us.download.nvidia.com/Windows/617.42/617.42-desktop-win10-win11-64bit-international-dch-whql.exe"


def _driver_json(version="617.42", url=GOOD_URL):
    return json.dumps({"Success": "1", "IDS": [{"downloadInfo": {"Version": version, "DownloadURL": url}}]}).encode()


def fake_fetch(driver_payload=None):
    def fetch(url, timeout=30):
        if "TypeID=2" in url:
            return SERIES_XML
        if "TypeID=3" in url:
            return PRODUCTS[url.split("ParentID=")[1].split("&")[0]]
        if "AjaxDriverService" in url:
            return driver_payload if driver_payload is not None else _driver_json()
        raise AssertionError(url)
    return fetch


# --- versions ------------------------------------------------------------------

@pytest.mark.parametrize("windows,expected", [
    ("31.0.15.5123", "551.23"),
    ("32.0.15.6094", "560.94"),
    ("32.0.15.9174", "591.74"),
    ("27.21.14.5671", "456.71"),
])
def test_windows_driver_version_maps_to_nvidia_version(windows, expected):
    assert nvidia_driver.windows_to_nvidia_version(windows) == expected


@pytest.mark.parametrize("bad", ["", None, "abc", "1.2", "31.0.x.y"])
def test_invalid_windows_version_returns_none(bad):
    assert nvidia_driver.windows_to_nvidia_version(bad) is None


def test_is_newer_compares_numerically():
    assert nvidia_driver.is_newer("617.42", "551.23")
    assert nvidia_driver.is_newer("1000.01", "999.99")
    assert not nvidia_driver.is_newer("551.23", "551.23")
    assert not nvidia_driver.is_newer("540.00", "551.23")


# --- GPU detection -----------------------------------------------------------------

def test_get_nvidia_gpus_keeps_only_nvidia(monkeypatch):
    payload = json.dumps([
        {"name": "Intel(R) UHD Graphics", "driver_version": "31.0.101.1"},
        {"name": "NVIDIA GeForce RTX 4070", "driver_version": "31.0.15.5123"},
        {"name": "AMD Radeon RX 6600", "driver_version": "31.0.1"},
    ])
    monkeypatch.setattr(nvidia_driver, "run_powershell", lambda script, timeout: payload)

    assert nvidia_driver.get_nvidia_gpus() == [
        {"name": "NVIDIA GeForce RTX 4070", "driver_version": "31.0.15.5123"}
    ]


def test_get_nvidia_gpus_accepts_single_object_and_empty_output(monkeypatch):
    monkeypatch.setattr(nvidia_driver, "run_powershell",
                        lambda s, t: json.dumps({"name": "NVIDIA GeForce GTX 1060", "driver_version": "1"}))
    assert len(nvidia_driver.get_nvidia_gpus()) == 1
    monkeypatch.setattr(nvidia_driver, "run_powershell", lambda s, t: "")
    assert nvidia_driver.get_nvidia_gpus() == []


# --- product + latest lookup -----------------------------------------------------------

def test_find_product_matches_desktop_gpu(monkeypatch):
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch())
    assert nvidia_driver.find_product("NVIDIA GeForce RTX 4070") == ("127", "1015")


def test_find_product_matches_notebook_gpu_in_notebook_series(monkeypatch):
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch())
    assert nvidia_driver.find_product("NVIDIA GeForce RTX 4060 Laptop GPU") == ("129", "1007")


def test_find_product_without_match_raises(monkeypatch):
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch())
    with pytest.raises(nvidia_driver.NvidiaDriverError, match="não encontrada"):
        nvidia_driver.find_product("NVIDIA GeForce RTX 9999")


def test_lookup_latest_returns_version_and_url(monkeypatch):
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch())
    assert nvidia_driver.lookup_latest("127", "1015") == ("617.42", GOOD_URL)


def test_lookup_latest_requests_game_ready_whql_dch(monkeypatch):
    seen = []

    def fetch(url, timeout=30):
        seen.append(url)
        return _driver_json()

    monkeypatch.setattr(nvidia_driver, "_fetch", fetch)
    nvidia_driver.lookup_latest("127", "1015")

    assert "upCRD=0" in seen[0] and "isWHQL=1" in seen[0] and "dch=1" in seen[0]


def test_lookup_latest_not_found_raises(monkeypatch):
    payload = json.dumps({"Success": "0", "IDS": [{"downloadInfo": {"Success": "0", "ID": ""}}]}).encode()
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch(payload))
    with pytest.raises(nvidia_driver.NvidiaDriverError):
        nvidia_driver.lookup_latest("127", "1015")


def test_lookup_latest_rejects_untrusted_download_url(monkeypatch):
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch(_driver_json(url="https://evil.example.com/x.exe")))
    with pytest.raises(nvidia_driver.NvidiaDriverError, match="URL"):
        nvidia_driver.lookup_latest("127", "1015")


@pytest.mark.parametrize("url", [
    "http://us.download.nvidia.com/x.exe",
    "https://nvidia.com.evil.io/x.exe",
    "https://evil.example.com/nvidia.com/x.exe",
    "ftp://us.download.nvidia.com/x.exe",
    "https://us.download.nvidia.com/readme.txt",
])
def test_validate_download_url_rejects(url):
    with pytest.raises(nvidia_driver.NvidiaDriverError):
        nvidia_driver.validate_download_url(url)


def test_validate_download_url_accepts_nvidia_https_exe():
    nvidia_driver.validate_download_url(GOOD_URL)


# --- check_update -------------------------------------------------------------------------

def _gpus(monkeypatch, gpus):
    monkeypatch.setattr(nvidia_driver, "get_nvidia_gpus", lambda: gpus)


def test_check_update_without_nvidia_returns_none(monkeypatch):
    _gpus(monkeypatch, [])
    assert nvidia_driver.check_update() is None


def test_check_update_returns_update_when_newer(monkeypatch):
    _gpus(monkeypatch, [{"name": "NVIDIA GeForce RTX 4070", "driver_version": "31.0.15.5123"}])
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch())

    update = nvidia_driver.check_update()

    assert update.gpu == "NVIDIA GeForce RTX 4070"
    assert (update.installed, update.latest, update.url) == ("551.23", "617.42", GOOD_URL)
    assert "617.42" in update.title and "RTX 4070" in update.title


def test_check_update_returns_none_when_up_to_date(monkeypatch):
    _gpus(monkeypatch, [{"name": "NVIDIA GeForce RTX 4070", "driver_version": "32.0.16.1742"}])
    monkeypatch.setattr(nvidia_driver, "_fetch", fake_fetch())
    assert nvidia_driver.check_update() is None


def test_check_update_network_failure_raises_domain_error(monkeypatch):
    _gpus(monkeypatch, [{"name": "NVIDIA GeForce RTX 4070", "driver_version": "31.0.15.5123"}])

    def boom(url, timeout=30):
        raise OSError("sem rede")

    monkeypatch.setattr(nvidia_driver, "_fetch", boom)
    with pytest.raises(nvidia_driver.NvidiaDriverError, match="NVIDIA"):
        nvidia_driver.check_update()


def test_check_update_ignores_powershell_failure(monkeypatch):
    def boom():
        raise PowerShellError("x")

    monkeypatch.setattr(nvidia_driver, "get_nvidia_gpus", boom)
    assert nvidia_driver.check_update() is None


# --- install ------------------------------------------------------------------------------

class _Done:
    def __init__(self, returncode=0):
        self.returncode = returncode


def _update():
    return nvidia_driver.NvidiaUpdate("NVIDIA GeForce RTX 4070", "551.23", "617.42", GOOD_URL)


def test_install_downloads_verifies_signature_then_runs_silent(monkeypatch, tmp_path):
    steps = []
    monkeypatch.setattr(nvidia_driver, "_download", lambda url, dest: (steps.append("download"), dest.write_bytes(b"x")))
    monkeypatch.setattr(nvidia_driver, "_verify_signature", lambda path: steps.append("verify"))

    def fake_run(cmd, **kwargs):
        steps.append(("run", cmd))
        return _Done(0)

    monkeypatch.setattr(nvidia_driver.subprocess, "run", fake_run)

    ok, reboot, note = nvidia_driver.install_update(_update(), workdir=tmp_path)

    assert ok is True and reboot is False
    assert steps[0] == "download" and steps[1] == "verify"
    cmd = steps[2][1]
    assert "-s" in cmd and "-noreboot" in cmd and "-noeula" in cmd and "-clean" not in cmd
    assert list(tmp_path.iterdir()) == []  # installer removed


def test_install_does_not_run_when_signature_invalid(monkeypatch, tmp_path):
    monkeypatch.setattr(nvidia_driver, "_download", lambda url, dest: dest.write_bytes(b"x"))

    def bad(path):
        raise nvidia_driver.NvidiaDriverError("assinatura inválida")

    monkeypatch.setattr(nvidia_driver, "_verify_signature", bad)
    ran = []
    monkeypatch.setattr(nvidia_driver.subprocess, "run", lambda *a, **k: ran.append(a))

    with pytest.raises(nvidia_driver.NvidiaDriverError, match="assinatura"):
        nvidia_driver.install_update(_update(), workdir=tmp_path)

    assert ran == []
    assert list(tmp_path.iterdir()) == []


def test_install_nonzero_exit_reports_failure_and_cleans_up(monkeypatch, tmp_path):
    monkeypatch.setattr(nvidia_driver, "_download", lambda url, dest: dest.write_bytes(b"x"))
    monkeypatch.setattr(nvidia_driver, "_verify_signature", lambda path: None)
    monkeypatch.setattr(nvidia_driver.subprocess, "run", lambda *a, **k: _Done(1))

    ok, reboot, note = nvidia_driver.install_update(_update(), workdir=tmp_path)

    assert ok is False
    assert "1" in note
    assert list(tmp_path.iterdir()) == []


def test_install_rejects_untrusted_url_before_downloading(monkeypatch, tmp_path):
    downloads = []
    monkeypatch.setattr(nvidia_driver, "_download", lambda url, dest: downloads.append(url))
    bad = nvidia_driver.NvidiaUpdate("g", "1.00", "2.00", "https://evil.example.com/x.exe")

    with pytest.raises(nvidia_driver.NvidiaDriverError):
        nvidia_driver.install_update(bad, workdir=tmp_path)

    assert downloads == []


def test_flicker_warning_tells_user_the_screen_may_flash():
    text = nvidia_driver.FLICKER_WARNING.lower()
    assert "tela" in text and "pisc" in text
