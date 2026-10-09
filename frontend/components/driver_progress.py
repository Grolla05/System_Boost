from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


def run_driver_update_with_progress(console: Console, update_func, dry_run=False):
    """Runs update_func(progress_callback=, on_scan=, dry_run=) under a spinner/bar and prints results.

    Returns (results, reboot_required) exactly as update_func produced them.
    """
    label = "Buscando drivers (dry-run)..." if dry_run else "Buscando drivers no Windows Update..."

    with Progress(
        TextColumn("[bold #9bbc0f]DRIVERS:[bold #9bbc0f]"),
        BarColumn(bar_width=35, style="#306230", complete_style="bold #9bbc0f"),
        TaskProgressColumn(text_format="[bold #cadc9f]{task.percentage:>3.0f}%[/bold #cadc9f]"),
        TextColumn("[dim #8bac0f]► {task.description}[/dim #8bac0f]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(label, total=None)

        def on_scan(total):
            progress.update(task, total=max(1, total), completed=0)

        def on_item(title):
            progress.update(task, description=f"Atualizando: {title[:50]}", advance=1)

        results, reboot_required = update_func(
            progress_callback=on_item, on_scan=on_scan, dry_run=dry_run
        )

    return results, reboot_required


def format_driver_summary(results, reboot_required=False):
    """Rich-markup block for the final screens: counts, plus per-driver lines for skips/failures."""
    if not results:
        return "[white]Drivers: nenhuma atualização pendente[/white]"
    updated = [r for r in results if r[1] is True]
    skipped = [r for r in results if r[1] is None]
    failed = [r for r in results if r[1] is False]

    lines = [f"[white]{len(updated)} driver(s) atualizado(s)[/white]"]
    for title, _, note in skipped:
        lines.append(f"[warning]{title}: {note}[/warning]")
    for title, _, note in failed:
        lines.append(f"[danger]{title}: {note}[/danger]")
    if reboot_required:
        lines.append("[warning]Reinicie o computador para concluir os drivers[/warning]")
    return "\n".join(lines)
