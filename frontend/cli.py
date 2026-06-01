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

def show_welcome():
    display_welcome_screen(console)

def show_loading(paths, clean_func, format_func):
    return run_cleanup_with_loading(console, paths, clean_func, format_func)

def show_completion(total_formatted):
    display_completion_screen(console, total_formatted)
