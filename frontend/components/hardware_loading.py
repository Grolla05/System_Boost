"""Dedicated retro diagnostic loading screen while scanning hardware components."""
import sys
import threading
import time
from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from ..audio import play_select
from ._terminal import clear_screen

SCAN_STEPS = [
    ("INICIALIZANDO DIAGNÓSTICO...", 1),
    ("LENDO REGISTRO DO WINDOWS...", 3),
    ("SONDANDO PROCESSADOR & THREADS...", 5),
    ("MEDINDO MEMÓRIA RAM INSTALADA...", 7),
    ("CONSULTANDO CONTROLADORES GPU (CIM)...", 9),
    ("IDENTIFICANDO DISCO E TIPO DO CHASSI...", 11),
    ("FINALIZANDO FICHA DA MÁQUINA...", 12),
]

RADAR_FRAMES = [
    "░░▒▒▓▓██▓▓▒▒░░",
    "▒▒▓▓██▓▓▒▒░░░░",
    "▓▓██▓▓▒▒░░░░▒▒",
    "██▓▓▒▒░░░░▒▒▓▓",
    "▓▓▒▒░░░░▒▒▓▓██",
    "▒▒░░░░▒▒▓▓██▓▓",
]


def create_diagnostic_panel(step_idx: int = 0, frame_idx: int = 0) -> Panel:
    """Creates the 8-bit diagnostic scan panel."""
    step_msg, progress_units = SCAN_STEPS[min(step_idx, len(SCAN_STEPS) - 1)]
    radar = RADAR_FRAMES[frame_idx % len(RADAR_FRAMES)]

    total_units = 12
    filled = min(total_units, progress_units)
    bar = f"[bold success]{'▰' * filled}[/bold success][dim]{'▱' * (total_units - filled)}[/dim]"

    lines = [
        "[bold accent]ESCANEANDO HARDWARE DA MÁQUINA...[/bold accent]",
        "",
        f"  [bold]STATUS :[/bold] [bold warning]{step_msg}[/bold warning]",
        f"  [bold]SENSOR :[/bold] [bold success]{bar}[/bold success]",
        f"  [bold]RADAR  :[/bold] [dim accent]{radar}[/dim accent]",
        "",
        "[dim]Aguarde enquanto os subsistemas respondem...[/dim]",
    ]

    return Panel(
        "\n".join(lines),
        title="[bold accent]╔═ HARDWARE DIAGNOSTIC // SYSTEM SCAN ═╗[/bold accent]",
        box=box.DOUBLE,
        border_style="accent",
        padding=(1, 3),
        expand=False,
    )


def show_hardware_loading(console: Console, fetch_func):
    """Displays a dedicated animated retro screen while fetch_func() executes."""
    # Fast path for non-terminal / automated tests
    if not getattr(console, "is_terminal", True):
        return fetch_func()

    result = None
    exc = None

    def worker():
        nonlocal result, exc
        try:
            result = fetch_func()
        except Exception as e:
            exc = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    clear_screen(console)
    vertical_pad = max(1, (console.height - 12) // 2)

    frame_idx = 0
    step_idx = 0

    with Live(
        Align.center(create_diagnostic_panel(step_idx, frame_idx)),
        console=console,
        refresh_per_second=15,
        transient=True,
    ) as live:
        while thread.is_alive():
            time.sleep(0.08)
            frame_idx += 1
            if frame_idx % 3 == 0 and step_idx < len(SCAN_STEPS) - 1:
                step_idx += 1
            live.update(Align.center(create_diagnostic_panel(step_idx, frame_idx)))

    play_select()

    if exc:
        raise exc

    return result

