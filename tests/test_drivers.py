import json

import pytest

from backend import drivers

GUID_A = "11111111-1111-1111-1111-111111111111"
GUID_B = "22222222-2222-2222-2222-222222222222"
GUID_C = "33333333-3333-3333-3333-333333333333"


class _Completed:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeRun:
    """Scripted subprocess.run: pops one response per call, records argv."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        return self.responses.pop(0)


def _json_bytes(obj):
    return json.dumps(obj).encode("utf-8")


def _scan_payload(*ids):
    return _json_bytes([
        {"title": f"Driver {i[0]}", "update_id": i, "manufacturer": "ACME", "model": "X", "size": 10}
        for i in ids
    ])


def _install_ok(reboot=False):
    return _Completed(0, _json_bytes({"result": 2, "reboot": reboot}))


def _install_fail():
    return _Completed(0, _json_bytes({"result": 4, "reboot": False}))


def _patch(monkeypatch, fake, admin=True):
    monkeypatch.setattr(drivers.subprocess, "run", fake)
    monkeypatch.setattr(drivers, "is_admin", lambda: admin)


# --- scan_drivers ---------------------------------------------------------

def test_scan_parses_json_list(monkeypatch):
    fake = FakeRun([_Completed(0, _scan_payload(GUID_A, GUID_B))])
    _patch(monkeypatch, fake)
    found = drivers.scan_drivers()
    assert [d["update_id"] for d in found] == [GUID_A, GUID_B]


def test_scan_single_object_is_wrapped_in_list(monkeypatch):
    one = _json_bytes({"title": "T", "update_id": GUID_A})
    _patch(monkeypatch, FakeRun([_Completed(0, one)]))
    assert len(drivers.scan_drivers()) == 1


def test_scan_empty_output_returns_empty_list(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"")]))
    assert drivers.scan_drivers() == []


def test_scan_handles_utf8_bom(monkeypatch):
    payload = b"\xef\xbb\xbf" + _scan_payload(GUID_A)
    _patch(monkeypatch, FakeRun([_Completed(0, payload)]))
    assert len(drivers.scan_drivers()) == 1


def test_scan_nonzero_returncode_raises(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(1, b"", b"boom")]))
    with pytest.raises(drivers.DriverError):
        drivers.scan_drivers()


def test_scan_invalid_json_raises(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"not json")]))
    with pytest.raises(drivers.DriverError):
        drivers.scan_drivers()


def test_scan_timeout_raises_driver_error(monkeypatch):
    def boom(cmd, **kwargs):
        raise drivers.subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(drivers.subprocess, "run", boom)
    with pytest.raises(drivers.DriverError):
        drivers.scan_drivers()


def test_scan_uses_argv_list_and_timeout(monkeypatch):
    fake = FakeRun([_Completed(0, b"[]")])
    _patch(monkeypatch, fake)
    drivers.scan_drivers()
    cmd, kwargs = fake.calls[0]
    assert isinstance(cmd, list) and cmd[0].lower().startswith("powershell")
    assert kwargs.get("capture_output") is True
    assert kwargs.get("timeout")


# --- install_driver -------------------------------------------------------

def test_install_success_reports_reboot(monkeypatch):
    _patch(monkeypatch, FakeRun([_install_ok(reboot=True)]))
    ok, reboot, _ = drivers.install_driver(GUID_A)
    assert ok is True and reboot is True


def test_install_failure_result_code(monkeypatch):
    _patch(monkeypatch, FakeRun([_install_fail()]))
    ok, reboot, note = drivers.install_driver(GUID_A)
    assert ok is False and note


def test_install_rejects_non_guid_id_without_running(monkeypatch):
    fake = FakeRun([])
    _patch(monkeypatch, fake)
    with pytest.raises(drivers.DriverError):
        drivers.install_driver("x'; Remove-Item C:\\ -Recurse; '")
    assert fake.calls == []


# --- update_all_drivers ---------------------------------------------------

def test_update_all_without_admin_is_skipped(monkeypatch):
    fake = FakeRun([])
    _patch(monkeypatch, fake, admin=False)
    results, reboot = drivers.update_all_drivers()
    assert len(results) == 1 and results[0][1] is None
    assert reboot is False
    assert fake.calls == []


def test_update_all_dry_run_never_installs(monkeypatch):
    fake = FakeRun([_Completed(0, _scan_payload(GUID_A, GUID_B))])
    _patch(monkeypatch, fake)
    results, reboot = drivers.update_all_drivers(dry_run=True)
    assert len(fake.calls) == 1  # scan only
    assert [r[1] for r in results] == [None, None]
    assert reboot is False


def test_update_all_one_failure_does_not_abort_rest(monkeypatch):
    fake = FakeRun([
        _Completed(0, _scan_payload(GUID_A, GUID_B, GUID_C)),
        _install_ok(),
        _install_fail(),
        _install_ok(),
    ])
    _patch(monkeypatch, fake)
    results, _ = drivers.update_all_drivers()
    assert [r[1] for r in results] == [True, False, True]


def test_update_all_exception_in_one_install_is_recorded(monkeypatch):
    fake = FakeRun([
        _Completed(0, _scan_payload(GUID_A, GUID_B)),
        _Completed(1, b"", b"err"),
        _install_ok(),
    ])
    _patch(monkeypatch, fake)
    results, _ = drivers.update_all_drivers()
    assert [r[1] for r in results] == [False, True]


def test_update_all_callbacks(monkeypatch):
    fake = FakeRun([
        _Completed(0, _scan_payload(GUID_A, GUID_B)),
        _install_ok(),
        _install_ok(),
    ])
    _patch(monkeypatch, fake)
    totals, titles = [], []
    drivers.update_all_drivers(on_scan=totals.append, progress_callback=titles.append)
    assert totals == [2]
    assert len(titles) == 2


def test_update_all_propagates_reboot_flag(monkeypatch):
    fake = FakeRun([
        _Completed(0, _scan_payload(GUID_A, GUID_B)),
        _install_ok(),
        _install_ok(reboot=True),
    ])
    _patch(monkeypatch, fake)
    _, reboot = drivers.update_all_drivers()
    assert reboot is True


def test_update_all_nothing_found(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    results, reboot = drivers.update_all_drivers()
    assert results == [] and reboot is False


def test_update_all_scan_error_becomes_failed_entry(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(1, b"", b"boom")]))
    results, _ = drivers.update_all_drivers()
    assert len(results) == 1 and results[0][1] is False


def test_powershell_does_not_inherit_console_stdin(monkeypatch):
    fake = FakeRun([_Completed(0, b"[]")])
    _patch(monkeypatch, fake)

    drivers.scan_drivers()

    assert fake.calls[0][1]["stdin"] is drivers.subprocess.DEVNULL
