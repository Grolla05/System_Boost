"""File logging for step-by-step diagnostics; never writes to the console or raises."""
import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT_LOGGER_NAME = "system_boost"
LOG_FILE_NAME = "system_boost.log"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 5
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def default_log_dir():
    """Returns <project root>/logs; for a frozen exe, the parent of dist/ (or the exe's own dir)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        base = exe_dir.parent if exe_dir.name.lower() == "dist" else exe_dir
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "logs"


def get_logger(name):
    """Returns a child logger under the system_boost root (e.g. system_boost.profiles)."""
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def _is_admin_safe():
    try:
        from .privileges import is_admin
        return is_admin()
    except Exception:
        return None


def setup_logging(log_dir=None, argv=None):
    """Attaches a rotating file handler once; returns the log file path, or None if unwritable."""
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(logging.DEBUG)
    root.propagate = True

    for handler in root.handlers:
        if isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename)

    log_dir = Path(log_dir) if log_dir else default_log_dir()
    log_file = log_dir / LOG_FILE_NAME
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_file, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
        )
    except OSError:
        root.addHandler(logging.NullHandler())
        return None

    handler.setFormatter(logging.Formatter(_FORMAT))
    handler.setLevel(logging.DEBUG)
    root.addHandler(handler)

    root.info("=" * 60)
    root.info(
        "SESSÃO INICIADA | python=%s | os=%s | admin=%s | frozen=%s | pid=%s | argv=%s",
        platform.python_version(), platform.platform(), _is_admin_safe(),
        bool(getattr(sys, "frozen", False)), os.getpid(),
        list(sys.argv[1:] if argv is None else argv),
    )
    return log_file
