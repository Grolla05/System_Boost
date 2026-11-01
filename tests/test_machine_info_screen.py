from io import StringIO
from unittest.mock import patch
from rich.console import Console

from backend.hardware import MachineInfo
from frontend import cli
from frontend.components import machine_info


def test_display_machine_info_centered_with_wait():
    out = StringIO()
    console = Console(file=out, width=100, height=30, force_terminal=False, theme=cli.custom_theme)

    with patch("frontend.components.machine_info._read_single_key"):
        machine_info.display_machine_info(
            console, MachineInfo(windows="Windows 11 Pro", cpu="Core i7"), wait=True
        )

    text = out.getvalue()
    assert "Windows 11 Pro" in text
    assert "Core i7" in text
    assert "voltar ao menu" in text.lower()
    # Checks vertical newline padding when wait=True
    assert text.startswith("\n")

