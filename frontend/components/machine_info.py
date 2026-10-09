from rich import box
from rich.console import Console
from rich.table import Table

from ._terminal import _read_single_key, clear_screen

_UNKNOWN = "[dim]desconhecido[/dim]"


def _or_unknown(value):
    return str(value) if value else _UNKNOWN


def _format_ram(ram_gb):
    if not ram_gb:
        return _UNKNOWN
    return f"{int(ram_gb)} GB" if float(ram_gb).is_integer() else f"{ram_gb:.1f} GB"


def _format_windows(info):
    if not info.windows:
        return _UNKNOWN
    parts = [info.windows]
    if info.version:
        parts.append(info.version)
    text = " ".join(parts)
    return f"{text} (compilação {info.build})" if info.build else text


def _format_cpu(info):
    if not info.cpu:
        return _UNKNOWN
    return f"{info.cpu} ({info.threads} threads)" if info.threads else info.cpu


def _format_disk(info):
    if not (info.disk_type or info.disk_model):
        return _UNKNOWN
    kind = info.disk_type or "tipo desconhecido"
    if info.disk_bus:
        kind = f"{kind} {info.disk_bus}"
    return f"{kind} — {info.disk_model}" if info.disk_model else kind


def display_machine_info(console: Console, info, wait=False):
    """Prints the machine's spec sheet; any field that couldn't be read shows 'desconhecido'.

    With wait=True (used when opened from the menu) the screen is cleared first and the sheet
    stays up until a key is pressed, since the menu would otherwise wipe it on its next redraw.
    """
    if wait:
        clear_screen(console)
    table = Table(
        title="[bold #9bbc0f]╔═ A FICHA DA MÁQUINA // CARTRIDGE INFO ═╗[/bold #9bbc0f]",
        show_header=False,
        box=box.DOUBLE,
        border_style="bold #8bac0f",
        padding=(0, 2),
    )
    table.add_column("Item", style="accent")
    table.add_column("Valor")

    table.add_row("Windows", _format_windows(info))
    table.add_row("Processador", _format_cpu(info))
    table.add_row("Memória", _format_ram(info.ram_gb))
    table.add_row("Placa de vídeo", "\n".join(info.gpus) if info.gpus else _UNKNOWN)
    table.add_row("Disco do sistema", _format_disk(info))
    table.add_row("Tipo", _or_unknown(info.form_factor))

    console.print(table)

    if wait:
        console.print("\n[bold #8bac0f]Pressione qualquer tecla para voltar ao menu...[/bold #8bac0f]")
        _read_single_key()
