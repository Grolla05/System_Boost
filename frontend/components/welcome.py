from rich import box
from rich.console import Console
from rich.panel import Panel

from ..audio import play_start
from ._terminal import _read_single_key, clear_screen

BANNER = """
[highlight] ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗   ██████╗  ██████╗  ██████╗ ███████╗████████╗[/highlight]
[accent] ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████╝   ██╔══██╗██╔═══██╗██╔═══██╗██╔════╝╚══██╔══╝[/accent]
[accent] ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║   ██████╔╝██║   ██║██║   ██║███████╗   ██║   [/accent]
[dim] ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║   ██╔══██╗██║   ██║██║   ██║╚════██║   ██║   [/dim]
[dim] ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║   ██████╔╝╚██████╔╝╚██████╔╝███████║   ██║   [/dim]
[dim] ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝   ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   [/dim]
"""

SUBTITLE = "[accent]►►► SYSTEM BOOST // GAME BOY EDITION ◄◄◄[/accent]\n[dim][ DISK CLEANUP & KERNEL TWEAKS ][/dim]"


def display_welcome_screen(console: Console, skip_wait: bool = False):
    """Displays the 8-bit Game Boy retro welcome screen."""
    clear_screen(console)
    console.print("\n" * max(1, (console.height // 6)))

    console.print(BANNER, justify="center")
    console.print(SUBTITLE, justify="center")
    console.print()

    box_content = "[highlight]► [ PRESS ANY KEY TO START ] ◄[/highlight]"
    prompt_panel = Panel(
        box_content,
        box=box.DOUBLE,
        border_style="border",
        expand=False,
        padding=(0, 3),
    )
    console.print(prompt_panel, justify="center")

    play_start()

    if skip_wait:
        return

    _read_single_key()

