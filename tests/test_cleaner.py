import os
import subprocess
import time

import pytest

from backend import cleaner

from backend.cleaner import (
    clean_directory,
    format_size,
    get_dir_size,
    get_temp_paths,
)


def _make_file(path, size_bytes):
    path.write_bytes(b"x" * size_bytes)


def test_get_dir_size_flat_files(tmp_path):
    _make_file(tmp_path / "a.txt", 100)
    _make_file(tmp_path / "b.txt", 250)

    assert get_dir_size(tmp_path) == 350


def test_get_dir_size_nested(tmp_path):
    _make_file(tmp_path / "a.txt", 100)
    nested = tmp_path / "sub"
    nested.mkdir()
    _make_file(nested / "b.txt", 50)
    deeper = nested / "deeper"
    deeper.mkdir()
    _make_file(deeper / "c.txt", 25)

    assert get_dir_size(tmp_path) == 175


def test_get_dir_size_missing_path_returns_zero(tmp_path):
    assert get_dir_size(tmp_path / "does-not-exist") == 0


def test_clean_directory_deletes_and_reports_size(tmp_path):
    _make_file(tmp_path / "a.txt", 100)
    nested = tmp_path / "sub"
    nested.mkdir()
    _make_file(nested / "b.txt", 50)

    freed = clean_directory(tmp_path)

    assert freed == 150
    assert list(tmp_path.iterdir()) == []
    assert tmp_path.exists()


def test_clean_directory_dry_run_does_not_delete(tmp_path):
    _make_file(tmp_path / "a.txt", 100)
    nested = tmp_path / "sub"
    nested.mkdir()
    _make_file(nested / "b.txt", 50)

    freed = clean_directory(tmp_path, dry_run=True)

    assert freed == 150
    assert (tmp_path / "a.txt").exists()
    assert (nested / "b.txt").exists()


def test_clean_directory_nonexistent_path_returns_zero(tmp_path):
    assert clean_directory(tmp_path / "does-not-exist") == 0


def test_clean_directory_handles_permission_error(tmp_path, monkeypatch):
    _make_file(tmp_path / "a.txt", 100)
    _make_file(tmp_path / "b.txt", 50)

    real_remove = os.remove

    def flaky_remove(path):
        if str(path).endswith("a.txt"):
            raise PermissionError("locked")
        return real_remove(path)

    monkeypatch.setattr(os, "remove", flaky_remove)

    freed = clean_directory(tmp_path)

    # "a.txt" failed to delete (skipped), "b.txt" succeeded.
    assert freed == 50
    assert (tmp_path / "a.txt").exists()
    assert not (tmp_path / "b.txt").exists()


def test_clean_directory_progress_callback_called_per_entry(tmp_path):
    _make_file(tmp_path / "a.txt", 10)
    _make_file(tmp_path / "b.txt", 10)

    calls = []
    clean_directory(tmp_path, progress_callback=calls.append)

    assert calls == [1, 1]


def test_format_size():
    assert format_size(0) == "0 B"
    assert format_size(1023) == "1023.00 B"
    assert format_size(1024) == "1.00 KB"
    assert format_size(1536) == "1.50 KB"
    assert format_size(1024 ** 3) == "1.00 GB"


def test_get_temp_paths_filters_nonexistent(monkeypatch, tmp_path):
    existing = tmp_path / "exists"
    existing.mkdir()

    monkeypatch.setenv("TEMP", str(existing))
    monkeypatch.setattr(
        "backend.cleaner.os.path.exists",
        lambda p: p == str(existing),
    )

    paths = get_temp_paths()

    assert paths == {"User Temp": str(existing)}


# --- PyInstaller onefile: never delete our own extraction dir ----------------

def _frozen_tree(tmp_path, monkeypatch):
    import sys
    mei = tmp_path / "_MEI123"
    mei.mkdir()
    (mei / "base_library.zip").write_bytes(b"x" * 100)
    other = tmp_path / "outro"
    other.mkdir()
    (other / "arquivo.tmp").write_bytes(b"y" * 10)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(mei), raising=False)
    return mei, other


def test_clean_directory_keeps_own_meipass(tmp_path, monkeypatch):
    mei, other = _frozen_tree(tmp_path, monkeypatch)

    freed = clean_directory(tmp_path)

    assert (mei / "base_library.zip").exists()
    assert not other.exists()
    assert freed == 10


def test_clean_directory_dry_run_ignores_own_meipass(tmp_path, monkeypatch):
    mei, other = _frozen_tree(tmp_path, monkeypatch)

    assert clean_directory(tmp_path, dry_run=True) == 10


def test_clean_directory_not_frozen_still_removes_mei_dirs(tmp_path, monkeypatch):
    import sys
    mei = tmp_path / "_MEI123"
    mei.mkdir()
    (mei / "f").write_bytes(b"z")
    monkeypatch.delattr(sys, "frozen", raising=False)

    clean_directory(tmp_path)

    assert not mei.exists()


def test_clean_directory_progress_counts_protected_entry(tmp_path, monkeypatch):
    _frozen_tree(tmp_path, monkeypatch)
    ticks = []

    clean_directory(tmp_path, progress_callback=ticks.append)

    assert len(ticks) == 2


# --- command cleanups ---

def _fake_cleanup(monkeypatch, measure, clean, executable="npm"):
    monkeypatch.setitem(cleaner.COMMAND_CLEANUPS, "fake", ("Fake", executable, measure, clean))


def test_command_cleanup_skips_when_tool_missing(monkeypatch):
    called = []
    _fake_cleanup(monkeypatch, lambda: 10, lambda: called.append(1) or (True, ""))
    monkeypatch.setattr(cleaner.shutil, "which", lambda name: None)
    assert cleaner.run_command_cleanup("fake") == ("skip", 0)
    assert not called


def test_command_cleanup_reports_measured_delta(monkeypatch):
    sizes = iter([100, 30])
    _fake_cleanup(monkeypatch, lambda: next(sizes), lambda: (True, ""))
    monkeypatch.setattr(cleaner.shutil, "which", lambda name: "npm")
    assert cleaner.run_command_cleanup("fake") == ("ok", 70)


def test_command_cleanup_dry_run_does_not_clean(monkeypatch):
    called = []
    _fake_cleanup(monkeypatch, lambda: 55, lambda: called.append(1) or (True, ""))
    monkeypatch.setattr(cleaner.shutil, "which", lambda name: "npm")
    assert cleaner.run_command_cleanup("fake", dry_run=True) == ("ok", 55)
    assert not called


def test_command_cleanup_failure_is_reported_not_raised(monkeypatch):
    _fake_cleanup(monkeypatch, lambda: 5, lambda: (False, "boom"), executable=None)
    assert cleaner.run_command_cleanup("fake") == ("fail", 0)


def test_command_cleanups_never_run_the_tool(monkeypatch, tmp_path):
    cache = tmp_path / "npm-cache"
    cache.mkdir()
    (cache / "index").write_bytes(b"x" * 40)
    monkeypatch.setenv("NPM_CONFIG_CACHE", str(cache))
    monkeypatch.setattr(cleaner.shutil, "which", lambda name: "npm.cmd")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("não deve executar nada"))

    assert cleaner.run_command_cleanup("npm-cache") == ("ok", 40)
    assert not (cache / "index").exists()


def test_uv_cache_defaults_to_local_app_data(monkeypatch, tmp_path):
    monkeypatch.delenv("UV_CACHE_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert cleaner._uv_cache() == os.path.join(str(tmp_path), "uv", "cache")


# --- links: only the link goes, never its target ---

@pytest.fixture
def junction(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep me")
    temp = tmp_path / "temp"
    temp.mkdir()
    link = temp / "link"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, check=True)
    return temp, link, outside


def test_clean_directory_removes_junction_but_not_its_target(junction):
    temp, link, outside = junction

    assert clean_directory(temp) == 0

    assert not os.path.lexists(link)
    assert (outside / "precious.txt").exists()


def test_clean_directory_keeps_target_of_nested_junction(junction):
    temp, link, outside = junction
    nested = temp / "sub"
    nested.mkdir()
    os.replace(link, nested / "link")

    clean_directory(temp)

    assert not nested.exists()
    assert (outside / "precious.txt").exists()


def test_dry_run_and_sizes_skip_junctions(junction):
    temp, link, outside = junction

    assert clean_directory(temp, dry_run=True) == 0
    assert get_dir_size(temp) == 0
    assert os.path.lexists(link)


# --- age and root rules ---

def _age(path, seconds=None):
    old = time.time() - (seconds or 3 * 24 * 3600)
    os.utime(path, (old, old))


def test_min_age_keeps_recent_files_only(tmp_path, monkeypatch):
    _make_file(tmp_path / "old.tmp", 10)
    _make_file(tmp_path / "new.tmp", 20)
    _age(tmp_path / "old.tmp")
    monkeypatch.setattr(cleaner, "_is_recent", lambda info, cutoff: info.st_size == 20)

    assert clean_directory(tmp_path, min_age_seconds=3600) == 10

    assert not (tmp_path / "old.tmp").exists()
    assert (tmp_path / "new.tmp").exists()


def test_recent_file_keeps_its_folder(tmp_path):
    sub = tmp_path / "app"
    sub.mkdir()
    _make_file(sub / "lock", 5)

    assert clean_directory(tmp_path, min_age_seconds=3600) == 0

    assert (sub / "lock").exists()


def test_dry_run_matches_min_age(tmp_path):
    _make_file(tmp_path / "new.tmp", 20)

    assert clean_directory(tmp_path, dry_run=True, min_age_seconds=3600) == 0


def test_keep_names_survive(tmp_path):
    keep = tmp_path / "HuggingFace"
    keep.mkdir()
    _make_file(keep / "model.bin", 5)
    _make_file(tmp_path / "other", 5)

    assert clean_directory(tmp_path, keep_names=("huggingface",)) == 5

    assert (keep / "model.bin").exists()


def test_temp_rules_are_declared():
    assert cleaner.CLEAN_RULES["User Temp"]["min_age_seconds"] == 86400
    assert cleaner.CLEAN_RULES["System Temp"]["min_age_seconds"] == 86400
    assert "huggingface" in cleaner.CLEAN_RULES["User Cache"]["keep_names"]


@pytest.mark.parametrize("env_var", ["USERPROFILE", "LOCALAPPDATA", "ProgramFiles"])
def test_unsafe_roots_are_refused(tmp_path, monkeypatch, env_var):
    monkeypatch.setenv(env_var, str(tmp_path))
    _make_file(tmp_path / "a.txt", 10)

    assert not cleaner.is_safe_clean_root(str(tmp_path))
    assert clean_directory(tmp_path) == 0
    assert (tmp_path / "a.txt").exists()


def test_parent_of_a_sensitive_folder_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData" / "Roaming"))
    assert not cleaner.is_safe_clean_root(str(tmp_path))


@pytest.mark.parametrize("path", ["C:\\", "C:\\Windows", "C:\\Windows\\System32\\..", "relative\\temp"])
def test_system_roots_are_refused(path):
    assert not cleaner.is_safe_clean_root(path)


def test_windows_temp_is_allowed():
    assert cleaner.is_safe_clean_root("C:\\Windows\\Temp")
