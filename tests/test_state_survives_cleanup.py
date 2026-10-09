"""The undo data (tweaks_state.json) and UI config must never live in a folder the cleaner empties.

The cleaner wipes %TEMP%, C:\\Windows\\Temp and C:\\Windows\\Prefetch. If the state file ever ended
up inside one of them, running any cleanup would silently destroy the only record of the original
values, and "desfazer ajustes" would have nothing to restore.
"""
import os
from pathlib import Path

from backend import cleaner
from backend.tweaks import manager, state_store
from frontend import palettes


def _is_inside(path, folder):
    path = os.path.normcase(os.path.realpath(path))
    folder = os.path.normcase(os.path.realpath(folder))
    try:
        return os.path.commonpath([path, folder]) == folder
    except ValueError:  # different drives
        return False


def _windows_like_env(monkeypatch, tmp_path):
    """Mimics a real Windows profile: %TEMP% is a *sibling* of the app-data folder, not its parent."""
    local = tmp_path / "AppData" / "Local"
    temp = local / "Temp"
    temp.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    monkeypatch.setenv("TEMP", str(temp))
    return local, temp


def test_real_state_file_path_is_outside_every_cleaned_folder():
    state_path = state_store._default_state_path()

    for name, folder in cleaner.get_temp_paths().items():
        assert not _is_inside(state_path, folder), f"state file would be wiped by cleaning '{name}'"


def test_real_ui_config_path_is_outside_every_cleaned_folder():
    for name, folder in cleaner.get_temp_paths().items():
        assert not _is_inside(palettes.CONFIG_PATH, folder), f"ui_config.json would be wiped by cleaning '{name}'"


def test_state_file_is_outside_user_temp_in_a_windows_like_profile(monkeypatch, tmp_path):
    local, temp = _windows_like_env(monkeypatch, tmp_path)

    state_path = state_store._default_state_path()

    assert Path(state_path) == local / "WinCleaner" / "tweaks_state.json"
    assert not _is_inside(state_path, temp)


def test_cleaning_user_temp_keeps_the_state_file_and_other_app_data(monkeypatch, tmp_path):
    local, temp = _windows_like_env(monkeypatch, tmp_path)
    (temp / "junk.tmp").write_bytes(b"x" * 100)
    (temp / "sub").mkdir()
    (temp / "sub" / "more.tmp").write_bytes(b"y" * 50)
    state_store.save_applied("visual_effects", None, 2, False)
    config = local / "WinCleaner" / "ui_config.json"
    config.write_text('{"palette": "dmg"}', encoding="utf-8")

    freed = cleaner.clean_directory(cleaner.get_temp_paths()["User Temp"])

    assert freed >= 150
    assert not (temp / "junk.tmp").exists()
    assert not (temp / "sub").exists()
    assert (local / "WinCleaner" / "tweaks_state.json").exists()
    assert config.exists()


def test_applied_tweaks_can_still_be_listed_for_undo_after_a_cleanup(monkeypatch, tmp_path):
    """The user's scenario: apply tweaks, run a cleanup, then open 'desfazer ajustes'."""
    _windows_like_env(monkeypatch, tmp_path)
    state_store.save_applied("visual_effects", None, 2, False)
    state_store.save_applied("power_plan", "381b4222-f694-41f0-9685-ff5bb260df2e", "8c5e7fda", False)

    cleaner.clean_directory(cleaner.get_temp_paths()["User Temp"])
    applied = manager.list_applied()

    assert [tweak.id for tweak, _ in applied] == ["power_plan", "visual_effects"]
    assert applied[0][1]["previous_value"] == "381b4222-f694-41f0-9685-ff5bb260df2e"
    assert applied[1][1]["previous_value"] is None  # "value didn't exist" survives too


def test_repeated_cleanups_do_not_erode_the_state(monkeypatch, tmp_path):
    local, temp = _windows_like_env(monkeypatch, tmp_path)
    state_store.save_applied("visual_effects", None, 2, False)

    for _ in range(3):
        (temp / "again.tmp").write_bytes(b"z")
        cleaner.clean_directory(cleaner.get_temp_paths()["User Temp"])

    assert state_store.get_applied("visual_effects") is not None
