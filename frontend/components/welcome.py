import os
from rich.console import Console
from rich.panel import Panel
from rich import box

def display_welcome_screen(console: Console, skip_wait: bool = False):
    """Displays the minimalist welcome screen."""
    console.clear()
    # Vertical centering simulation
    console.print("\n" * (console.height // 3))

    welcome_text = "[bold white]BEM-VINDO ao system Cleanup[/bold white]"
    console.print(Panel(welcome_text, box=box.ROUNDED, border_style="accent", expand=False, padding=(1, 4)), justify="center")

    if skip_wait:
        return

    console.print("\n\n[dim]pressione qualquer tecla para prosseguir[/dim]", justify="center")

    # Wait for key press
    if os.name == 'nt':
        import msvcrt
        msvcrt.getch()
    else:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
