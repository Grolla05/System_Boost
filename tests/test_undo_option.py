from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from backend.tweaks.base import Tweak
from frontend import cli
from frontend.components import level_completion, level_menu, undo_menu


@pytest.fixture(autouse=True)
def _tty(monkeypatch):
    """Arrow/number-key navigation only runs on a TTY; pytest captures stdin so force it."""
    monkeypatch.setattr(level_menu, "_is_interactive_terminal", lambda: True)


def _console():
    out = StringIO()
    return out, Console(file=out, width=100, force_terminal=False, theme=cli.custom_theme)


class _T(Tweak):
    def __init__(self, tweak_id, label, requires_admin=False):
        self.id = tweak_id
        self.label = label
        self.description = label
        self.requires_admin = requires_admin

    def get_current_value(self):
        return None

    def apply(self):
        return None

    def undo(self, previous_value):
        return None


# --- menu: 6th option -------------------------------------------------------

def test_undo_choice_is_exported_and_distinct():
    assert cli.UNDO_CHOICE == level_menu.UNDO_CHOICE
    assert level_menu.UNDO_CHOICE not in level_menu.LEVEL_ORDER
    assert level_menu.UNDO_CHOICE != level_menu.INFO_CHOICE


def test_menu_panel_lists_undo_option_and_range():
    out, console = _console()

    console.print(level_menu._render_menu_panel(0))

    text = out.getvalue()
    assert "[6]" in text
    assert "DESFAZER" in text.upper()
    assert "[1-6]" in text


def test_menu_panel_keeps_info_as_option_5():
    out, console = _console()

    console.print(level_menu._render_menu_panel(0))

    assert "[5] VER FICHA" in out.getvalue()


def test_direct_key_6_returns_undo_choice():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", return_value="6"):
        assert level_menu.display_level_menu(console) == level_menu.UNDO_CHOICE


def test_direct_key_5_still_returns_info_choice():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", return_value="5"):
        assert level_menu.display_level_menu(console) == level_menu.INFO_CHOICE


def test_arrow_down_five_times_reaches_undo_option():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", side_effect=["down"] * 5 + ["enter"]):
        assert level_menu.display_level_menu(console) == level_menu.UNDO_CHOICE


def test_arrow_up_from_first_wraps_to_undo_option():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", side_effect=["up", "enter"]):
        assert level_menu.display_level_menu(console) == level_menu.UNDO_CHOICE


def test_arrow_down_six_times_wraps_back_to_first_level():
    _, console = _console()

    with patch("frontend.components.level_menu._read_menu_key", side_effect=["down"] * 6 + ["enter"]):
        assert level_menu.display_level_menu(console) == "leve"


def test_fallback_prompt_accepts_6_for_undo():
    _, console = _console()
    seen = {}

    def fake_ask(*args, **kwargs):
        seen.update(kwargs)
        return 6

    with patch("frontend.components.level_menu._is_interactive_terminal", return_value=False):
        with patch("rich.prompt.IntPrompt.ask", side_effect=fake_ask):
            assert level_menu.display_level_menu(console) == level_menu.UNDO_CHOICE

    assert "6" in seen["choices"]


# --- undo screens ----------------------------------------------------------------

def _applied():
    return [
        (_T("hibernation", "Desativar hibernação", requires_admin=True),
         {"previous_value": 1, "applied_value": 0}),
        (_T("visual_effects", "Efeitos visuais: melhor desempenho"),
         {"previous_value": None, "applied_value": 2}),
    ]


def test_confirm_lists_every_applied_tweak_and_returns_answer():
    out, console = _console()

    with patch("rich.prompt.Confirm.ask", return_value=True) as ask:
        assert undo_menu.display_undo_confirm(console, _applied(), admin=True) is True

    text = out.getvalue()
    assert "Desativar hibernação" in text
    assert "Efeitos visuais" in text
    ask.assert_called_once()


def test_confirm_returns_false_when_declined():
    _, console = _console()

    with patch("rich.prompt.Confirm.ask", return_value=False):
        assert undo_menu.display_undo_confirm(console, _applied(), admin=True) is False


def test_confirm_warns_about_admin_tweaks_when_not_elevated():
    out, console = _console()

    with patch("rich.prompt.Confirm.ask", return_value=True):
        undo_menu.display_undo_confirm(console, _applied(), admin=False)

    assert "Administrador" in out.getvalue()


def test_confirm_has_no_admin_warning_when_elevated():
    out, console = _console()

    with patch("rich.prompt.Confirm.ask", return_value=True):
        undo_menu.display_undo_confirm(console, _applied(), admin=True)

    assert "Administrador" not in out.getvalue()


def test_empty_screen_says_nothing_to_undo_and_waits():
    out, console = _console()

    with patch("frontend.components.undo_menu._read_single_key") as read:
        undo_menu.display_undo_empty(console, wait=True)

    read.assert_called_once()
    assert "nenhum ajuste" in out.getvalue().lower()


def test_empty_screen_does_not_wait_when_disabled():
    _, console = _console()

    with patch("frontend.components.undo_menu._read_single_key") as read:
        undo_menu.display_undo_empty(console, wait=False)

    read.assert_not_called()


def test_results_show_ok_and_failure_with_reason_and_wait():
    out, console = _console()
    results = [("visual_effects", True, None), ("hibernation", False, "requer privilégios de administrador")]

    with patch("frontend.components.undo_menu._read_single_key") as read:
        undo_menu.display_undo_results(console, results, wait=True)

    text = out.getvalue()
    assert "visual_effects" in text
    assert "hibernation" in text
    assert "requer privilégios de administrador" in text
    assert "1 de 2" in text
    read.assert_called_once()


def test_results_do_not_wait_when_disabled():
    _, console = _console()

    with patch("frontend.components.undo_menu._read_single_key") as read:
        undo_menu.display_undo_results(console, [("a", True, None)], wait=False)

    read.assert_not_called()


# --- "how to revert" hints ------------------------------------------------------

def _completion(tweak_results):
    out, console = _console()
    level_completion.display_level_completion(console, "Leve", "1.00 MB", tweak_results, skip_wait=True)
    return out.getvalue()


def test_completion_tells_how_to_revert_when_tweaks_were_applied():
    text = _completion([("visual_effects", True, None)])

    assert "opção 6" in text
    assert "undo --all" in text


def test_completion_tells_how_to_revert_when_tweaks_were_already_applied():
    assert "undo --all" in _completion([("visual_effects", "already", "já aplicado")])


def test_completion_has_no_revert_hint_when_nothing_was_applied():
    text = _completion([("hibernation", None, "requer administrador"), ("x", False, "erro")])

    assert "undo --all" not in text


def test_summary_mentions_reversibility_when_tweaks_will_apply():
    out, console = _console()

    with patch("rich.prompt.Confirm.ask", return_value=True):
        level_menu.display_level_summary(console, "leve", {}, ["visual_effects"], [])

    assert "undo --all" in out.getvalue()


def test_summary_has_no_reversibility_line_without_tweaks():
    out, console = _console()

    with patch("rich.prompt.Confirm.ask", return_value=True):
        level_menu.display_level_summary(console, "leve", {}, [], [])

    assert "undo --all" not in out.getvalue()


# --- cmd_menu loop --------------------------------------------------------------

def _patch_flow(monkeypatch, choices, applied=None, confirm=True, admin=True):
    import main

    calls = {"undo_all": 0, "confirm": [], "results": [], "empty": [], "errors": [], "summary": []}
    monkeypatch.setattr(main, "show_welcome", lambda skip_wait=False: None)
    monkeypatch.setattr(main, "show_level_menu", lambda it=iter(choices): next(it))
    monkeypatch.setattr(main, "is_admin", lambda: admin)
    monkeypatch.setattr(main, "list_applied", lambda: list(applied or []))
    monkeypatch.setattr(main, "show_undo_confirm", lambda a, admin: calls["confirm"].append((a, admin)) or confirm)
    monkeypatch.setattr(main, "show_undo_results", lambda r, wait=True: calls["results"].append((r, wait)))
    monkeypatch.setattr(main, "show_undo_empty", lambda wait=True: calls["empty"].append(wait))
    monkeypatch.setattr(main, "show_tweak_error", lambda msg: calls["errors"].append(msg))
    monkeypatch.setattr(main.profiles, "resolve_clean_paths", lambda level: {})
    monkeypatch.setattr(main.profiles, "resolve_tweak_plan", lambda level: ([], []))
    monkeypatch.setattr(
        main, "show_level_summary",
        lambda level_id, *a, **k: calls["summary"].append(level_id) or False,
    )

    def fake_undo_all():
        calls["undo_all"] += 1
        return [("visual_effects", True, None)]

    monkeypatch.setattr(main, "undo_all", fake_undo_all)
    return main, calls


def test_cmd_menu_undo_runs_undo_all_and_returns_to_menu(monkeypatch):
    main, calls = _patch_flow(monkeypatch, [cli.UNDO_CHOICE, "leve"], applied=_applied())

    main.cmd_menu(main.parse_args(["menu"]))

    assert calls["undo_all"] == 1
    assert calls["results"] == [([("visual_effects", True, None)], True)]
    assert calls["summary"] == ["leve"]  # undo is not treated as a level


def test_cmd_menu_undo_passes_admin_state_to_confirm(monkeypatch):
    main, calls = _patch_flow(monkeypatch, [cli.UNDO_CHOICE, "leve"], applied=_applied(), admin=False)

    main.cmd_menu(main.parse_args(["menu"]))

    assert calls["confirm"][0][1] is False


def test_cmd_menu_undo_declined_does_nothing(monkeypatch):
    main, calls = _patch_flow(monkeypatch, [cli.UNDO_CHOICE, "leve"], applied=_applied(), confirm=False)

    main.cmd_menu(main.parse_args(["menu"]))

    assert calls["undo_all"] == 0
    assert calls["results"] == []
    assert calls["summary"] == ["leve"]


def test_cmd_menu_undo_with_nothing_applied_shows_empty_screen(monkeypatch):
    main, calls = _patch_flow(monkeypatch, [cli.UNDO_CHOICE, "leve"], applied=[])

    main.cmd_menu(main.parse_args(["menu"]))

    assert calls["empty"] == [True]
    assert calls["confirm"] == []
    assert calls["undo_all"] == 0


def test_cmd_menu_undo_with_yes_skips_confirmation_and_waiting(monkeypatch):
    main, calls = _patch_flow(monkeypatch, [cli.UNDO_CHOICE, "leve"], applied=_applied())

    main.cmd_menu(main.parse_args(["menu", "-y"]))

    assert calls["confirm"] == []
    assert calls["undo_all"] == 1
    assert calls["results"][0][1] is False


def test_cmd_menu_survives_unexpected_error_during_undo(monkeypatch):
    main, calls = _patch_flow(monkeypatch, [cli.UNDO_CHOICE, "leve"], applied=_applied())

    def boom():
        raise RuntimeError("kaboom")

    monkeypatch.setattr(main, "undo_all", boom)

    main.cmd_menu(main.parse_args(["menu"]))

    assert any("kaboom" in m for m in calls["errors"])
    assert calls["summary"] == ["leve"]  # menu kept running
