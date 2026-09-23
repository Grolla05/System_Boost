from rich import box
from rich.console import Console
from rich.panel import Panel

from ._terminal import wait_for_exit_or_back


def display_level_completion(console: Console, level_label, total_formatted, tweak_results, close_terminal=True, skip_wait=False):
    """Shows the combined cleanup + tweaks summary; returns 'back' or 'exit' based on the user's choice."""
    console.clear()
    console.print("\n" * (console.height // 3))

    applied = [r for r in tweak_results if r[1] is True]
    skipped = [r for r in tweak_results if r[1] is None]
    failed = [r for r in tweak_results if r[1] is False]

    body = (
        f"[bold success]OTIMIZAÇÃO {level_label.upper()} CONCLUÍDA[/bold success]\n\n"
        f"[white]{total_formatted} liberados do seu sistema[/white]\n"
        f"[white]{len(applied)} ajuste(s) aplicado(s)[/white]"
    )
    if skipped:
        body += f"\n[warning]{len(skipped)} pulado(s) (requer Administrador)[/warning]"
    if failed:
        body += f"\n[danger]{len(failed)} falharam[/danger]"

    panel = Panel(body, box=box.ROUNDED, border_style="success", expand=False, padding=(1, 4))
    console.print(panel, justify="center")

    if skip_wait:
        return "exit"

    console.print(
        "\n\n[dim]pressione Enter para sair ou ESC para voltar ao menu principal[/dim]",
        justify="center",
    )
    return wait_for_exit_or_back(close_terminal=close_terminal)
