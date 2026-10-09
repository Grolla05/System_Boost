from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from backend.hardware import MachineInfo
from frontend import cli
from frontend.components import level_menu, machine_info


@pytest.fixture(autouse=True)
def _tty(monkeypatch):
    """The arrow/number-key path is only taken on a TTY; pytest captures stdin so force it."""
    monkeypatch.setattr(level_menu, "_is_interactive_terminal", lambda: True)


def _console():
    out = StringIO()
    return out, Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)


# --- level menu: 5th option ---------------------------------------------

def test_info_choice_is_exported_through_cli():
    assert cli.INFO_CHOICE == level_menu.INFO_CHOICE
    assert level_menu.INFO_CHOICE not in level_menu.LEVEL_ORDER


def test_menu_panel_lists_info_option():
    out, console = _console()

    console.print(level_menu._render_menu_panel(0))

    text = out.getvalue()
    assert "[5]" in text
    assert "FICHA" in text.upper()


def test_menu_panel_still_lists_all_four_levels():
    out, console = _console()

    console.print(level_menu._render_menu_panel(0))

    text = out.getvalue()
    for n in "1234":
        assert f"[{n}]" in text


def test_direct_key_5_returns_info_choice():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", return_value="5"):
        assert level_menu.display_level_menu(console) == level_menu.INFO_CHOICE


def test_arrow_down_four_times_reaches_info_option():
    _, console = _console()

    keys = ["down", "down", "down", "down", "enter"]
    with patch("frontend.components.level_menu._read_menu_key", side_effect=keys):
        assert level_menu.display_level_menu(console) == level_menu.INFO_CHOICE


def test_arrow_up_from_first_wraps_to_info_option():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", side_effect=["up", "enter"]):
        assert level_menu.display_level_menu(console) == level_menu.INFO_CHOICE


def test_arrow_down_five_times_wraps_back_to_first_level():
    _, console = _console()

    keys = ["down"] * 5 + ["enter"]
    with patch("frontend.components.level_menu._read_menu_key", side_effect=keys):
        assert level_menu.display_level_menu(console) == "leve"


def test_fallback_prompt_accepts_5_for_info():
    _, console = _console()
    seen = {}

    def fake_ask(*args, **kwargs):
        seen.update(kwargs)
        return 5

    with patch("frontend.components.level_menu._is_interactive_terminal", return_value=False):
        with patch("rich.prompt.IntPrompt.ask", side_effect=fake_ask):
            assert level_menu.display_level_menu(console) == level_menu.INFO_CHOICE

    assert "5" in seen["choices"]


# --- info screen with "press a key to go back" ---------------------------

def test_info_screen_waits_for_key_when_asked():
    out, console = _console()

    with patch("frontend.components.machine_info._read_single_key") as read:
        machine_info.display_machine_info(console, MachineInfo(windows="Windows 11 Pro"), wait=True)

    read.assert_called_once()
    text = out.getvalue()
    assert "Windows 11 Pro" in text
    assert "voltar" in text.lower()


def test_info_screen_does_not_wait_by_default():
    _, console = _console()

    with patch("frontend.components.machine_info._read_single_key") as read:
        machine_info.display_machine_info(console, MachineInfo())

    read.assert_not_called()


def test_cli_show_machine_info_forwards_wait():
    with patch("frontend.cli.display_machine_info") as display:
        cli.show_machine_info("INFO", wait=True)

    display.assert_called_once_with(cli.console, "INFO", wait=True)


# --- cmd_menu loop --------------------------------------------------------

def _patch_menu_flow(monkeypatch, choices, proceed=False):
    import main

    shown, summaries = [], []
    fetches = []
    sentinel = object()

    monkeypatch.setattr(main, "show_welcome", lambda skip_wait=False: None)
    monkeypatch.setattr(main, "show_level_menu", lambda it=iter(choices): next(it))
    monkeypatch.setattr(main, "get_machine_info", lambda: fetches.append(1) or sentinel)
    monkeypatch.setattr(main, "show_machine_info", lambda info, wait=False: shown.append((info, wait)))
    monkeypatch.setattr(main.profiles, "resolve_clean_paths", lambda level: {})
    monkeypatch.setattr(main.profiles, "resolve_tweak_plan", lambda level: ([], []))
    monkeypatch.setattr(
        main, "show_level_summary",
        lambda level_id, *a, **k: summaries.append(level_id) or proceed,
    )
    return main, shown, summaries, fetches, sentinel


def test_cmd_menu_info_option_shows_sheet_and_returns_to_menu(monkeypatch):
    main, shown, summaries, fetches, sentinel = _patch_menu_flow(
        monkeypatch, [cli.INFO_CHOICE, "leve"]
    )

    main.cmd_menu(main.parse_args(["menu"]))

    assert shown == [(sentinel, True)]
    assert summaries == ["leve"]  # level flow resumed after the sheet, info id never treated as a level


def test_cmd_menu_reads_hardware_only_once_across_repeated_views(monkeypatch):
    main, shown, summaries, fetches, sentinel = _patch_menu_flow(
        monkeypatch, [cli.INFO_CHOICE, cli.INFO_CHOICE, cli.INFO_CHOICE, "leve"]
    )

    main.cmd_menu(main.parse_args(["menu"]))

    assert len(shown) == 3
    assert len(fetches) == 1


def test_cmd_menu_without_info_never_reads_hardware(monkeypatch):
    main, shown, summaries, fetches, sentinel = _patch_menu_flow(monkeypatch, ["leve"])

    main.cmd_menu(main.parse_args(["menu"]))

    assert fetches == []
    assert shown == []

