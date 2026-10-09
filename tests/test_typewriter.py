from io import StringIO
from unittest.mock import patch
from rich.console import Console

from frontend import typewriter


def test_typewriter_renders_full_text():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False)

    text = "TESTING TYPEWRITER EFFECT"
    typewriter.typewriter_print(console, text, speed=0.0, sound=False)

    rendered = out.getvalue()
    assert "TESTING TYPEWRITER EFFECT" in rendered


def test_typewriter_skips_when_requested():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False)

    text = "SKIPPED TYPEWRITER"
    typewriter.typewriter_print(console, text, skip=True, sound=False)

    rendered = out.getvalue()
    assert "SKIPPED TYPEWRITER" in rendered


def test_typewriter_instant_on_keypress():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=True)

    text = "INTERRUPTED BY USER"
    # Simulate a key already pending in stdin/msvcrt
    with patch("frontend.typewriter._has_keypress", side_effect=[False, True, True]):
        typewriter.typewriter_print(console, text, speed=0.001, sound=False)

    rendered = out.getvalue()
    assert "INTERRUPTED BY USER" in rendered

