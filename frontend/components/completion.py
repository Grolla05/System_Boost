import sys
from rich.console import Console
from rich.panel import Panel
from rich import box

from ._terminal import wait_for_keypress_and_maybe_close

def display_completion_screen(console: Console, total_formatted, dry_run=False, close_terminal=True, skip_wait=False):
    """Displays the final screen with the amount of space freed."""
    console.clear()
    console.print("\n" * (console.height // 3))

    title = "SIMULAÇÃO CONCLUÍDA" if dry_run else "LIMPEZA CONCLUÍDA"
    verb = "seriam limpos" if dry_run else "foram limpos"

    success_panel = Panel(
        f"[bold success]{title}[/bold success]\n\n"
        f"[white]{total_formatted} {verb} do seu sistema[/white]",
        box=box.ROUNDED,
        border_style="success",
        expand=False,
        padding=(1, 4)
    )
    console.print(success_panel, justify="center")

    if skip_wait:
        sys.exit(0)

    console.print("\n\n[dim]pressione qualquer tecla para sair[/dim]", justify="center")

    wait_for_keypress_and_maybe_close(close_terminal=close_terminal)

    sys.exit(0)

