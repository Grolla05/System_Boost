from io import StringIO
from unittest.mock import patch

from rich.console import Console

from frontend import cli
from frontend.components import level_menu, welcome, completion, level_completion


def test_gameboy_theme_defined():
    # Verify the theme exists and has Game Boy DMG color tokens
    theme = cli.custom_theme
    assert "accent" in theme.styles
    assert "success" in theme.styles
    assert "header" in theme.styles


def test_welcome_screen_renders_banner():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)
    with patch("frontend.components.welcome._read_single_key"):
        with patch("frontend.audio.play_start"):
            welcome.display_welcome_screen(console, skip_wait=True)
    text = out.getvalue()
    assert "SYSTEM BOOST" in text or "BOOST" in text
    assert "PRESS" in text or "pressione" in text.lower()


def test_level_menu_direct_number_key():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)

    # Pressing '2' selects 'mediana' directly
    with patch("frontend.components.level_menu._is_interactive_terminal", return_value=True):
        with patch("frontend.components.level_menu._read_menu_key", return_value="2"):
            chosen = level_menu.display_level_menu(console)
            assert chosen == "mediana"


def test_level_menu_arrow_and_enter():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)

    # Pressing DOWN once moves from 1 to 2, then ENTER confirms
    keys = ["down", "enter"]
    with patch("frontend.components.level_menu._is_interactive_terminal", return_value=True):
        with patch("frontend.components.level_menu._read_menu_key", side_effect=keys):
            chosen = level_menu.display_level_menu(console)
            assert chosen == "mediana"


def test_level_menu_fallback_when_piped():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)

    # When not a tty / piped, it reads from prompt input
    with patch("frontend.components.level_menu._is_interactive_terminal", return_value=False):
        with patch("rich.prompt.IntPrompt.ask", return_value=3):
            chosen = level_menu.display_level_menu(console)
            assert chosen == "alta"


def test_level_summary_renders_briefing():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)

    with patch("rich.prompt.Confirm.ask", return_value=True):
        res = level_menu.display_level_summary(
            console, "leve", ["User Temp"], ["visual_effects"], []
        )
        assert res is True

    text = out.getvalue()
    assert "User Temp" in text
    assert "Efeitos visuais" in text or "visual" in text.lower()


def test_completion_screen_renders_arcade_score():
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)

    with patch("frontend.audio.play_victory"):
        with patch("sys.exit", side_effect=SystemExit):
            try:
                completion.display_completion_screen(
                    console, "150.00 MB", dry_run=False, skip_wait=True
                )
            except SystemExit:
                pass
    text = out.getvalue()
    assert "150.00 MB" in text
    assert "LIMPEZA CONCLUÍDA" in text or "STAGE" in text or "CONCLUÍDA" in text
