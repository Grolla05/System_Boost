import os

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
