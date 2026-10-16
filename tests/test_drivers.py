import json

import pytest

from backend import drivers, nvidia_driver

GUID_A = "11111111-1111-1111-1111-111111111111"
GUID_B = "22222222-2222-2222-2222-222222222222"
GUID_C = "33333333-3333-3333-3333-333333333333"


@pytest.fixture(autouse=True)
def _no_nvidia(monkeypatch):
    """By default the machine has no NVIDIA update; real GPU detection must never run in tests."""
    monkeypatch.setattr(drivers.nvidia_driver, "check_update", lambda: None)


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


def test_update_all_on_result_reports_each_driver(monkeypatch):
    fake = FakeRun([
        _Completed(0, _scan_payload(GUID_A, GUID_B)),
        _install_ok(),
        _install_fail(),
    ])
    _patch(monkeypatch, fake)
    events = []

    drivers.update_all_drivers(on_result=lambda title, status, note: events.append((title, status)))

    assert events == [("Driver 1", True), ("Driver 2", False)]


def test_update_all_on_result_reports_exceptions_as_failure(monkeypatch):
    fake = FakeRun([_Completed(0, _scan_payload(GUID_A)), _Completed(1, b"", b"err")])
    _patch(monkeypatch, fake)
    events = []

    drivers.update_all_drivers(on_result=lambda title, status, note: events.append(status))

    assert events == [False]


def test_update_all_on_result_dry_run_reports_skip(monkeypatch):
    fake = FakeRun([_Completed(0, _scan_payload(GUID_A))])
    _patch(monkeypatch, fake)
    events = []

    drivers.update_all_drivers(dry_run=True, on_result=lambda title, status, note: events.append((status, note)))

    assert events == [(None, "dry-run")]


# --- NVIDIA ---------------------------------------------------------------

NV_UPDATE = nvidia_driver.NvidiaUpdate("NVIDIA GeForce RTX 4070", "551.23", "617.42", "https://us.download.nvidia.com/x.exe")


def _with_nvidia(monkeypatch, update=NV_UPDATE, install=None):
    monkeypatch.setattr(drivers.nvidia_driver, "check_update", lambda: update)
    installed = []

    def fake_install(u):
        installed.append(u)
        return install() if install else (True, False, "instalado")

    monkeypatch.setattr(drivers.nvidia_driver, "install_update", fake_install)
    return installed


def test_update_all_installs_nvidia_after_windows_update(monkeypatch):
    fake = FakeRun([_Completed(0, _scan_payload(GUID_A)), _install_ok()])
    _patch(monkeypatch, fake)
    installed = _with_nvidia(monkeypatch)

    results, _ = drivers.update_all_drivers()

    assert [r[0] for r in results] == ["Driver 1", NV_UPDATE.title]
    assert [r[1] for r in results] == [True, True]
    assert installed == [NV_UPDATE]


def test_update_all_nvidia_counts_in_on_scan_total(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, _scan_payload(GUID_A)), _install_ok()]))
    _with_nvidia(monkeypatch)
    totals = []

    drivers.update_all_drivers(on_scan=totals.append)

    assert totals == [2]


def test_update_all_nvidia_alone_when_windows_update_has_nothing(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    _with_nvidia(monkeypatch)

    results, _ = drivers.update_all_drivers()

    assert [r[1] for r in results] == [True]


def test_update_all_nvidia_dry_run_does_not_download(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    installed = _with_nvidia(monkeypatch)

    results, _ = drivers.update_all_drivers(dry_run=True)

    assert installed == []
    assert [(r[0], r[1], r[2]) for r in results] == [(NV_UPDATE.title, None, "dry-run")]


def test_update_all_warns_about_screen_flicker_before_installing_nvidia(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    order = []
    _with_nvidia(monkeypatch, install=lambda: (order.append("install"), (True, False, "ok"))[1])
    notices = []

    def on_notice(message):
        order.append("notice")
        notices.append(message)

    drivers.update_all_drivers(on_notice=on_notice)

    assert notices == [nvidia_driver.FLICKER_WARNING]
    assert order == ["notice", "install"]


def test_update_all_no_flicker_warning_without_nvidia_update_or_in_dry_run(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    notices = []
    drivers.update_all_drivers(on_notice=notices.append)
    assert notices == []

    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    _with_nvidia(monkeypatch)
    drivers.update_all_drivers(dry_run=True, on_notice=notices.append)
    assert notices == []


def test_update_all_nvidia_failure_does_not_abort_and_is_recorded(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, _scan_payload(GUID_A)), _install_ok()]))

    def boom():
        raise nvidia_driver.NvidiaDriverError("assinatura inválida")

    _with_nvidia(monkeypatch, install=boom)

    results, _ = drivers.update_all_drivers()

    assert [r[1] for r in results] == [True, False]
    assert "assinatura" in results[1][2]


def test_update_all_nvidia_lookup_error_becomes_skipped_entry(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))

    def boom():
        raise nvidia_driver.NvidiaDriverError("não foi possível consultar a NVIDIA")

    monkeypatch.setattr(drivers.nvidia_driver, "check_update", boom)

    results, _ = drivers.update_all_drivers()

    assert len(results) == 1 and results[0][1] is None
    assert "NVIDIA" in results[0][0] and "consultar" in results[0][2]


def test_update_all_nvidia_runs_even_if_windows_update_scan_fails(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(1, b"", b"boom")]))
    installed = _with_nvidia(monkeypatch)

    results, _ = drivers.update_all_drivers()

    assert [r[1] for r in results] == [False, True]
    assert installed == [NV_UPDATE]


def test_update_all_nvidia_propagates_reboot_and_callbacks(monkeypatch):
    _patch(monkeypatch, FakeRun([_Completed(0, b"[]")]))
    _with_nvidia(monkeypatch, install=lambda: (True, True, "reinicie para concluir"))
    titles, events = [], []

    _, reboot = drivers.update_all_drivers(
        progress_callback=titles.append, on_result=lambda t, s, n: events.append((t, s)))

    assert reboot is True
    assert titles == [NV_UPDATE.title] and events == [(NV_UPDATE.title, True)]


def test_update_all_nvidia_skipped_without_admin(monkeypatch):
    _patch(monkeypatch, FakeRun([]), admin=False)
    installed = _with_nvidia(monkeypatch)

    results, _ = drivers.update_all_drivers()

    assert len(results) == 1 and results[0][1] is None
    assert installed == []
