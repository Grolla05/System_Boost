from rich import box
from rich.console import Console
from rich.table import Table


def display_tweak_list(console: Console, statuses):
    """Prints a table of tweaks with id, label, admin requirement, current value, and applied status."""
    table = Table(
        title="[highlight]╔═ AJUSTES DISPONÍVEIS // TWEAKS INVENTORY ═╗[/highlight]",
        box=box.DOUBLE,
        border_style="border",
    )
    table.add_column("ID", style="accent")
    table.add_column("Ajuste")
    table.add_column("Admin", justify="center")
    table.add_column("Valor atual")
    table.add_column("Status")

    for tweak, current_value, record in statuses:
        admin_marker = "[warning]sim[/warning]" if tweak.requires_admin else "não"
        status = "[success]aplicado[/success]" if record else "[dim]—[/dim]"
        shown = f"{len(current_value)} item(ns)" if isinstance(current_value, list) else str(current_value)
        table.add_row(tweak.id, tweak.label, admin_marker, shown, status)

    console.print(table)
