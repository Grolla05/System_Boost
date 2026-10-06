import os
import sys
from pathlib import Path

from .logger import get_logger

log = get_logger("cleaner")


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def _protected_paths():
    """Paths the cleaner must never touch: the PyInstaller onefile extraction dir (sys._MEIPASS)
    holds this running program's own runtime (base_library.zip, lazy-imported modules)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass:
        return {_norm(meipass)}
    return set()


def get_dir_size(path, protected=frozenset()):
    """Calculates the total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                if _norm(entry.path) in protected:
                    continue
                total += get_dir_size(entry.path, protected)
    except (PermissionError, FileNotFoundError):
        pass
    return total

def format_size(size_bytes):
    """Formats bytes into a human-readable string (MB, GB)."""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

def _remove_and_measure(path, protected=frozenset()):
    """Recursively deletes a directory tree, summing freed bytes in a single pass."""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file() or entry.is_symlink():
                    total += entry.stat().st_size
                    os.remove(entry.path)
                elif entry.is_dir():
                    if _norm(entry.path) in protected:
                        continue
                    total += _remove_and_measure(entry.path, protected)
            except (PermissionError, OSError, FileNotFoundError):
                pass
    except (PermissionError, FileNotFoundError):
        pass
    try:
        os.rmdir(path)
    except OSError:
        pass
    return total


def clean_directory(directory_path, progress_callback=None, dry_run=False):
    """
    Safely deletes all files and subdirectories within a directory.
    Ignores files that are currently in use. When dry_run is True, only
    measures what would be freed without deleting anything.
    """
    path = Path(directory_path)
    bytes_freed = 0
    protected = _protected_paths()

    if not path.exists():
        log.info("limpeza '%s': pasta inexistente, ignorada", path)
        return 0

    log.info("limpeza '%s': iniciando (dry_run=%s)", path, dry_run)
    skipped = 0
    try:
        entries = list(os.scandir(path))
        log.debug("limpeza '%s': %d entradas encontradas", path, len(entries))
        for entry in entries:
            try:
                if entry.is_file() or entry.is_symlink():
                    file_size = entry.stat().st_size
                    if not dry_run:
                        os.remove(entry.path)
                    bytes_freed += file_size
                elif entry.is_dir():
                    if _norm(entry.path) in protected:
                        pass
                    elif dry_run:
                        bytes_freed += get_dir_size(entry.path, protected)
                    else:
                        bytes_freed += _remove_and_measure(entry.path, protected)
            except (PermissionError, OSError, FileNotFoundError) as exc:
                # Skip files/folders in use or already gone (logged, never surfaced)
                skipped += 1
                log.debug("limpeza: ignorado '%s': %s", entry.path, exc)

            if progress_callback:
                progress_callback(1)
    except (PermissionError, OSError) as exc:
        log.warning("limpeza '%s': não foi possível listar a pasta: %s", path, exc)

    log.info("limpeza '%s': concluída, %d bytes liberados, %d entradas ignoradas", path, bytes_freed, skipped)
    return bytes_freed

def get_temp_paths():
    """Returns a list of standard Windows temporary directories."""
    paths = {
        "User Temp": os.environ.get("TEMP"),
        "System Temp": "C:\\Windows\\Temp",
        "Prefetch": "C:\\Windows\\Prefetch"
    }
    return {k: v for k, v in paths.items() if v and os.path.exists(v)}
