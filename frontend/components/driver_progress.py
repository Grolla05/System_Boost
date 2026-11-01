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
