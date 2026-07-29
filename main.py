import argparse
import sys

from backend.privileges import is_admin
from backend.cleaner import get_temp_paths, clean_directory, format_size
from frontend.cli import console, show_welcome, show_loading, show_completion

PATH_CHOICES = ("User Temp", "System Temp", "Prefetch")


def parse_args():
    parser = argparse.ArgumentParser(description="WinCleaner - limpeza de arquivos temporários do Windows")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Simula a limpeza sem apagar nada")
    parser.add_argument("--paths", nargs="+", choices=PATH_CHOICES, help="Restringe a limpeza a pastas específicas")
    parser.add_argument("-y", "--yes", action="store_true", help="Pula telas de confirmação (uso automatizado)")
    parser.add_argument("--no-close", action="store_true", help="Não fecha o terminal ao final")
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Welcome Screen
    show_welcome(skip_wait=args.yes)

    # 2. Setup behind the scenes
    admin_status = is_admin()
    all_paths = get_temp_paths()

    if not admin_status:
        paths_to_clean = {k: v for k, v in all_paths.items() if k == "User Temp"}
    else:
        paths_to_clean = all_paths

    if args.paths:
        paths_to_clean = {k: v for k, v in paths_to_clean.items() if k in args.paths}

    if "Prefetch" in paths_to_clean and not args.yes:
        console.print(
            "[warning]Prefetch será limpo — o Windows recria automaticamente, "
            "mas isso pode afetar o próximo boot.[/warning]"
        )

    # 3. Loading Screen & Cleanup
    results, total_formatted, total_bytes = show_loading(
        paths_to_clean, clean_directory, format_size, dry_run=args.dry_run
    )

    # 4. Completion Screen
    close_terminal = not (args.no_close or args.dry_run or args.yes)
    show_completion(total_formatted, dry_run=args.dry_run, close_terminal=close_terminal, skip_wait=args.yes)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user.")
        sys.exit(0)
