import os
import shutil
import subprocess
import sys
from pathlib import Path

from ._powershell import PowerShellError, run_powershell
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

ADMIN_ONLY_PATHS = frozenset({"System Temp", "Prefetch"})


def get_temp_paths():
    """Returns a dict of standard Windows temporary/cache directories that exist."""
    local = os.environ.get("LOCALAPPDATA")
    home = os.path.expanduser("~")
    paths = {
        "User Temp": os.environ.get("TEMP"),
        "System Temp": "C:\\Windows\\Temp",
        "Prefetch": "C:\\Windows\\Prefetch",
        "SquirrelTemp": os.path.join(local, "SquirrelTemp") if local else None,
        # Only caches: ~/.gradle also holds gradle.properties (credentials/config)
        "Gradle Cache": os.path.join(home, ".gradle", "caches"),
        "Go Build Cache": os.path.join(local, "go-build") if local else None,
        "User Cache": os.path.join(home, ".cache"),
    }
    return {k: v for k, v in paths.items() if v and os.path.exists(v)}


# --- Command-based cleanups (tool's own cache clean; nothing is moved) ---

def _run_command(argv, timeout=300):
    """Runs a tool command; returns (ok, detail). Never raises."""
    try:
        result = subprocess.run(
            argv, capture_output=True, check=False, timeout=timeout, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode != 0:
        detail = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        return False, detail[:200] or f"código {result.returncode}"
    return True, (result.stdout or b"").decode("utf-8", errors="replace").strip()


def _tool_cache_dir(argv):
    """Asks a tool for its cache directory (e.g. `npm config get cache`)."""
    ok, out = _run_command(argv, timeout=30)
    path = out.splitlines()[-1].strip() if ok and out else ""
    return path if path and os.path.isdir(path) else None


def _recycle_bin_size():
    try:
        out = run_powershell(
            "(New-Object -ComObject Shell.Application).NameSpace(0xA).Items() | "
            "ForEach-Object { $_.ExtendedProperty('Size') } | Measure-Object -Sum | "
            "ForEach-Object { [int64]$_.Sum }", 60)
        return int(out or 0)
    except (PowerShellError, ValueError):
        return 0


def _empty_recycle_bin():
    try:
        run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue", 120)
        return True, ""
    except PowerShellError as exc:
        return False, str(exc)


# id -> (label, executable or None, size-measuring fn, clean fn)
COMMAND_CLEANUPS = {
    "npm-cache": (
        "npm cache", "npm",
        lambda: get_dir_size(d) if (d := _tool_cache_dir(["npm", "config", "get", "cache"])) else 0,
        lambda: _run_command(["npm", "cache", "clean", "--force"]),
    ),
    "uv-cache": (
        "uv cache", "uv",
        lambda: get_dir_size(d) if (d := _tool_cache_dir(["uv", "cache", "dir"])) else 0,
        lambda: _run_command(["uv", "cache", "clean"]),
    ),
    "recycle-bin": ("Lixeira", None, _recycle_bin_size, _empty_recycle_bin),
}


def run_command_cleanup(cleanup_id, dry_run=False):
    """Runs one command cleanup. Returns (status, bytes_freed): status is 'ok', 'skip' (tool not
    installed) or 'fail'. dry_run only measures."""
    label, executable, measure, clean = COMMAND_CLEANUPS[cleanup_id]
    if executable and shutil.which(executable) is None:
        log.info("limpeza '%s': %s não instalado, ignorada", cleanup_id, executable)
        return "skip", 0
    before = measure()
    if dry_run:
        log.info("limpeza '%s': dry-run, %d bytes seriam liberados", cleanup_id, before)
        return "ok", before
    ok, detail = clean()
    if not ok:
        log.warning("limpeza '%s': falhou: %s", cleanup_id, detail)
        return "fail", 0
    freed = max(before - measure(), 0)
    log.info("limpeza '%s': concluída, %d bytes liberados", cleanup_id, freed)
    return "ok", freed
