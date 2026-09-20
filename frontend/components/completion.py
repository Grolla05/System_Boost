import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich import box

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

    # Wait for key press
    if os.name == 'nt':
        import msvcrt
        msvcrt.getch()

        # Close the console window (PowerShell / CMD) on Windows
        if close_terminal:
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    WM_CLOSE = 0x0010
                    ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            except Exception:
                pass
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        except Exception:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    sys.exit(0)

