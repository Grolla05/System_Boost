from rich import box
from rich.console import Console
from rich.panel import Panel

from ..audio import play_start
from ._terminal import _read_single_key, clear_screen

BANNER = """
[bold #9bbc0f] ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗   ██████╗  ██████╗  ██████╗ ███████╗████████╗[/bold #9bbc0f]
[bold #8bac0f] ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████╝   ██╔══██╗██╔═══██╗██╔═══██╗██╔════╝╚══██╔══╝[/bold #8bac0f]
[bold #8bac0f] ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║   ██████╔╝██║   ██║██║   ██║███████╗   ██║   [/bold #8bac0f]
[bold #306230] ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║   ██╔══██╗██║   ██║██║   ██║╚════██║   ██║   [/bold #306230]
[bold #306230] ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║   ██████╔╝╚██████╔╝╚██████╔╝███████║   ██║   [/bold #306230]
[dim #306230] ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝   ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   [/dim #306230]
"""

SUBTITLE = "[bold #8bac0f]►►► SYSTEM BOOST // GAME BOY EDITION ◄◄◄[/bold #8bac0f]\n[dim #cadc9f][ DISK CLEANUP & KERNEL TWEAKS ][/dim #cadc9f]"


def display_welcome_screen(console: Console, skip_wait: bool = False):
    """Displays the 8-bit Game Boy retro welcome screen."""
    clear_screen(console)
    console.print("\n" * max(1, (console.height // 6)))

    console.print(BANNER, justify="center")
    console.print(SUBTITLE, justify="center")
    console.print()

    box_content = "[bold #9bbc0f]► [ PRESS ANY KEY TO START ] ◄[/bold #9bbc0f]"
    prompt_panel = Panel(
        box_content,
        box=box.DOUBLE,
        border_style="bold #8bac0f",
        expand=False,
        padding=(0, 3),
    )
    console.print(prompt_panel, justify="center")

    play_start()

    if skip_wait:
        return

    _read_single_key()

