"""Retro 8-bit color palettes and theme management for System Boost."""
import json
import os
from pathlib import Path
from rich.theme import Theme

LOCAL_APPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
CONFIG_DIR = Path(LOCAL_APPDATA) / "WinCleaner"
CONFIG_PATH = CONFIG_DIR / "ui_config.json"

PALETTES = {
    "dmg": {
        "name": "Game Boy Classic (DMG-01)",
        "info": "bold #8bac0f",
        "warning": "bold #cadc9f",
        "danger": "bold red",
        "success": "bold #9bbc0f",
        "accent": "bold #8bac0f",
        "header": "bold #0f380f on #8bac0f",
        "dim": "#306230",
        "border": "bold #8bac0f",
        "bar_complete": "bold #9bbc0f",
        "bar_remaining": "#306230",
        "highlight": "bold #9bbc0f",
        "shadow": "#306230",
    },
    "pocket": {
        "name": "Game Boy Pocket (Monochrome)",
        "info": "bold #a0a0a0",
        "warning": "bold #e0e0e0",
        "danger": "bold red",
        "success": "bold #ffffff",
        "accent": "bold #ffffff",
        "header": "bold #000000 on #ffffff",
        "dim": "#555555",
        "border": "bold #aaaaaa",
        "bar_complete": "bold #ffffff",
        "bar_remaining": "#333333",
        "highlight": "bold #ffffff",
        "shadow": "#222222",
    },
    "arcade": {
        "name": "Cyber Arcade 80s (Neon)",
        "info": "bold #00f0ff",
        "warning": "bold #ffe600",
        "danger": "bold red",
        "success": "bold #00ff66",
        "accent": "bold #ff007f",
        "header": "bold white on #ff007f",
        "dim": "#4d0099",
        "border": "bold #00f0ff",
        "bar_complete": "bold #ff007f",
        "bar_remaining": "#1a0033",
        "highlight": "bold #ffe600",
        "shadow": "#2e0854",
    },
    "amber": {
        "name": "Phosphor Amber CRT",
        "info": "bold #ffaa00",
        "warning": "bold #ffd480",
        "danger": "bold red",
        "success": "bold #ff9900",
        "accent": "bold #ff9900",
        "header": "bold #1a0f00 on #ff9900",
        "dim": "#663d00",
        "border": "bold #ff9900",
        "bar_complete": "bold #ffb833",
        "bar_remaining": "#472a00",
        "highlight": "bold #ffe066",
        "shadow": "#331f00",
    },
    "matrix": {
        "name": "Matrix Terminal",
        "info": "bold #00dd33",
        "warning": "bold #99ff99",
        "danger": "bold red",
        "success": "bold #00ff41",
        "accent": "bold #00ff41",
        "header": "bold #002200 on #00ff41",
        "dim": "#004d1a",
        "border": "bold #00ff41",
        "bar_complete": "bold #00ff41",
        "bar_remaining": "#003311",
        "highlight": "bold #b3ffcc",
        "shadow": "#002b0e",
    },
}

PALETTE_ORDER = ("dmg", "pocket", "arcade", "amber", "matrix")
_CURRENT_PALETTE = "dmg"


def get_theme(palette_name: str = "dmg") -> Theme:
    """Returns a rich.theme.Theme corresponding to the given palette name."""
    palette = PALETTES.get(palette_name, PALETTES["dmg"])
    return Theme({
        "info": palette["info"],
        "warning": palette["warning"],
        "danger": palette["danger"],
        "success": palette["success"],
        "accent": palette["accent"],
        "header": palette["header"],
        "dim": palette["dim"],
        "border": palette["border"],
        "highlight": palette["highlight"],
    })


def get_current_palette_name() -> str:
    """Returns the currently active palette key."""
    return _CURRENT_PALETTE


def set_current_palette(palette_name: str):
    """Sets the active palette."""
    global _CURRENT_PALETTE
    if palette_name in PALETTES:
        _CURRENT_PALETTE = palette_name


def cycle_palette() -> str:
    """Cycles to the next palette and returns its name."""
    global _CURRENT_PALETTE
    idx = PALETTE_ORDER.index(_CURRENT_PALETTE) if _CURRENT_PALETTE in PALETTE_ORDER else 0
    next_palette = PALETTE_ORDER[(idx + 1) % len(PALETTE_ORDER)]
    _CURRENT_PALETTE = next_palette
    save_palette(next_palette)
    return next_palette


def load_palette() -> str:
    """Loads saved palette from disk config, or defaults to 'dmg'."""
    global _CURRENT_PALETTE
    try:
        if CONFIG_PATH.is_file():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            saved = data.get("palette")
            if saved in PALETTES:
                _CURRENT_PALETTE = saved
                return saved
    except Exception:
        pass
    _CURRENT_PALETTE = "dmg"
    return "dmg"


def save_palette(palette_name: str):
    """Persists chosen palette to disk config."""
    global _CURRENT_PALETTE
    if palette_name not in PALETTES:
        return
    _CURRENT_PALETTE = palette_name
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps({"palette": palette_name}, indent=2), encoding="utf-8")
    except Exception:
        pass

