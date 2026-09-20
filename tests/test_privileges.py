import ctypes
import types

from backend.privileges import is_admin


def _fake_windll(is_admin_result):
    shell32 = types.SimpleNamespace(IsUserAnAdmin=lambda: is_admin_result)
    return types.SimpleNamespace(shell32=shell32)


def test_is_admin_true_when_windows_api_reports_admin(monkeypatch):
    monkeypatch.setattr(ctypes, "windll", _fake_windll(1), raising=False)

    assert is_admin() is True


def test_is_admin_false_when_windows_api_reports_non_admin(monkeypatch):
    monkeypatch.setattr(ctypes, "windll", _fake_windll(0), raising=False)

    assert is_admin() is False


def test_is_admin_falls_back_to_getuid_when_windll_unavailable(monkeypatch):
    monkeypatch.delattr(ctypes, "windll", raising=False)
    monkeypatch.setattr("os.getuid", lambda: 0, raising=False)

    assert is_admin() is True
