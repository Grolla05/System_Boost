from io import StringIO

from rich.console import Console

from backend.hardware import MachineInfo
from frontend.cli import custom_theme
from frontend.components.machine_info import display_machine_info


def _render(info):
    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=custom_theme)
    display_machine_info(console, info)
    return out.getvalue()


def _full_info(**overrides):
    base = dict(
        windows="Windows 11 Pro", version="23H2", build="22631.4460",
        cpu="AMD Ryzen 5 5600 6-Core Processor", threads=12, ram_gb=16.0,
        gpus=["NVIDIA GeForce RTX 3060"],
        disk_type="SSD", disk_model="Samsung SSD 980", disk_bus="NVMe",
        form_factor="Notebook",
    )
    base.update(overrides)
    return MachineInfo(**base)


def test_renders_every_field():
    text = _render(_full_info())

    assert "Windows 11 Pro" in text
    assert "23H2" in text
    assert "22631.4460" in text
    assert "Ryzen 5 5600" in text
    assert "12" in text
    assert "16 GB" in text
    assert "RTX 3060" in text
    assert "SSD" in text
    assert "Samsung SSD 980" in text
    assert "Notebook" in text
    assert "desconhecido" not in text


def test_unknown_fields_show_desconhecido_and_do_not_crash():
    text = _render(MachineInfo())

    assert "desconhecido" in text
    assert "None" not in text


def test_fractional_ram_keeps_one_decimal():
    assert "15.8 GB" in _render(_full_info(ram_gb=15.8))


def test_multiple_gpus_all_listed():
    text = _render(_full_info(gpus=["Intel(R) UHD Graphics", "NVIDIA GeForce RTX 3060"]))

    assert "UHD Graphics" in text
    assert "RTX 3060" in text


def test_no_gpus_shows_desconhecido():
    assert "desconhecido" in _render(_full_info(gpus=[]))


def test_desktop_label_rendered():
    assert "Desktop" in _render(_full_info(form_factor="Desktop"))
