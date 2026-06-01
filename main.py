import sys
from backend.privileges import is_admin
from backend.cleaner import get_temp_paths, clean_directory, format_size
from frontend.cli import show_welcome, show_loading, show_completion

def main():
    # 1. Welcome Screen
    show_welcome()
    
    # 2. Setup behind the scenes
    admin_status = is_admin()
    all_paths = get_temp_paths()
    
    if not admin_status:
        paths_to_clean = {k: v for k, v in all_paths.items() if k == "User Temp"}
    else:
        paths_to_clean = all_paths

    # 3. Loading Screen & Cleanup
    results, total_formatted, total_bytes = show_loading(paths_to_clean, clean_directory, format_size)
    
    # 4. Completion Screen
    show_completion(total_formatted)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user.")
        sys.exit(0)
