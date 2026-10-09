import subprocess

from backend.logger import get_logger

log = get_logger("powershell")

PS_PRELUDE = "[Console]::OutputEncoding=[Text.Encoding]::UTF8;$ErrorActionPreference='Stop';"


class PowerShellError(Exception):
    """Raised when powershell.exe can't run, times out, or exits non-zero."""


def run_powershell(script, timeout):
    """Runs a PowerShell script and returns its stdout, decoded and stripped."""
    log.debug("powershell: executando (timeout=%ss), script=%.200s", timeout, script)
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-Command", script],
            capture_output=True, check=False, timeout=timeout, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        log.error("powershell: timeout após %ss", timeout)
        raise PowerShellError(f"tempo esgotado ({timeout}s) aguardando o PowerShell")
    except OSError as exc:
        log.error("powershell: não executou: %s", exc)
        raise PowerShellError(f"não foi possível executar o PowerShell: {exc}")
    log.debug("powershell: returncode=%s", result.returncode)
    if result.returncode != 0:
        detail = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        log.error("powershell: stderr=%s", detail[:500])
        raise PowerShellError(f"PowerShell retornou {result.returncode}: {detail}"[:300])
    return (result.stdout or b"").decode("utf-8-sig", errors="replace").strip()
