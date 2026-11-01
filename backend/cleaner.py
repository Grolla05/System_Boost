import os
import shutil
import stat
import sys
import time
from pathlib import Path

from ._powershell import PowerShellError, run_powershell
from .logger import get_logger

log = get_logger("cleaner")

_IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003  # junction
_IO_REPARSE_TAG_SYMLINK = 0xA000000C
_LINK_TAGS = (_IO_REPARSE_TAG_MOUNT_POINT, _IO_REPARSE_TAG_SYMLINK)


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def _protected_paths():
    """Paths the cleaner must never touch: the PyInstaller onefile extraction dir (sys._MEIPASS)
    holds this running program's own runtime (base_library.zip, lazy-imported modules)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass:
        return {_norm(meipass)}
    return set()


def _attributes(entry):
    return getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)


def _is_link(entry):
    """True for symlinks and for directories that are reparse points (junctions included).

    DirEntry.is_symlink() is False for junctions, while is_dir() is True: walking into one
    would clean its target, which may be anywhere on disk.
    """
    if entry.is_symlink():
        return True
    attributes = _attributes(entry)
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT and attributes & stat.FILE_ATTRIBUTE_DIRECTORY)


def _remove_link(entry):
    """Removes a junction or symlink itself, never its target; other reparse points stay."""
    tag = getattr(entry.stat(follow_symlinks=False), "st_reparse_tag", _IO_REPARSE_TAG_SYMLINK)
    if tag not in _LINK_TAGS:
        return
    if _attributes(entry) & stat.FILE_ATTRIBUTE_DIRECTORY:
        os.rmdir(entry.path)
    else:
        os.remove(entry.path)


def _is_recent(info, cutoff):
    """True if a stat result was created or changed after cutoff (extracted files keep old mtimes)."""
    return cutoff is not None and max(info.st_mtime, info.st_ctime) > cutoff


def get_dir_size(path, protected=frozenset(), cutoff=None):
    """Calculates the total size of a directory in bytes, without following links."""
    total = 0
    try:
        entries = list(os.scandir(path))
    except OSError:
        return 0
    for entry in entries:
        try:
            if _is_link(entry):
                continue
            if entry.is_file():
                info = entry.stat()
                if not _is_recent(info, cutoff):
                    total += info.st_size
            elif entry.is_dir() and _norm(entry.path) not in protected:
                total += get_dir_size(entry.path, protected, cutoff)
        except OSError:
            continue
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

def _remove_and_measure(path, protected=frozenset(), cutoff=None):
    """Recursively deletes a directory tree, summing freed bytes in a single pass."""
    total = 0
    try:
        keep_dir = _is_recent(os.stat(path, follow_symlinks=False), cutoff)
        entries = list(os.scandir(path))
    except OSError:
        return 0
    for entry in entries:
        try:
            if _is_link(entry):
                _remove_link(entry)
            elif entry.is_file():
                info = entry.stat()
                if not _is_recent(info, cutoff):
                    os.remove(entry.path)
                    total += info.st_size
            elif entry.is_dir() and _norm(entry.path) not in protected:
                total += _remove_and_measure(entry.path, protected, cutoff)
        except OSError:
            pass
    if not keep_dir:
        try:
            os.rmdir(path)
        except OSError:
            pass
    return total


def _sensitive_paths():
    """Folders that must survive, so no cleaned root may be one of them or contain one."""
    home = os.path.expanduser("~")
    candidates = [r"C:\Windows", os.environ.get("SystemRoot"), home]
    candidates += [os.path.join(home, name) for name in ("Desktop", "Documents", "Downloads")]
    candidates += [
        os.environ.get(name)
        for name in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "ProgramData", "ProgramFiles", "ProgramFiles(x86)")
    ]
    return {_norm(p) for p in candidates if p}


def is_safe_clean_root(path):
    """False for roots that must never be emptied, wherever the environment points them."""
    if not os.path.isabs(path):
        return False
    root = _norm(path)
    if root == os.path.splitdrive(root)[0] + os.sep:
        return False
    prefix = root + os.sep
    return not any(p == root or p.startswith(prefix) for p in _sensitive_paths())


def clean_directory(directory_path, progress_callback=None, dry_run=False, min_age_seconds=0, keep_names=()):
    """
    Safely deletes all files and subdirectories within a directory.
    Ignores files that are currently in use. When dry_run is True, only
    measures what would be freed without deleting anything. Items newer than
    min_age_seconds and top-level names in keep_names are left alone.
    """
    path = Path(directory_path)
    bytes_freed = 0
    protected = _protected_paths()
    cutoff = time.time() - min_age_seconds if min_age_seconds else None
    keep = {name.lower() for name in keep_names}

    if not path.exists():
        log.info("limpeza '%s': pasta inexistente, ignorada", path)
        return 0
    if not is_safe_clean_root(str(path)):
        log.error("limpeza '%s': pasta recusada, não é uma pasta temporária segura", path)
        return 0

    log.info("limpeza '%s': iniciando (dry_run=%s)", path, dry_run)
    skipped = 0
    try:
        entries = list(os.scandir(path))
        log.debug("limpeza '%s': %d entradas encontradas", path, len(entries))
        for entry in entries:
            try:
                if entry.name.lower() in keep:
                    pass
                elif _is_link(entry):
                    if not dry_run:
                        _remove_link(entry)
                elif entry.is_file():
                    info = entry.stat()
                    if not _is_recent(info, cutoff):
                        if not dry_run:
                            os.remove(entry.path)
                        bytes_freed += info.st_size
                elif entry.is_dir():
                    if _norm(entry.path) in protected:
                        pass
                    elif dry_run:
                        bytes_freed += get_dir_size(entry.path, protected, cutoff)
                    else:
                        bytes_freed += _remove_and_measure(entry.path, protected, cutoff)
            except OSError as exc:
                # Skip files/folders in use or already gone (logged, never surfaced)
                skipped += 1
                log.debug("limpeza: ignorado '%s': %s", entry.path, exc)

            if progress_callback:
                progress_callback(1)
    except OSError as exc:
        log.warning("limpeza '%s': não foi possível listar a pasta: %s", path, exc)

    log.info("limpeza '%s': concluída, %d bytes liberados, %d entradas ignoradas", path, bytes_freed, skipped)
    return bytes_freed

ADMIN_ONLY_PATHS = frozenset({"System Temp", "Prefetch"})

_DAY = 24 * 60 * 60

# Extra clean_directory arguments per folder: running apps keep recent temp files, and model
# downloads in ~/.cache are too expensive to recreate.
CLEAN_RULES = {
    "User Temp": {"min_age_seconds": _DAY},
    "System Temp": {"min_age_seconds": _DAY},
    "User Cache": {"keep_names": ("huggingface", "torch", "lm-studio", "ollama")},
}


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


# --- Cache and Recycle Bin cleanups (measured before/after; nothing is moved) ---

def _tool_cache_dir(env_var, *default_parts):
    """Returns a tool's cache folder without running the tool: this process may be elevated,
    and whatever is on the user's PATH must not inherit that."""
    configured = os.environ.get(env_var)
    if configured:
        return configured
    local = os.environ.get("LOCALAPPDATA")
    return os.path.join(local, *default_parts) if local else None


def _measure_cache(path):
    return get_dir_size(path) if path else 0


def _clean_cache(path):
    if path:
        clean_directory(path)
    return True, ""


def _npm_cache():
    return _tool_cache_dir("NPM_CONFIG_CACHE", "npm-cache")


def _uv_cache():
    return _tool_cache_dir("UV_CACHE_DIR", "uv", "cache")


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


# id -> (label, executable that must be installed or None, size-measuring fn, clean fn)
COMMAND_CLEANUPS = {
    "npm-cache": ("npm cache", "npm", lambda: _measure_cache(_npm_cache()), lambda: _clean_cache(_npm_cache())),
    "uv-cache": ("uv cache", "uv", lambda: _measure_cache(_uv_cache()), lambda: _clean_cache(_uv_cache())),
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
