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


def test_flush_input_drains_pending_keys_on_windows(monkeypatch):
    import sys
    import types

    pending = [True, True, False]
    drained = []
    fake_msvcrt = types.SimpleNamespace(kbhit=lambda: pending.pop(0), getch=lambda: drained.append(1) or b"x")
    monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)
    monkeypatch.setattr(_terminal.os, "name", "nt")

    _terminal.flush_input()

    assert len(drained) == 2


def test_read_single_key_flushes_before_waiting(monkeypatch):
    import sys
    import types

    order = []
    fake_msvcrt = types.SimpleNamespace(kbhit=lambda: False, getch=lambda: order.append("getch") or b"x")
    monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)
    monkeypatch.setattr(_terminal.os, "name", "nt")
    monkeypatch.setattr(_terminal, "flush_input", lambda: order.append("flush"))

    _terminal._read_single_key()

    assert order == ["flush", "getch"]
