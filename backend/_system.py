"""Absolute paths to Windows tools. This process is usually elevated, so a bare "sc" must never
be resolved: Windows would look in the working directory and on the user's PATH first."""
import ctypes
import os

_MAX_PATH = 260


def _system_directory():
    """Asks Windows for System32 instead of trusting %SystemRoot%, which the environment can change."""
    buffer = ctypes.create_unicode_buffer(_MAX_PATH)
    if not ctypes.windll.kernel32.GetSystemDirectoryW(buffer, _MAX_PATH):
        raise OSError("GetSystemDirectoryW falhou")
    return buffer.value


def system_exe(name):
    """Returns the full path of a System32 tool, e.g. system_exe('sc') -> ...\\System32\\sc.exe."""
    return os.path.join(_system_directory(), f"{name}.exe")


def powershell_exe():
    """Returns the full path of Windows PowerShell."""
    return os.path.join(_system_directory(), "WindowsPowerShell", "v1.0", "powershell.exe")
