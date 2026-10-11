import sys
from rich.console import Console
from rich.panel import Panel
from rich import box

from ._terminal import clear_screen, wait_for_keypress_and_maybe_close

from ..audio import play_victory

def display_completion_screen(console: Console, total_formatted, dry_run=False, close_terminal=True, skip_wait=False, driver_summary=None):
    """Displays the final screen with the amount of space freed in 8-bit Game Boy style."""
    clear_screen(console)
    console.print("\n" * max(1, (console.height // 5)))

    title = "SIMULAÇÃO CONCLUÍDA" if dry_run else "LIMPEZA CONCLUÍDA"
    verb = "seriam limpos" if dry_run else "foram limpos"

    body = (
        f"[bold #9bbc0f]★ ★ ★ {title} ★ ★ ★[/bold #9bbc0f]\n\n"
        f"[bold #cadc9f]TOTAL SCORE: {total_formatted} {verb} do seu sistema[/bold #cadc9f]"
    )
    if driver_summary:
        body += f"\n\n{driver_summary}"

    success_panel = Panel(
        body,
        box=box.DOUBLE,
        border_style="bold #8bac0f",
        expand=False,
        padding=(1, 4)
    )
    console.print(success_panel, justify="center")

    play_victory()

    if skip_wait:
        sys.exit(0)

    console.print("\n\n[dim]pressione qualquer tecla para sair[/dim]", justify="center")

    wait_for_keypress_and_maybe_close(close_terminal=close_terminal)

    sys.exit(0)

