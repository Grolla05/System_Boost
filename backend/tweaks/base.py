"""Base abstraction all reversible tweaks implement."""
from abc import ABC, abstractmethod


class TweakError(Exception):
    """Raised when a tweak can't be looked up, read, applied, or undone."""


class Tweak(ABC):
    """Common interface every reversible Windows tweak must implement."""

    id = None
    label = None
    description = None
    requires_admin = False

    @abstractmethod
    def get_current_value(self):
        """Reads and returns the tweak's current value from Windows."""

    @abstractmethod
    def apply(self):
        """Applies the tweak's target state and returns the value that was set."""

    @abstractmethod
    def undo(self, previous_value):
        """Restores previous_value, reversing a prior apply()."""
