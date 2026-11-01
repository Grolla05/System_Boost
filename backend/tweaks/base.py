"""Base abstraction all reversible tweaks implement."""
from abc import ABC, abstractmethod


class TweakError(Exception):
    """Raised when a tweak can't be looked up, read, applied, or undone."""


class TweakAlreadyApplied(TweakError):
    """Raised when apply is requested for a tweak whose applied state is already recorded."""


class TweakPartialUndo(TweakError):
    """Raised by undo() when some items were not restored; remaining holds them for a later retry."""

    def __init__(self, remaining):
        self.remaining = remaining
        names = ", ".join(str(item.get("name") or item.get("task") or item) for item in remaining)
        super().__init__(f"{len(remaining)} item(ns) não restaurado(s): {names}")


class Tweak(ABC):
    """Common interface every reversible Windows tweak must implement."""

    id = None
    label = None
    description = None
    requires_admin = False
    previews_items = False  # True: get_current_value() lists the items apply() would change

    @abstractmethod
    def get_current_value(self):
        """Reads and returns the tweak's current value from Windows."""

    @abstractmethod
    def apply(self):
        """Applies the tweak's target state and returns the value that was set."""

    @abstractmethod
    def undo(self, previous_value):
        """Restores previous_value, reversing a prior apply()."""
