"""8-bit typewriter text rendering with optional audio clicks and instant skip."""
import os
import sys
import time
from rich.console import Console

from .audio import play_typewriter_click


def _has_keypress() -> bool:
    """Non-blocking check if a key has been pressed."""
    try:
        if os.name == "nt":
            import msvcrt
            return msvcrt.kbhit()
        else:
            import select
            r, _, _ = select.select([sys.stdin], [], [], 0)
            return bool(r)
    except Exception:
        return False


def typewriter_print(
    console: Console,
    text: str,
    speed: float = 0.012,
    sound: bool = True,
    skip: bool = False,
):
    """Prints text with a retro typewriter character delay and sound clicks.

    If skip is True, or if output is piped/non-terminal, renders immediately.
    Pressing any key during rendering skips to the end instantly.
    """
    if skip or not getattr(console, "is_terminal", True) or speed <= 0:
        console.print(text)
        return

    skipped = False
    for i, ch in enumerate(text):
        if not skipped and _has_keypress():
            skipped = True

        console.file.write(ch)
        if not skipped:
            console.file.flush()
            if sound and i % 4 == 0 and ch not in " \n\r\t":
                play_typewriter_click()
            if speed > 0:
                time.sleep(speed)

    console.file.write("\n")
    console.file.flush()

