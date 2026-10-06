import io

from rich.console import Console

from frontend.components import _terminal


def _console(is_terminal):
    return Console(file=io.StringIO(), force_terminal=is_terminal, width=80)


def test_clear_screen_runs_cls_on_windows_terminal(monkeypatch):
    calls = []
    monkeypatch.setattr(_terminal.os, "name", "nt")
    monkeypatch.setattr(_terminal.os, "system", lambda cmd: calls.append(cmd) or 0)

    _terminal.clear_screen(_console(True))

    assert calls == ["cls"]


def test_clear_screen_skips_cls_when_piped(monkeypatch):
    calls = []
    monkeypatch.setattr(_terminal.os, "name", "nt")
    monkeypatch.setattr(_terminal.os, "system", lambda cmd: calls.append(cmd) or 0)

    _terminal.clear_screen(_console(False))

    assert calls == []


def test_clear_screen_writes_ansi_on_posix_terminal(monkeypatch):
    monkeypatch.setattr(_terminal.os, "name", "posix")
    console = _console(True)

    _terminal.clear_screen(console)

    assert "\x1b[2J" in console.file.getvalue()
