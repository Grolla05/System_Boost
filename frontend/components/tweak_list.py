from rich.console import Console
from rich.table import Table


def display_tweak_list(console: Console, statuses):
    """Prints a table of tweaks with id, label, admin requirement, current value, and applied status."""
    table = Table(title="Ajustes disponíveis")
    table.add_column("ID", style="accent")
    table.add_column("Ajuste")
    table.add_column("Admin", justify="center")
    table.add_column("Valor atual")
    table.add_column("Status")

    for tweak, current_value, record in statuses:
        admin_marker = "[warning]sim[/warning]" if tweak.requires_admin else "não"
        status = "[success]aplicado[/success]" if record else "[dim]—[/dim]"
        table.add_row(tweak.id, tweak.label, admin_marker, str(current_value), status)

    console.print(table)
