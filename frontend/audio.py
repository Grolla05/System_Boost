"""8-bit retro chiptune audio generator using native Windows winsound."""
import os
import sys
import threading

_SOUND_ENABLED = True


def set_sound_enabled(enabled: bool):
    """Enables or disables retro sound effects globally."""
    global _SOUND_ENABLED
    _SOUND_ENABLED = bool(enabled)


def is_sound_enabled() -> bool:
    """Returns True if sound effects are enabled."""
    return _SOUND_ENABLED


def _play_tones_async(tones):
    """Plays a sequence of (frequency_hz, duration_ms) tuples in a daemon thread."""
    if not _SOUND_ENABLED:
        return

    def _worker():
        try:
            if os.name != "nt":
                return
            import winsound
            for freq, duration in tones:
                winsound.Beep(int(freq), int(duration))
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def play_blip():
    """Short retro blip sound when navigating menu items."""
    _play_tones_async([(880, 25)])


def play_select():
    """Two-tone affirmative blip when selecting an item."""
    _play_tones_async([(650, 35), (980, 50)])


def play_start():
    """Classic Game Boy / coin start sound."""
    _play_tones_async([(784, 45), (1046, 90)])


def play_victory():
    """Victory fanfare chiptune sequence."""
    _play_tones_async([(523, 70), (659, 70), (784, 70), (1046, 160)])


def play_error():
    """Low buzz tone for errors or cancellations."""
    _play_tones_async([(220, 60), (180, 90)])


def play_typewriter_click():
    """Subtle high tick for typewriter dialogue."""
    _play_tones_async([(1400, 10)])


