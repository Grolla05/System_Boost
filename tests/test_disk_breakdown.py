from io import StringIO
from rich.console import Console

from frontend import palettes
from frontend.components import disk_breakdown


def test_render_disk_breakdown_with_data():
    sizes = {
        "User Temp": 1024 * 1024 * 250,      # 250 MB
        "System Temp": 1024 * 1024 * 750,    # 750 MB
    }
    panel = disk_breakdown.create_disk_breakdown_panel(sizes)

    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=palettes.get_theme("dmg"))
    console.print(panel)
    text = out.getvalue()

    assert "User Temp" in text
    assert "System Temp" in text
    assert "25%" in text or "25.0%" in text
    assert "75%" in text or "75.0%" in text
    assert "1.00 GB" in text or "1,000" in text or "1000" in text or "GB" in text


def test_render_disk_breakdown_empty():
    sizes = {
        "User Temp": 0,
        "System Temp": 0,
    }
    panel = disk_breakdown.create_disk_breakdown_panel(sizes)

    out = StringIO()
    console = Console(file=out, width=100, force_terminal=False, theme=palettes.get_theme("dmg"))
    console.print(panel)
    text = out.getvalue()

    assert "0 B" in text or "0.00" in text or "vazio" in text.lower() or "0%" in text


def test_measure_paths_sizes(tmp_path):
    d1 = tmp_path / "temp1"
    d1.mkdir()
    f1 = d1 / "file1.bin"
    f1.write_bytes(b"x" * 1024)

    d2 = tmp_path / "temp2"
    d2.mkdir()
    f2 = d2 / "file2.bin"
    f2.write_bytes(b"y" * 2048)

    paths = {"Path 1": str(d1), "Path 2": str(d2)}
    measured = disk_breakdown.measure_paths_sizes(paths)
    assert measured["Path 1"] == 1024
    assert measured["Path 2"] == 2048

