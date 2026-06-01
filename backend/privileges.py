import ctypes
import os

def is_admin():
    """Checks if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Fallback for non-Windows systems (though this tool is Windows-specific)
        return os.getuid() == 0 if hasattr(os, 'getuid') else False
