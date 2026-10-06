"""Shared fixtures for backend/tweaks tests: fake winreg and fake subprocess.run."""
import pytest


class FakeWinReg:
    """In-memory stand-in for the stdlib winreg module, keyed by (hive, path)."""

    HKEY_LOCAL_MACHINE = "HKLM"
    HKEY_CURRENT_USER = "HKCU"
    REG_DWORD = 4
    KEY_SET_VALUE = 0x0002
    KEY_READ = 0x20019

    def __init__(self):
        """Creates an empty in-memory registry store."""
        self._store = {}  # (hive, path) -> {value_name: value}

    def OpenKey(self, hive, path, *args, **kwargs):
        """Returns a handle if (hive, path) exists, else raises FileNotFoundError."""
        key = (hive, path)
        if key not in self._store:
            raise FileNotFoundError(f"key not found: {path}")
        return key

    def CreateKeyEx(self, hive, path, *args, **kwargs):
        """Returns a handle, creating the (hive, path) entry if it's missing."""
        key = (hive, path)
        self._store.setdefault(key, {})
        return key

    def CloseKey(self, handle):
        """No-op for the fake — nothing to release."""

    def QueryValueEx(self, handle, value_name):
        """Returns (value, type) for value_name, raising FileNotFoundError if absent."""
        values = self._store.get(handle, {})
        if value_name not in values:
            raise FileNotFoundError(f"value not found: {value_name}")
        return values[value_name], self.REG_DWORD

    def SetValueEx(self, handle, value_name, reserved, type_, value):
        """Sets value_name under handle to value."""
        self._store.setdefault(handle, {})[value_name] = value

    def DeleteValue(self, handle, value_name):
        """Deletes value_name under handle, raising FileNotFoundError if absent."""
        values = self._store.get(handle, {})
        if value_name not in values:
            raise FileNotFoundError(f"value not found: {value_name}")
        del values[value_name]

    def seed(self, hive, path, value_name, value):
        """Test helper: pre-populates a value as if it already existed in the registry."""
        self._store.setdefault((hive, path), {})[value_name] = value

    def has_value(self, hive, path, value_name):
        """Test helper: reports whether value_name currently exists under (hive, path)."""
        return value_name in self._store.get((hive, path), {})


@pytest.fixture
def fake_winreg():
    """A fresh, isolated FakeWinReg instance for each test."""
    return FakeWinReg()


class FakeCompletedProcess:
    """Minimal stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode=0, stdout=b""):
        """Stores the scripted returncode and stdout for this fake result."""
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = b""


class FakeSubprocessRun:
    """Records every subprocess.run call and returns a scripted response."""

    def __init__(self):
        """Starts with no recorded calls and a successful (0) default returncode."""
        self.calls = []
        self.returncode = 0
        self.stdout = b""

    def __call__(self, cmd, **kwargs):
        """Records cmd and returns the currently-scripted FakeCompletedProcess."""
        self.calls.append(cmd)
        return FakeCompletedProcess(returncode=self.returncode, stdout=self.stdout)


@pytest.fixture
def fake_run():
    """A fresh FakeSubprocessRun recorder for each test."""
    return FakeSubprocessRun()
