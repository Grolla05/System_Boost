"""Live mission log: one line per step with its running / OK / FAIL / SKIP state."""
import time
from dataclasses import dataclass
from typing import Optional

from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from ._terminal import clear_screen

_SPINNER = "|/-\\"

# status -> (tag, rich style)
_TAGS = {
    "ok": ("[ OK ]", "success"),
    "already": ("[ OK ]", "dim"),
    "fail": ("[FAIL]", "danger"),
    "skip": ("[SKIP]", "warning"),
}

# Panel borders (2) + title/padding rows kept free so a cropped log never overflows the screen.
_CHROME_ROWS = 6


@dataclass
class LogLine:
    key: Optional[str]
    text: str
    status: str  # running | ok | already | fail | skip
    note: Optional[str] = None
    indent: bool = False


class MissionLog:
    """Collects steps and renders them live; the whole log stays on screen when it ends."""

    def __init__(self, console: Console, title: str, keep=False):
        self.console = console
        self.title = title
        self.keep = keep  # True: print the full log after it ends instead of leaving a clean screen
        self.lines = []
        self._live = None

    # --- state -----------------------------------------------------------------
    def _find(self, key):
        for line in self.lines:
            if line.key == key:
                return line
        return None

    def start(self, key, text):
        """Adds a step in the 'running' state."""
        self.lines.append(LogLine(key, text, "running"))

    def finish(self, key, status, note=None, text=None):
        """Sets a step's final status (ok | already | fail | skip); creates the line if it never started."""
        line = self._find(key)
        if line is None:
            self.lines.append(LogLine(key, text or str(key), status, note))
            return
        line.status = status
        line.note = note
        if text:
            line.text = text

    def item(self, text, status="ok", note=None):
        """Adds an indented sub-line (one affected item) under the current step."""
        self.lines.append(LogLine(None, text, status, note, indent=True))

    def is_running(self, key):
        line = self._find(key)
        return line is not None and line.status == "running"

    # --- rendering ---------------------------------------------------------------
    def _render_line(self, line):
        if line.status == "running":
            tag = f"[ {_SPINNER[int(time.monotonic() * 8) % len(_SPINNER)]}  ]"
            style = "accent"
        else:
            tag, style = _TAGS[line.status]
        text = Text()
        if line.indent:
            text.append("         └ ", style="dim")
            text.append(line.text)
        else:
            text.append(tag, style=style)
            text.append(" " + line.text)
        if line.note:
            text.append(f"  — {line.note}", style="dim")
        return text

    def render(self, max_height=None):
        """Builds the panel; with max_height it shows only the newest lines that fit."""
        lines = self.lines
        hidden = 0
        if max_height is not None:
            capacity = max(3, max_height - _CHROME_ROWS)
            if len(lines) > capacity:
                hidden = len(lines) - (capacity - 1)
                lines = lines[hidden:]
        body = Text()
        if hidden:
            body.append(f"... {hidden} linha(s) anterior(es)\n", style="dim")
        for i, line in enumerate(lines):
            if i:
                body.append("\n")
            body.append_text(self._render_line(line))
        if not self.lines:
            body.append("aguardando...", style="dim")
        return Panel(
            body,
            width=min(76, max(40, self.console.width - 4)),
            title=f"[bold accent]MISSION LOG // {self.title}[/bold accent]",
            box=box.DOUBLE, border_style="accent", padding=(0, 2),
        )

    # --- live display ------------------------------------------------------------
    def __enter__(self):
        clear_screen(self.console)
        self._live = Live(
            get_renderable=lambda: Align.center(
                self.render(self.console.height), vertical="middle", height=max(1, self.console.height - 1),
            ),
            console=self.console, refresh_per_second=10, transient=True,
        )
        self._live.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            for line in self.lines:
                if line.status == "running":
                    line.status = "fail"
                    line.note = "interrompido"
        self._live.stop()
        self._live = None
        if self.keep:
            self.console.print(self.render(None))
        return False
