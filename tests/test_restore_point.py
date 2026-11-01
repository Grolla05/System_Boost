from backend import restore_point
from backend._powershell import PowerShellError


def test_requires_admin(monkeypatch):
    monkeypatch.setattr(restore_point, "is_admin", lambda: False)
    monkeypatch.setattr(restore_point, "run_powershell", lambda *a: 1 / 0)

    assert restore_point.create_restore_point() == (False, "requer administrador")


def test_success(monkeypatch):
    scripts = []
    monkeypatch.setattr(restore_point, "is_admin", lambda: True)
    monkeypatch.setattr(restore_point, "run_powershell", lambda script, timeout: scripts.append(script) or "")

    ok, _ = restore_point.create_restore_point()

    assert ok is True
    assert "Checkpoint-Computer" in scripts[0]


def test_failure_is_returned_not_raised(monkeypatch):
    def fail(script, timeout):
        raise PowerShellError("desligada")

    monkeypatch.setattr(restore_point, "is_admin", lambda: True)
    monkeypatch.setattr(restore_point, "run_powershell", fail)

    ok, note = restore_point.create_restore_point()

    assert ok is False
    assert "Proteção do Sistema" in note
