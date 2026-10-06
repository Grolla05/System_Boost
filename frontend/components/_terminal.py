"""Shared keypress + terminal auto-close helpers for 'run and done' screens."""
import os
import sys

ESC_KEYS = (b"\x1b", "\x1b")


def flush_input():
    """Discards keystrokes typed while the program was busy, so a stale key can't skip a 'press a key' wait."""
    try:
        if os.name == 'nt':
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        else:
            import termios
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass


def _read_single_key():
    """Reads and returns one raw keypress (bytes on Windows, 1-char str on POSIX)."""
    flush_input()
    if os.name == 'nt':
        import msvcrt
        return msvcrt.getch()

    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    except Exception:
        return ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def clear_screen(console):
    """Erases the visible screen. rich's console.clear() only homes the cursor on some Windows consoles."""
    console.clear()
    if not console.is_terminal:
        return
    if os.name == 'nt':
        os.system("cls")
    else:
        console.file.write("\x1b[2J\x1b[3J\x1b[H")
        console.file.flush()


def _close_terminal():
    """Best-effort force-close of the hosting console window (Windows only)."""
    if os.name != 'nt':
        return
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            WM_CLOSE = 0x0010
            ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    except Exception:
        pass


def wait_for_keypress_and_maybe_close(close_terminal=True):
    """Blocks for one keypress, then optionally force-closes the hosting terminal (Windows)."""
    _read_single_key()
    if close_terminal:
        _close_terminal()


def wait_for_exit_or_back(close_terminal=True):
    """Blocks for one keypress. Returns 'back' on ESC, else 'exit' (closing the terminal if asked)."""
    key = _read_single_key()
    if key in ESC_KEYS:
        return "back"
    if close_terminal:
        _close_terminal()
    return "exit"
