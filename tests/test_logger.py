import logging
import sys
from pathlib import Path

import pytest

from backend import logger as sb_logger


@pytest.fixture(autouse=True)
def _reset_logging():
    """Removes handlers added during a test so tests don't leak into each other."""
    root = logging.getLogger(sb_logger.ROOT_LOGGER_NAME)
    before = list(root.handlers)
    yield
    for handler in list(root.handlers):
        if handler not in before:
            handler.close()
            root.removeHandler(handler)


def _flush():
    for handler in logging.getLogger(sb_logger.ROOT_LOGGER_NAME).handlers:
        handler.flush()


def test_setup_logging_creates_dir_and_file(tmp_path):
    log_dir = tmp_path / "logs"

    log_file = sb_logger.setup_logging(log_dir=log_dir)
    sb_logger.get_logger("t").info("hello step")
    _flush()

    assert log_file == log_dir / "system_boost.log"
    assert log_file.exists()
    assert "hello step" in log_file.read_text(encoding="utf-8")


def test_setup_logging_is_idempotent(tmp_path):
    sb_logger.setup_logging(log_dir=tmp_path / "logs")
    sb_logger.setup_logging(log_dir=tmp_path / "logs")
    sb_logger.get_logger("t").info("only once")
    _flush()

    content = (tmp_path / "logs" / "system_boost.log").read_text(encoding="utf-8")
    assert content.count("only once") == 1


def test_log_line_format_has_level_and_module(tmp_path):
    sb_logger.setup_logging(log_dir=tmp_path / "logs")
    sb_logger.get_logger("profiles").warning("careful")
    _flush()

    content = (tmp_path / "logs" / "system_boost.log").read_text(encoding="utf-8")
    assert "WARNING" in content
    assert "profiles" in content


def test_session_header_is_written(tmp_path):
    sb_logger.setup_logging(log_dir=tmp_path / "logs", argv=["menu", "-y"])
    _flush()

    content = (tmp_path / "logs" / "system_boost.log").read_text(encoding="utf-8")
    assert "SESSÃO INICIADA" in content
    assert "menu" in content


def test_setup_logging_falls_back_silently_when_dir_unwritable(tmp_path):
    blocker = tmp_path / "file_not_dir"
    blocker.write_text("x")

    result = sb_logger.setup_logging(log_dir=blocker / "logs")
    sb_logger.get_logger("t").info("must not raise")

    assert result is None


def test_default_log_dir_source_mode_is_project_root_logs(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    expected = Path(sb_logger.__file__).resolve().parent.parent / "logs"
    assert sb_logger.default_log_dir() == expected


def test_default_log_dir_frozen_in_dist_uses_parent_of_dist(monkeypatch, tmp_path):
    exe = tmp_path / "proj" / "dist" / "System Boost.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))

    assert sb_logger.default_log_dir() == tmp_path / "proj" / "logs"


def test_default_log_dir_frozen_elsewhere_uses_exe_dir(monkeypatch, tmp_path):
    exe = tmp_path / "apps" / "System Boost.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))

    assert sb_logger.default_log_dir() == tmp_path / "apps" / "logs"
