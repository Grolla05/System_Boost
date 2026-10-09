import sys
from rich.console import Console
from rich.theme import Theme
from .components.welcome import display_welcome_screen
from .components.loading import run_cleanup_with_loading
from .components.completion import display_completion_screen
from .components.tweak_list import display_tweak_list
from .components.tweak_result import display_tweak_success, display_tweak_error, display_undo_all_results
from .components.level_menu import display_level_menu, display_level_summary, INFO_CHOICE
from .components.level_completion import display_level_completion
from .components.driver_progress import run_driver_update_with_progress, format_driver_summary
from .components.machine_info import display_machine_info

from .audio import set_sound_enabled, is_sound_enabled
from .palettes import (
    PALETTES,
    get_theme,
    load_palette,
    save_palette,
    set_current_palette,
    get_current_palette_name,
    cycle_palette as palettes_cycle,
)

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Initialize theme from persisted config or default 'dmg'
_initial_palette = load_palette()
custom_theme = get_theme(_initial_palette)
console = Console(theme=custom_theme)


def apply_palette(palette_name: str):
    """Changes active console theme and saves choice."""
    if palette_name in PALETTES:
        save_palette(palette_name)
        console.push_theme(get_theme(palette_name))


def cycle_active_palette() -> str:
    """Cycles to the next palette and updates the console."""
    next_pal = palettes_cycle()
    console.push_theme(get_theme(next_pal))
    return next_pal

def show_welcome(skip_wait=False):
    display_welcome_screen(console, skip_wait=skip_wait)

def show_loading(paths, clean_func, format_func, dry_run=False):
    return run_cleanup_with_loading(console, paths, clean_func, format_func, dry_run=dry_run)

def show_completion(total_formatted, dry_run=False, close_terminal=True, skip_wait=False, driver_summary=None):
    display_completion_screen(
        console, total_formatted, dry_run=dry_run, close_terminal=close_terminal,
        skip_wait=skip_wait, driver_summary=driver_summary,
    )

def show_tweak_list(statuses):
    display_tweak_list(console, statuses)

def show_tweak_success(message):
    display_tweak_success(console, message)

def show_tweak_error(message):
    display_tweak_error(console, message)

def show_undo_all_results(results):
    display_undo_all_results(console, results)

def show_machine_info(info, wait=False):
    display_machine_info(console, info, wait=wait)

def show_level_menu():
    return display_level_menu(console)

def show_level_summary(level_id, clean_paths, applicable_ids, skipped_ids):
    return display_level_summary(console, level_id, clean_paths, applicable_ids, skipped_ids)

def show_driver_update(update_func, dry_run=False):
    return run_driver_update_with_progress(console, update_func, dry_run=dry_run)

def show_level_completion(level_label, total_formatted, tweak_results, close_terminal=True, skip_wait=False, driver_summary=None):
    return display_level_completion(
        console, level_label, total_formatted, tweak_results,
        close_terminal=close_terminal, skip_wait=skip_wait, driver_summary=driver_summary,
    )
