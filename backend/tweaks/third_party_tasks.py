"""Reversible tweak: disables third-party scheduled tasks (tasks outside \\Microsoft\\)."""
import json
import subprocess

from backend._powershell import PS_PRELUDE, PowerShellError, run_powershell
from backend.logger import get_logger

from . import third_party
from .base import Tweak

log = get_logger("tweaks.third_party_tasks")

# Tasks outside \Microsoft\ that aren't disabled. @() + InputObject keeps the JSON an array
# even for zero or one task (Windows PowerShell 5.1 has no -AsArray).
_DISCOVER_SCRIPT = (
    PS_PRELUDE
    + "$t=@(Get-ScheduledTask | Where-Object { $_.TaskPath -notlike '\\Microsoft\\*' -and $_.State -ne 'Disabled' }"
    + " | ForEach-Object { [pscustomobject]@{ task=($_.TaskPath + $_.TaskName);"
    + " command=[Environment]::ExpandEnvironmentVariables([string]($_.Actions | Select-Object -First 1).Execute) } });"
    + " ConvertTo-Json -InputObject $t -Compress"
)


def discover_tasks():
    """Lists non-Microsoft enabled scheduled tasks as [{'task': full path, 'command': executable}]."""
    try:
        output = run_powershell(_DISCOVER_SCRIPT, timeout=60)
    except PowerShellError as exc:
        log.warning("tarefas agendadas: não foi possível listar: %s", exc)
        return []
    if not output:
        return []
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        log.warning("tarefas agendadas: resposta inválida: %s", exc)
        return []
    if isinstance(data, dict):
        data = [data]
    return [{"task": str(t.get("task", "")), "command": str(t.get("command") or "")} for t in data]


def set_task_enabled(task, enabled):
    """Runs schtasks /Change to enable or disable the task; raises OSError on failure."""
    flag = "/Enable" if enabled else "/Disable"
    result = subprocess.run(["schtasks", "/Change", "/TN", task, flag], capture_output=True, check=False)
    log.debug("schtasks /Change %s %s: returncode=%s", task, flag, result.returncode)
    if result.returncode != 0:
        raise OSError(f"schtasks /Change {task} {flag} retornou {result.returncode}")


class ThirdPartyTasksTweak(Tweak):
    """Disables third-party scheduled tasks; undo re-enables only the ones it disabled."""

    id = "third_party_tasks"
    label = "Tarefas agendadas de terceiros: desativar"
    description = "Desativa tarefas agendadas de terceiros que rodam sozinhas em segundo plano (tarefas do Windows são preservadas)."
    requires_admin = True

    def _candidates(self):
        return [
            t for t in discover_tasks()
            if third_party.is_third_party(t["task"].rsplit("\\", 1)[-1], t["command"])
        ]

    def get_current_value(self):
        """Returns the JSON-safe list of tasks apply() would disable."""
        return [{"task": t["task"]} for t in self._candidates()]

    def apply(self):
        """Disables each candidate task; returns the tasks actually changed."""
        changed = []
        for task in self._candidates():
            try:
                set_task_enabled(task["task"], False)
            except OSError as exc:
                log.warning("tarefa '%s': não foi possível desativar: %s", task["task"], exc)
                continue
            log.info("tarefa '%s': desativada", task["task"])
            changed.append({"task": task["task"]})
        return changed

    def undo(self, previous_value):
        """Re-enables each task that apply() disabled."""
        for task in previous_value or []:
            try:
                set_task_enabled(task["task"], True)
            except OSError as exc:
                log.warning("tarefa '%s': não foi possível reativar: %s", task["task"], exc)
        return previous_value
