from unittest.mock import patch
from frontend import palettes


def test_all_palettes_exist():
    expected = {"dmg", "pocket", "arcade", "amber", "matrix"}
    assert expected.issubset(set(palettes.PALETTES.keys()))


def test_get_theme_returns_valid_rich_theme():
    for name in palettes.PALETTES:
        theme = palettes.get_theme(name)
        assert "accent" in theme.styles
        assert "header" in theme.styles
        assert "success" in theme.styles
        assert "warning" in theme.styles
        assert "danger" in theme.styles


def test_cycle_palette():
    p1 = palettes.get_current_palette_name()
    p2 = palettes.cycle_palette()
    assert p1 != p2
    assert p2 in palettes.PALETTES


def test_save_and_load_palette_config(tmp_path):
    config_file = tmp_path / "ui_config.json"
    with patch("frontend.palettes.CONFIG_PATH", config_file):
        palettes.save_palette("matrix")
        assert palettes.load_palette() == "matrix"
        assert palettes.get_current_palette_name() == "matrix"

