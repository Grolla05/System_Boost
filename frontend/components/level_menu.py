from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
from rich.table import Table

from backend.profiles import LEVEL_ORDER, LEVELS
from backend.tweaks import catalog as tweaks_catalog


def display_level_menu(console: Console):
    """Shows the 4 optimization levels and prompts for a numbered choice, returning the chosen level id."""
    console.clear()
    table = Table(title="Escolha o nível de otimização")
    table.add_column("#", justify="center", style="accent")
    table.add_column("Nível")
    table.add_column("Descrição")

    for i, level_id in enumerate(LEVEL_ORDER, start=1):
        level = LEVELS[level_id]
        table.add_row(str(i), level["label"], level["description"])

    console.print(table)
    choice = IntPrompt.ask(
        "Digite o número do nível desejado",
        choices=[str(i) for i in range(1, len(LEVEL_ORDER) + 1)],
    )
    return LEVEL_ORDER[choice - 1]


def display_level_summary(console: Console, level_id, clean_paths, applicable_ids, skipped_ids):
    """Shows what the chosen level will do and asks the user to confirm before running it."""
    level = LEVELS[level_id]
    lines = [f"[bold accent]{level['label']}[/bold accent]", ""]

    lines.append("Pastas a limpar: " + (", ".join(sorted(clean_paths)) if clean_paths else "nenhuma"))
    lines.append("")
    lines.append("Ajustes a aplicar:")
    for tweak_id in applicable_ids:
        lines.append(f"  - {tweaks_catalog.get_tweak(tweak_id).label}")
    if not applicable_ids:
        lines.append("  (nenhum)")

    if skipped_ids:
        lines.append("")
        lines.append("[warning]Pulados (requer Administrador):[/warning]")
        for tweak_id in skipped_ids:
            lines.append(f"  - {tweaks_catalog.get_tweak(tweak_id).label}")

    console.print(Panel("\n".join(lines), border_style="accent", expand=False, padding=(1, 2)))
    return Confirm.ask("Prosseguir?", default=True)
