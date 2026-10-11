import json

from backend.tweaks import startup_apps
from backend.tweaks.startup_apps import StartupAppsTweak


def _entry(scope, name, previous=None):
    return {"scope": scope, "name": name, "previous": previous}


def _raw(scope, name, command, enabled=True, previous=None):
    return {"scope": scope, "name": name, "command": command, "enabled": enabled, "previous": previous}


def test_metadata_and_no_admin_requirement():
    tweak = StartupAppsTweak()
    assert tweak.id == "startup_apps"
    assert tweak.label
    assert tweak.requires_admin is False


def test_get_current_value_lists_only_enabled_third_party_entries(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setattr(startup_apps, "discover_entries", lambda: [
        _raw("hkcu_run", "Spotify", r"C:\Users\x\Spotify.exe"),
        _raw("hkcu_run", "OneDrive", r"C:\Users\x\AppData\Local\Microsoft\OneDrive\OneDrive.exe"),
        _raw("hkcu_run", "Already", r"C:\Apps\a.exe", enabled=False, previous="030000000000000000000000"),
    ])

    assert StartupAppsTweak().get_current_value() == [_entry("hkcu_run", "Spotify")]


def test_value_is_json_serializable(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setattr(startup_apps, "discover_entries", lambda: [
        _raw("user_folder", "x.lnk", r"C:\Apps\x.exe", previous="020000000000000000000000"),
    ])

    json.dumps(StartupAppsTweak().get_current_value())


def test_apply_disables_each_candidate_and_returns_changed(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    writes = []
    monkeypatch.setattr(startup_apps, "discover_entries", lambda: [
        _raw("hkcu_run", "A", r"C:\Apps\a.exe"),
        _raw("hklm_run", "B", r"C:\Apps\b.exe"),
    ])
    monkeypatch.setattr(startup_apps, "write_approved", lambda scope, name, data: writes.append((scope, name, data)))

    result = StartupAppsTweak().apply()

    assert [(s, n) for s, n, _ in writes] == [("hkcu_run", "A"), ("hklm_run", "B")]
    assert all(d[0] == 3 for _, _, d in writes)  # first byte 03 = disabled
    assert result == [{"scope": "hkcu_run", "name": "A"}, {"scope": "hklm_run", "name": "B"}]


def test_apply_one_failure_does_not_abort_others(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    writes = []

    def fake_write(scope, name, data):
        if name == "A":
            raise OSError("denied")
        writes.append(name)

    monkeypatch.setattr(startup_apps, "discover_entries", lambda: [
        _raw("hkcu_run", "A", r"C:\Apps\a.exe"),
        _raw("hkcu_run", "B", r"C:\Apps\b.exe"),
    ])
    monkeypatch.setattr(startup_apps, "write_approved", fake_write)

    result = StartupAppsTweak().apply()

    assert writes == ["B"]
    assert result == [{"scope": "hkcu_run", "name": "B"}]


def test_undo_restores_previous_bytes_or_removes_value(monkeypatch):
    writes = []
    monkeypatch.setattr(startup_apps, "write_approved", lambda scope, name, data: writes.append((scope, name, data)))
    previous = [_entry("hkcu_run", "A", "020000000000000000000000"), _entry("hkcu_run", "B", None)]

    StartupAppsTweak().undo(previous)

    assert writes == [
        ("hkcu_run", "A", bytes.fromhex("020000000000000000000000")),
        ("hkcu_run", "B", None),
    ]


def test_undo_failure_does_not_abort_others(monkeypatch):
    writes = []

    def fake_write(scope, name, data):
        if name == "A":
            raise OSError("x")
        writes.append(name)

    monkeypatch.setattr(startup_apps, "write_approved", fake_write)

    StartupAppsTweak().undo([_entry("hkcu_run", "A"), _entry("hkcu_run", "B")])

    assert writes == ["B"]
