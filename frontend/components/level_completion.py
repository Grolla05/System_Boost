from rich import box
from rich.console import Console
from rich.panel import Panel

from ._terminal import clear_screen, wait_for_exit_or_back
from .level_menu import REVERT_HINT


from ..audio import play_victory


def display_level_completion(console: Console, level_label, total_formatted, tweak_results, close_terminal=True, skip_wait=False, driver_summary=None):
    """Shows the combined cleanup + tweaks summary in 8-bit Game Boy style; returns 'back' or 'exit'."""
    clear_screen(console)
    console.print("\n" * max(1, (console.height // 5)))

    applied = [r for r in tweak_results if r[1] is True]
    already = [r for r in tweak_results if r[1] == "already"]
    skipped = [r for r in tweak_results if r[1] is None]
    failed = [r for r in tweak_results if r[1] is False]

    body = (
        f"[bold #9bbc0f]★ ★ ★ OTIMIZAÇÃO {level_label.upper()} CONCLUÍDA ★ ★ ★[/bold #9bbc0f]\n\n"
        f"[bold #cadc9f]SCORE: {total_formatted} liberados do seu sistema[/bold #cadc9f]\n"
        f"[bold #8bac0f]BUFFS: {len(applied)} ajuste(s) aplicado(s)[/bold #8bac0f]"
    )
    if already:
        body += f"\n[dim #cadc9f]  • {len(already)} já aplicado(s) anteriormente[/dim #cadc9f]"
    if applied or already:
        body += f"\n[dim]  Para reverter: {REVERT_HINT}[/dim]"
    if skipped:
        reasons = ", ".join(sorted({r[2] for r in skipped if r[2]})) or "pulado"
        body += f"\n[warning]  • {len(skipped)} pulado(s) ({reasons})[/warning]"
    if failed:
        body += f"\n[danger]  • {len(failed)} falharam[/danger]"
        for tweak_id, _, note in failed:
            body += f"\n[danger]    - {tweak_id}: {note}[/danger]"
    if driver_summary:
        body += f"\n\n{driver_summary}"

    panel = Panel(body, box=box.DOUBLE, border_style="bold #8bac0f", expand=False, padding=(1, 4))
    console.print(panel, justify="center")

    play_victory()

    if skip_wait:
        return "exit"

    console.print(
        "\n\n[dim]pressione Enter para sair ou ESC para voltar ao menu principal[/dim]",
        justify="center",
    )
    return wait_for_exit_or_back(close_terminal=close_terminal)
