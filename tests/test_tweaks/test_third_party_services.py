import json

import pytest

from backend.tweaks import third_party_services as mod
from backend.tweaks.third_party_services import ThirdPartyServicesTweak


def _svc(name, command, start_type="auto"):
    return {"name": name, "display": name, "command": command, "start_type": start_type}


@pytest.fixture(autouse=True)
def _windows_root(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")


def test_metadata_requires_admin():
    tweak = ThirdPartyServicesTweak()
    assert tweak.id == "third_party_services"
    assert tweak.requires_admin is True


def test_get_current_value_keeps_only_third_party(monkeypatch):
    monkeypatch.setattr(mod, "discover_services", lambda: [
        _svc("MyUpdater", r'"C:\Program Files\MyApp\updater.exe" /svc'),
        _svc("Dhcp", r"C:\Windows\system32\svchost.exe -k LocalService"),
        _svc("AvastSvc", r"C:\Program Files\Avast Software\Avast\AvastSvc.exe"),
        _svc("MyDelayed", r"C:\Program Files\MyApp\d.exe", start_type="delayed-auto"),
    ])

    value = ThirdPartyServicesTweak().get_current_value()

    assert value == [
        {"name": "MyUpdater", "start_type": "auto"},
        {"name": "MyDelayed", "start_type": "delayed-auto"},
    ]
    json.dumps(value)


def test_apply_sets_demand_and_stops(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "discover_services", lambda: [_svc("MyUpdater", r"C:\MyApp\u.exe")])
    monkeypatch.setattr(mod, "set_start_type", lambda n, t: calls.append(("config", n, t)))
    monkeypatch.setattr(mod, "stop_service", lambda n: calls.append(("stop", n)))

    result = ThirdPartyServicesTweak().apply()

    assert calls == [("config", "MyUpdater", "demand"), ("stop", "MyUpdater")]
    assert result == [{"name": "MyUpdater"}]


def test_apply_failure_on_one_service_does_not_abort(monkeypatch):
    done = []

    def fake_config(name, start_type):
        if name == "A":
            raise OSError("denied")
        done.append(name)

    monkeypatch.setattr(mod, "discover_services", lambda: [_svc("A", r"C:\x\a.exe"), _svc("B", r"C:\x\b.exe")])
    monkeypatch.setattr(mod, "set_start_type", fake_config)
    monkeypatch.setattr(mod, "stop_service", lambda n: None)

    assert ThirdPartyServicesTweak().apply() == [{"name": "B"}]
    assert done == ["B"]


def test_undo_restores_start_type_and_restarts(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "set_start_type", lambda n, t: calls.append(("config", n, t)))
    monkeypatch.setattr(mod, "start_service", lambda n: calls.append(("start", n)))

    ThirdPartyServicesTweak().undo([{"name": "A", "start_type": "auto"}, {"name": "B", "start_type": "delayed-auto"}])

    assert calls == [
        ("config", "A", "auto"), ("start", "A"),
        ("config", "B", "delayed-auto"), ("start", "B"),
    ]


def test_set_start_type_uses_sc_config(monkeypatch, fake_run):
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    mod.set_start_type("Foo", "demand")

    assert fake_run.calls == [["sc", "config", "Foo", "start=", "demand"]]


def test_set_start_type_raises_on_failure(monkeypatch, fake_run):
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    fake_run.returncode = 5

    with pytest.raises(OSError):
        mod.set_start_type("Foo", "demand")
