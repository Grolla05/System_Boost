"""Disk space breakdown and pre-scan visualization panel."""
import os
from rich import box
from rich.panel import Panel

from backend.cleaner import format_size


def measure_paths_sizes(paths: dict) -> dict:
    """Calculates total bytes occupied in each directory, handling errors gracefully."""
    measured = {}
    for name, path in paths.items():
        total = 0
        try:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        try:
                            fp = os.path.join(root, f)
                            total += os.path.getsize(fp)
                        except (OSError, PermissionError):
                            pass
        except Exception:
            pass
        measured[name] = total
    return measured


def create_disk_breakdown_panel(sizes: dict, bar_width: int = 20) -> Panel:
    """Creates a retro 8-bit horizontal bar chart of space distribution across paths."""
    total_bytes = sum(sizes.values())
    lines = [
        "[bold accent]DISTRIBUIÇÃO DE ESPAÇO IDENTIFICADA:[/bold accent]",
        "",
    ]

    for name, size in sizes.items():
        pct = (size / total_bytes * 100.0) if total_bytes > 0 else 0.0
        filled = int(bar_width * pct / 100.0)
        remaining = bar_width - filled
        bar_str = f"[bold success]{'█' * filled}[/bold success][dim]{'░' * remaining}[/dim]"
        formatted_size = format_size(size)
        lines.append(
            f"  [bold]{name:<16}[/bold] : {formatted_size:>9}  [{bar_str}]  {pct:>5.1f}%"
        )

    lines.append("")
    formatted_total = format_size(total_bytes)
    lines.append(f"[bold highlight]TOTAL IDENTIFICADO: {formatted_total}[/bold highlight]")

    return Panel(
        "\n".join(lines),
        title="[bold accent]╔═ DISK LOOT BREAKDOWN // PRE-SCAN ═╗[/bold accent]",
        box=box.DOUBLE,
        border_style="accent",
        padding=(1, 3),
        expand=False,
    )
