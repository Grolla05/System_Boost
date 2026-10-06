from rich import box
from rich.console import Console
from rich.panel import Panel


def display_tweak_success(console: Console, message):
    """Prints a success panel for a completed apply/undo action."""
    console.print(Panel(f"[success]{message}[/success]", box=box.ROUNDED, border_style="success", expand=False))


def display_tweak_error(console: Console, message):
    """Prints an error panel when an apply/undo action fails."""
    console.print(Panel(f"[danger]{message}[/danger]", box=box.ROUNDED, border_style="danger", expand=False))


def display_undo_all_results(console: Console, results):
    """Prints one success/failure line per tweak for a `boost undo --all` run."""
    for tweak_id, success, error in results:
        if success:
            console.print(f"[success]OK[/success] {tweak_id}")
        else:
            console.print(f"[danger]FALHA[/danger] {tweak_id}: {error}")
