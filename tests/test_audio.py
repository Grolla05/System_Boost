import sys
from unittest.mock import patch, MagicMock

from frontend import audio


def test_sound_toggle():
    audio.set_sound_enabled(True)
    assert audio.is_sound_enabled() is True

    audio.set_sound_enabled(False)
    assert audio.is_sound_enabled() is False
    audio.set_sound_enabled(True)


def test_sound_calls_do_not_raise():
    # Calling all sound triggers should never raise exceptions, even when sound is disabled or enabled
    audio.set_sound_enabled(True)
    with patch("winsound.Beep", side_effect=RuntimeError("no audio device")):
        audio.play_blip()
        audio.play_select()
        audio.play_start()
        audio.play_victory()
        audio.play_error()

    audio.set_sound_enabled(False)
    audio.play_blip()
    audio.play_select()
    audio.play_start()
    audio.play_victory()
    audio.play_error()
    audio.set_sound_enabled(True)


def test_sound_calls_winsound_when_enabled():
    mock_beep = MagicMock()
    with patch.dict(sys.modules, {"winsound": MagicMock(Beep=mock_beep)}):
        with patch("threading.Thread") as mock_thread:
            def fake_thread(target, *args, **kwargs):
                t = MagicMock()
                t.start = target
                return t

            mock_thread.side_effect = fake_thread

            audio.set_sound_enabled(True)
            audio.play_blip()
            assert mock_beep.called


def test_sound_does_not_call_winsound_when_disabled():
    mock_beep = MagicMock()
    with patch.dict(sys.modules, {"winsound": MagicMock(Beep=mock_beep)}):
        audio.set_sound_enabled(False)
        audio.play_blip()
        assert not mock_beep.called
        audio.set_sound_enabled(True)
