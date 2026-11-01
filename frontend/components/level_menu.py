import os
import sys
from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
from rich.text import Text

from backend._system import cli_command
from backend.profiles import LEVEL_ORDER, LEVELS, preview_tweak_items
from backend.tweaks import catalog as tweaks_catalog
from ..audio import play_blip, play_select
from ._terminal import clear_screen, flush_input

# Returned by display_level_menu instead of a level id when the user picks "ver ficha da máquina".
INFO_CHOICE = "info"
# Returned when the user picks "desfazer ajustes" (reverts every applied tweak).
UNDO_CHOICE = "undo"
# Returned on ESC/Q: leave without running anything.
EXIT_CHOICE = "exit"
_OPTIONS = tuple(LEVEL_ORDER) + (INFO_CHOICE, UNDO_CHOICE)
REVERT_HINT = f"opção 6 do menu ou `{cli_command()} undo --all`"
_DIGIT_KEYS = tuple(str(i) for i in range(1, len(_OPTIONS) + 1))
_PREVIEW_LIMIT = 30
PREFETCH_WARNING = (
    "[warning]Prefetch será limpo: o Windows recria automaticamente, "
    "mas isso pode afetar o próximo boot.[/warning]"
)


def _is_interactive_terminal() -> bool:
    """Checks whether the session is running in an interactive TTY console."""
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def _read_menu_key() -> str:
    """Reads a single key for menu navigation (up, down, enter, esc, p, or a 1-6 option number)."""
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
        "STAGE 2: MEDIANA (BOOST)",
        "STAGE 3: ALTA (TURBO BOOST)",
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

    extras = [
        ("VER FICHA DA MÁQUINA", "Windows, CPU, RAM, GPU, disco e tipo (notebook/desktop)"),
        ("DESFAZER AJUSTES", "Restaura o valor original de cada ajuste já aplicado"),
    ]
    for offset, (title, description) in enumerate(extras):
        idx = len(LEVEL_ORDER) + offset
        num = idx + 1
        if selected_idx == idx:
            lines.append(f"[bold success]► [{num}] {title}[/bold success]")
            lines.append(f"    [bold warning]{description}[/bold warning]")
        else:
            lines.append(f"  [dim] [{num}] {title}[/dim]")
            lines.append(f"    [dim]{description}[/dim]")
        if offset < len(extras) - 1:
            lines.append("")

    subtitle = (
        f"[bold accent][↑/↓] Navegar  [1-{len(_OPTIONS)}] Direto  "
        f"[P] Tema: {pal_name}  [ENTER] Confirmar[/bold accent]"
    )
    # Wide enough for the legend: palettes with long names would otherwise get it cropped.
    subtitle_width = Text.from_markup(subtitle).cell_len + 6
    return Panel(
        "\n".join(lines),
        title="[bold accent]╔═ SELECT OPTIMIZATION STAGE ═╗[/bold accent]",
        subtitle=subtitle,
        box=box.DOUBLE,
        border_style="accent",
        padding=(1, 3),
        expand=False,
        width=max(79, subtitle_width),
    )


def display_level_menu(console: Console):
    """Shows the 4 levels plus 'ver ficha' and 'desfazer ajustes' with arrow / number key navigation.

    Returns the chosen level id, INFO_CHOICE (machine spec sheet), UNDO_CHOICE (revert tweaks)
    or EXIT_CHOICE (ESC/Q).
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
            return EXIT_CHOICE


def display_level_summary(
    console: Console, level_id, clean_paths, applicable_ids, skipped_ids, clean_commands=(), machine_notes=(),
):
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
    ]
    if clean_commands:
        labels = [cleaner.COMMAND_CLEANUPS[c][0] for c in clean_commands]
        lines.append("[bold accent]Caches/Lixeira:[/bold accent] " + ", ".join(labels))
        if "recycle-bin" in clean_commands:
            lines.append(
                "[warning]Lixeira será esvaziada de vez (todas as unidades, inclusive D: e OneDrive): "
                "os arquivos não poderão ser restaurados.[/warning]")
    if "Prefetch" in clean_paths:
        lines.append(PREFETCH_WARNING)
    lines += ["", "[bold accent]Ajustes a aplicar:[/bold accent]"]

    preview = preview_tweak_items(applicable_ids)
    for tweak_id in applicable_ids:
        lines.append(f"  [bold warning]⚡ {tweaks_catalog.get_tweak(tweak_id).label}[/bold warning]")
        names = preview.get(tweak_id, ())
        lines += [f"      [dim]• {escape(name)}[/dim]" for name in names[:_PREVIEW_LIMIT]]
        if len(names) > _PREVIEW_LIMIT:
            lines.append(f"      [dim]... e mais {len(names) - _PREVIEW_LIMIT}[/dim]")
    if not applicable_ids:
        lines.append("  [dim](nenhum)[/dim]")
    else:
        lines.append("")
        lines.append(f"[dim]Reversível: {REVERT_HINT}[/dim]")
        if any(t in applicable_ids for t in ("startup_apps", "third_party_services", "third_party_tasks")):
            lines.append("[dim]Preservados: itens do Windows, antivírus, drivers, VPN, bancos de dados, backup, "
                         "licenças e atualizadores reconhecidos.[/dim]")
        if "hibernation" in applicable_ids:
            lines.append("[warning]Hibernação off: apaga o hiberfil.sys e perde hibernação/inicialização rápida.[/warning]")

    lines += ["", "[dim]Um ponto de restauração é criado antes; se falhar, a missão continua com um aviso.[/dim]"]

    if skipped_ids:
        lines.append("")
        lines.append("[warning]Pulados (requer Administrador):[/warning]")
        for tweak_id in skipped_ids:
            lines.append(f"  [warning]• {tweaks_catalog.get_tweak(tweak_id).label}[/warning]")

    if machine_notes:
        lines.append("")
        lines.append("[accent]Fora deste nível nesta máquina:[/accent]")
        lines += [f"  [dim]• {escape(note)}[/dim]" for note in machine_notes]

    briefing_panel = Panel("\n".join(lines), box=box.DOUBLE, border_style="accent", expand=False, padding=(1, 3))
    console.print(briefing_panel)
    return Confirm.ask("[bold success]Iniciar missão?[/bold success]", default=True)


def display_driver_confirm(console: Console):
    """Asks before the driver step; declining (the default) leaves drivers untouched."""
    console.print(
        "\n[warning]Drivers: busca no Windows Update e na NVIDIA e instala o que estiver pendente. "
        "O driver NVIDIA baixa cerca de 1 GB, a tela pode piscar e pode ser preciso reiniciar.[/warning]"
    )
    return Confirm.ask("[bold success]Atualizar drivers também?[/bold success]", default=False)


def display_clean_confirm(console: Console, paths):
    """Lists the folders about to be cleaned and asks for confirmation."""
    lines = ["[bold accent]Pastas a limpar:[/bold accent] " + (", ".join(sorted(paths)) or "nenhuma")]
    if "Prefetch" in paths:
        lines.append(PREFETCH_WARNING)
    console.print(Panel("\n".join(lines), box=box.DOUBLE, border_style="accent", expand=False, padding=(1, 3)))
    return Confirm.ask("[bold success]Limpar agora?[/bold success]", default=False)
