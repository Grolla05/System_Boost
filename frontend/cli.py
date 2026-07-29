from rich.console import Console
from rich.theme import Theme
from .components.welcome import display_welcome_screen
from .components.loading import run_cleanup_with_loading
from .components.completion import display_completion_screen

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
