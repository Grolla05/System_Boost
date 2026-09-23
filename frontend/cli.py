from rich.console import Console
from rich.theme import Theme
from .components.welcome import display_welcome_screen
from .components.loading import run_cleanup_with_loading
from .components.completion import display_completion_screen
from .components.tweak_list import display_tweak_list
from .components.tweak_result import display_tweak_success, display_tweak_error, display_undo_all_results
from .components.level_menu import display_level_menu, display_level_summary
from .components.level_completion import display_level_completion

# Apple-like theme: Monochromatic with a blue accent
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "red",
    "success": "bold green",
    "accent": "bold blue",
    "header": "bold white on blue",
})

console = Console(theme=custom_theme)

def show_welcome(skip_wait=False):
    display_welcome_screen(console, skip_wait=skip_wait)

def show_loading(paths, clean_func, format_func, dry_run=False):
    return run_cleanup_with_loading(console, paths, clean_func, format_func, dry_run=dry_run)

def show_completion(total_formatted, dry_run=False, close_terminal=True, skip_wait=False):
    display_completion_screen(console, total_formatted, dry_run=dry_run, close_terminal=close_terminal, skip_wait=skip_wait)

def show_tweak_list(statuses):
    display_tweak_list(console, statuses)

def show_tweak_success(message):
    display_tweak_success(console, message)

def show_tweak_error(message):
    display_tweak_error(console, message)

def show_undo_all_results(results):
    display_undo_all_results(console, results)

def show_level_menu():
    return display_level_menu(console)

def show_level_summary(level_id, clean_paths, applicable_ids, skipped_ids):
    return display_level_summary(console, level_id, clean_paths, applicable_ids, skipped_ids)

def show_level_completion(level_label, total_formatted, tweak_results, close_terminal=True, skip_wait=False):
    return display_level_completion(
        console, level_label, total_formatted, tweak_results,
        close_terminal=close_terminal, skip_wait=skip_wait,
    )
