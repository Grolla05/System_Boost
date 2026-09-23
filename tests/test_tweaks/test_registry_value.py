import pytest

from backend.tweaks.registry_value import RegistryValueTweak
from backend.tweaks.base import TweakError


def _make_tweak(fake_winreg, requires_admin=False):
    return RegistryValueTweak(
        tweak_id="visual_effects",
        label="Efeitos visuais: melhor desempenho",
        description="Ajusta os efeitos visuais do Windows para melhor desempenho.",
        hive=fake_winreg.HKEY_CURRENT_USER,
        key_path="Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects",
        value_name="VisualFXSetting",
        target_value=2,
        requires_admin=requires_admin,
    )


def test_get_current_value_returns_none_when_key_missing(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)

    assert tweak.get_current_value() is None


def test_get_current_value_returns_none_when_value_missing(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)
    fake_winreg.seed(tweak.hive, tweak.key_path, "SomeOtherValue", 1)

    assert tweak.get_current_value() is None


def test_get_current_value_returns_existing_value(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)
    fake_winreg.seed(tweak.hive, tweak.key_path, "VisualFXSetting", 0)

    assert tweak.get_current_value() == 0


def test_apply_creates_key_and_writes_target_value(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)

    result = tweak.apply()

    assert result == 2
    assert tweak.get_current_value() == 2


def test_undo_restores_previous_int_value(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)
    tweak.apply()

    tweak.undo(0)

    assert tweak.get_current_value() == 0


def test_undo_deletes_value_when_previous_value_was_none(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)
    tweak.apply()
    assert fake_winreg.has_value(tweak.hive, tweak.key_path, "VisualFXSetting")

    tweak.undo(None)

    assert not fake_winreg.has_value(tweak.hive, tweak.key_path, "VisualFXSetting")
    assert tweak.get_current_value() is None


def test_undo_with_none_is_a_noop_when_value_already_absent(monkeypatch, fake_winreg):
    import backend.tweaks.registry_value as module
    monkeypatch.setattr(module, "winreg", fake_winreg)
    tweak = _make_tweak(fake_winreg)

    tweak.undo(None)  # must not raise

    assert tweak.get_current_value() is None
