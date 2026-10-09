from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from backend.tweaks import catalog as tweaks_catalog

from ._terminal import _read_single_key, clear_screen

_BACK_HINT = "\n[dim]Pressione qualquer tecla para voltar ao menu...[/dim]"


def _panel(body, title):
    return Panel(
        body, title=f"[bold accent]{title}[/bold accent]", box=box.DOUBLE,
        border_style="accent", expand=False, padding=(1, 3),
    )


def _label(tweak_id):
    try:
        return tweaks_catalog.get_tweak(tweak_id).label
    except Exception:
        return tweak_id


def display_undo_confirm(console: Console, applied, admin):
    """Lists the applied tweaks that will be reverted and asks for confirmation.

    `applied` is [(tweak, record)] from backend.tweaks.list_applied(). Tweaks that need
    Administrator are flagged when the session isn't elevated, since they will fail to revert.
    """
    clear_screen(console)
    lines = [
        f"[bold success]{len(applied)} ajuste(s) aplicado(s) serão revertidos ao valor original:[/bold success]",
        "",
    ]
    for tweak, _record in applied:
        lines.append(f"  [bold warning]⏪ {tweak.label}[/bold warning]")

    needs_admin = [tweak.label for tweak, _ in applied if tweak.requires_admin]
    if needs_admin and not admin:
        lines.append("")
        lines.append("[warning]Sem Administrador, estes não poderão ser desfeitos:[/warning]")
        for label in needs_admin:
            lines.append(f"  [warning]• {label}[/warning]")

    console.print(_panel("\n".join(lines), "╔═ DESFAZER AJUSTES ═╗"))
    return Confirm.ask("[bold success]Reverter agora?[/bold success]", default=True)


def display_undo_empty(console: Console, wait=True):
    """Tells the user there is nothing to revert."""
    clear_screen(console)
    console.print(_panel("[bold warning]Nenhum ajuste aplicado: nada para desfazer.[/bold warning]", "╔═ DESFAZER AJUSTES ═╗"))
    if wait:
        console.print(_BACK_HINT)
        _read_single_key()


def display_undo_results(console: Console, results, wait=True):
    """Shows one line per reverted tweak (OK / FALHA + reason) and a total."""
    clear_screen(console)
    lines = []
    for tweak_id, success, error in results:
        label = _label(tweak_id)
        if success:
            lines.append(f"[success]OK[/success]    {tweak_id}  [dim]{label}[/dim]")
        else:
            lines.append(f"[danger]FALHA[/danger] {tweak_id}: {error}")
    done = sum(1 for _, success, _ in results if success)
    lines.append("")
    lines.append(f"[bold accent]{done} de {len(results)} ajuste(s) desfeito(s)[/bold accent]")

    console.print(_panel("\n".join(lines), "╔═ RESULTADO ═╗"))
    if wait:
        console.print(_BACK_HINT)
        _read_single_key()
