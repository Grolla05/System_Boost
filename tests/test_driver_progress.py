import io

from rich.console import Console

from frontend.components.driver_progress import run_driver_update_with_progress


def test_progress_prints_notices_to_the_user():
    console = Console(file=io.StringIO(), force_terminal=False, width=120)

    def update(progress_callback=None, on_scan=None, dry_run=False, on_notice=None):
        on_scan(1)
        on_notice("a tela pode piscar durante a instalação")
        progress_callback("NVIDIA GeForce RTX 4070 → 617.42")
        return [("NVIDIA GeForce RTX 4070 → 617.42", True, "instalado")], False

    results, reboot = run_driver_update_with_progress(console, update)

    assert results[0][1] is True and reboot is False
    assert "a tela pode piscar" in console.file.getvalue()
