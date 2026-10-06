from io import StringIO

from rich.console import Console

from frontend.cli import custom_theme
from frontend.components import level_completion


def _render(tweak_results):
    console = Console(file=StringIO(), width=100, force_terminal=False, theme=custom_theme)
    level_completion.display_level_completion(
        console, "Leve", "1.00 MB", tweak_results, skip_wait=True
    )
    return console.file.getvalue()


def test_already_applied_is_shown_and_not_counted_as_failure():
    out = _render([("visual_effects", "already", "já aplicado")])

    assert "já aplicado" in out
    assert "falharam" not in out
    assert "falha" not in out.lower().replace("já aplicado", "")


def test_failures_list_tweak_id_and_reason():
    out = _render([("hibernation", False, "Falha ao desativar hibernação.")])

    assert "1 falharam" in out
    assert "hibernation" in out
    assert "Falha ao desativar hibernação." in out


def test_skipped_label_uses_real_note():
    out = _render([("telemetry", None, "requer administrador")])

    assert "1 pulado(s)" in out
    assert "requer administrador" in out


def test_applied_count_only_counts_true():
    out = _render([("a", True, None), ("b", "already", "já aplicado"), ("c", False, "x")])

    assert "1 ajuste(s) aplicado(s)" in out
