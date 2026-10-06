import pytest

from backend.tweaks.base import Tweak, TweakError


def test_tweak_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Tweak()


def test_subclass_missing_a_method_cannot_be_instantiated():
    class Incomplete(Tweak):
        def get_current_value(self):
            return None

        def apply(self):
            return None

        # undo() intentionally not implemented

    with pytest.raises(TypeError):
        Incomplete()


def test_tweak_error_is_an_exception():
    assert issubclass(TweakError, Exception)
