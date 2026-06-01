import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

def run_cleanup_with_loading(console: Console, paths, clean_func, format_func):
    """Executes the cleanup process with a unified loading screen."""
    console.clear()
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
    
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[accent]{task.description}"),
        BarColumn(bar_width=40, style="accent", complete_style="accent"),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        
        main_task = progress.add_task("Limpando arquivos desnecessários...", total=max(1, total_files))
        
        for name, path in paths.items():
            def update_progress(n):
                progress.update(main_task, advance=n)
                
            bytes_freed = clean_func(path, update_progress)
            results.append((name, format_func(bytes_freed)))
            total_freed += bytes_freed
            
    return results, format_func(total_freed), total_freed
