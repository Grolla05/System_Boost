"""Reversible tweak mechanism for a Windows scheduled task's enabled state."""
import subprocess
import xml.etree.ElementTree as ET

from .base import Tweak, TweakError

_NAMESPACE = "{http://schemas.microsoft.com/windows/2004/02/mit/task}"


class ScheduledTaskTweak(Tweak):
    """Enables/disables a Windows scheduled task via schtasks.exe."""

    def __init__(self, tweak_id, label, description, task_path, requires_admin=True):
        """Stores the task's full path (as schtasks /TN expects it)."""
        self.id = tweak_id
        self.label = label
        self.description = description
        self.task_path = task_path
        self.requires_admin = requires_admin

    def get_current_value(self):
        """Queries the task's XML definition and returns 'Enabled' or 'Disabled'."""
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", self.task_path, "/XML", "ONE"],
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise TweakError(f"Tarefa agendada '{self.task_path}' não encontrada.")
        try:
            # schtasks declares encoding="UTF-16" in the XML prolog, but the bytes
            # captured through a redirected pipe are actually UTF-8 — decode as text
            # ourselves so ET doesn't trust a declaration that doesn't match the bytes.
            xml_text = result.stdout.decode("utf-8")
            root = ET.fromstring(xml_text)
        except (UnicodeDecodeError, ET.ParseError) as exc:
            raise TweakError(f"Não foi possível interpretar a definição da tarefa '{self.task_path}': {exc}") from exc
        enabled = root.find(f".//{_NAMESPACE}Enabled")
        if enabled is None:
            enabled = root.find(".//Enabled")
        if enabled is None:
            return "Enabled"
        return "Enabled" if enabled.text.strip().lower() == "true" else "Disabled"

    def apply(self):
        """Disables the scheduled task."""
        self._set_state("Disabled")
        return "Disabled"

    def undo(self, previous_value):
        """Restores the task's previous enabled/disabled state."""
        self._set_state(previous_value)
        return previous_value

    def _set_state(self, state):
        """Runs schtasks /Change to enable or disable the task."""
        flag = "/Enable" if state == "Enabled" else "/Disable"
        result = subprocess.run(
            ["schtasks", "/Change", "/TN", self.task_path, flag],
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise TweakError(f"Falha ao alterar tarefa '{self.task_path}'.")
