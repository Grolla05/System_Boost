import os
import sys
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

from backend.profiles import LEVEL_ORDER, LEVELS
from backend.tweaks import catalog as tweaks_catalog
from ..audio import play_blip, play_select
from ._terminal import clear_screen, flush_input

# Returned by display_level_menu instead of a level id when the user picks "ver ficha da máquina".
INFO_CHOICE = "info"
_OPTIONS = tuple(LEVEL_ORDER) + (INFO_CHOICE,)
_DIGIT_KEYS = tuple(str(i) for i in range(1, len(_OPTIONS) + 1))


def _is_interactive_terminal() -> bool:
    """Checks whether the session is running in an interactive TTY console."""
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def _read_menu_key() -> str:
    """Reads a single key for menu navigation (up, down, enter, esc, or 1-5)."""
    flush_input()
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            code = msvcrt.getch()
            if code == b"H":
                return "up"
            elif code == b"P":
                return "down"
            return ""
        if ch in (b"\r", b"\n"):
            return "enter"
        if ch == b"\x1b":
            return "esc"
        if ch in (b"p", b"P"):
            return "p"
        if ch.decode("latin1") in _DIGIT_KEYS:
            return ch.decode("latin1")
        if ch in (b"q", b"Q"):
            return "esc"
        return ""
    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    seq = sys.stdin.read(2)
                    if seq == "[A":
                        return "up"
                    elif seq == "[B":
                        return "down"
                return "esc"
            if ch in ("\r", "\n"):
                return "enter"
            if ch in _DIGIT_KEYS:
                return ch
            if ch in ("p", "P"):
                return "p"
            if ch in ("q", "Q"):
                return "esc"
            return ""
        except Exception:
            return ""
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _render_menu_panel(selected_idx: int) -> Panel:
    """Renders the stage selection panel with a retro pointer and palette status."""
    from ..palettes import PALETTES, get_current_palette_name
    pal_name = PALETTES.get(get_current_palette_name(), {}).get("name", "Classic")

    lines = []
    stage_titles = [
        "STAGE 1: LEVE (NORMAL)",
        "STAGE 2: MEDIANA (TURBO BOOST)",
        "STAGE 3: ALTA (OVERCLOCK)",
        "STAGE 4: EXTREMA (HYPER DRIVE)",
    ]

    for i, level_id in enumerate(LEVEL_ORDER):
        level = LEVELS[level_id]
        stage_title = stage_titles[i]
        num = i + 1

        if i == selected_idx:
            lines.append(f"[bold success]► [{num}] {stage_title}[/bold success]")
            lines.append(f"    [bold warning]{level['description']}[/bold warning]")
        else:
            lines.append(f"  [dim] [{num}] {stage_title}[/dim]")
            lines.append(f"    [dim]{level['description']}[/dim]")
        lines.append("")

    info_idx = len(LEVEL_ORDER)
    info_num = info_idx + 1
    if selected_idx == info_idx:
        lines.append(f"[bold success]► [{info_num}] VER FICHA DA MÁQUINA[/bold success]")
        lines.append("    [bold warning]Windows, CPU, RAM, GPU, disco e tipo (notebook/desktop)[/bold warning]")
    else:
        lines.append(f"  [dim] [{info_num}] VER FICHA DA MÁQUINA[/dim]")
        lines.append("    [dim]Windows, CPU, RAM, GPU, disco e tipo (notebook/desktop)[/dim]")

    subtitle = f"[bold accent][↑/↓] Navegar  [1-5] Direto  [P] Tema: {pal_name}  [ENTER] Confirmar[/bold accent]"
    return Panel(
        "\n".join(lines),
        title="[bold accent]╔═ SELECT OPTIMIZATION STAGE ═╗[/bold accent]",
        subtitle=subtitle,
        box=box.DOUBLE,
        border_style="accent",
        padding=(1, 3),
        expand=False,
    )


def display_level_menu(console: Console):
    """Shows the 4 optimization levels plus 'ver ficha' with arrow / number key navigation.

    Returns the chosen level id, or INFO_CHOICE when the user asks for the machine spec sheet.
    """
    if not _is_interactive_terminal():
        clear_screen(console)
        console.print(_render_menu_panel(0))
        choice = IntPrompt.ask(
            f"Digite o número da opção desejada (1-{len(_OPTIONS)})",
            choices=list(_DIGIT_KEYS),
            default=1,
        )
        return _OPTIONS[choice - 1]

    selected_idx = 0
    while True:
        clear_screen(console)
        console.print("\n" * max(1, (console.height // 8)))
        panel = _render_menu_panel(selected_idx)
        console.print(panel, justify="center")

        key = _read_menu_key()
        if key == "up":
            selected_idx = (selected_idx - 1) % len(_OPTIONS)
            play_blip()
        elif key == "down":
            selected_idx = (selected_idx + 1) % len(_OPTIONS)
            play_blip()
        elif key in _DIGIT_KEYS:
            selected_idx = int(key) - 1
            play_select()
            return _OPTIONS[selected_idx]
        elif key == "p":
            from ..cli import cycle_active_palette
            cycle_active_palette()
            play_blip()
        elif key == "enter":
            play_select()
            return _OPTIONS[selected_idx]
        elif key == "esc":
            play_select()
            return _OPTIONS[selected_idx]


def display_level_summary(console: Console, level_id, clean_paths, applicable_ids, skipped_ids):
    """Shows the retro pre-scan disk breakdown and mission briefing before running."""
    from backend import cleaner
    from .disk_breakdown import measure_paths_sizes, create_disk_breakdown_panel

    level = LEVELS[level_id]

    try:
        all_temp = cleaner.get_temp_paths()
        active_paths = {p: all_temp[p] for p in clean_paths if p in all_temp}
        if active_paths:
            sizes = measure_paths_sizes(active_paths)
            console.print(create_disk_breakdown_panel(sizes))
            console.print()
    except Exception:
        pass

    lines = [
        f"[bold success]MISSION BRIEFING // STAGE: {level['label'].upper()}[/bold success]",
        "",
        "[bold accent]Pastas a limpar:[/bold accent] " + (", ".join(sorted(clean_paths)) if clean_paths else "nenhuma"),
        "",
        "[bold accent]Ajustes a aplicar:[/bold accent]",
    ]

    for tweak_id in applicable_ids:
        lines.append(f"  [bold warning]⚡ {tweaks_catalog.get_tweak(tweak_id).label}[/bold warning]")
    if not applicable_ids:
        lines.append("  [dim](nenhum)[/dim]")

    if skipped_ids:
        lines.append("")
        lines.append("[warning]Pulados (requer Administrador):[/warning]")
        for tweak_id in skipped_ids:
            lines.append(f"  [warning]• {tweaks_catalog.get_tweak(tweak_id).label}[/warning]")

    briefing_panel = Panel("\n".join(lines), box=box.DOUBLE, border_style="accent", expand=False, padding=(1, 3))
    console.print(briefing_panel)
    return Confirm.ask("[bold success]Iniciar missão?[/bold success]", default=True)
