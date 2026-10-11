import os
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, ProgressColumn
from rich.text import Text
from .retro_sprite import get_sprite_frame
from ._terminal import clear_screen

class RetroSpriteColumn(ProgressColumn):
    """Animates an 8-bit sprite based on processed item count."""
    def render(self, task):
        frame = get_sprite_frame(int(task.completed))
        return Text(f"[{frame}]", style="bold success")

def run_cleanup_with_loading(console: Console, paths, clean_func, format_func, dry_run=False):
    """Executes the cleanup process with a unified loading screen."""
    clear_screen(console)
    console.print("\n" * (console.height // 3))
    
    total_files = 0
    for path in paths.values():
        try:
            if os.path.exists(path):
                total_files += len(list(os.scandir(path)))
        except:
            pass

    results = []
    total_freed = 0
    
    console.print("[bold accent]╔═[ PURGING UNNECESSARY SECTORS ]═╗[/bold accent]\n")

    with Progress(
        RetroSpriteColumn(),
        TextColumn("[bold accent]ENERGY:[bold accent]"),
        BarColumn(bar_width=32, style="dim", complete_style="success"),
        TaskProgressColumn(text_format="[bold warning]{task.percentage:>3.0f}%[/bold warning]"),
        TextColumn("[dim]► {task.description}[/dim]"),
        console=console,
        transient=True
    ) as progress:
        
        label = "Analisando arquivos (dry-run)..." if dry_run else "Limpando arquivos desnecessários..."
        main_task = progress.add_task(label, total=max(1, total_files))

        for name, path in paths.items():
            def update_progress(n):
                progress.update(main_task, advance=n)

            bytes_freed = clean_func(path, update_progress, dry_run=dry_run)
            results.append((name, format_func(bytes_freed)))
            total_freed += bytes_freed
            
    return results, format_func(total_freed), total_freed
