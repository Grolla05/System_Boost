import os
from pathlib import Path

def get_dir_size(path):
    """Calculates the total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
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

def _remove_and_measure(path):
    """Recursively deletes a directory tree, summing freed bytes in a single pass."""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file() or entry.is_symlink():
                    total += entry.stat().st_size
                    os.remove(entry.path)
                elif entry.is_dir():
                    total += _remove_and_measure(entry.path)
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

    if not path.exists():
        return 0

    try:
        entries = list(os.scandir(path))
        for entry in entries:
            try:
                if entry.is_file() or entry.is_symlink():
                    file_size = entry.stat().st_size
                    if not dry_run:
                        os.remove(entry.path)
                    bytes_freed += file_size
                elif entry.is_dir():
                    if dry_run:
                        bytes_freed += get_dir_size(entry.path)
                    else:
                        bytes_freed += _remove_and_measure(entry.path)
            except (PermissionError, OSError, FileNotFoundError):
                # Silently skip files/folders in use or already gone
                pass

            if progress_callback:
                progress_callback(1)
    except (PermissionError, OSError):
        pass

    return bytes_freed

def get_temp_paths():
    """Returns a list of standard Windows temporary directories."""
    paths = {
        "User Temp": os.environ.get("TEMP"),
        "System Temp": "C:\\Windows\\Temp",
        "Prefetch": "C:\\Windows\\Prefetch"
    }
    return {k: v for k, v in paths.items() if v and os.path.exists(v)}
