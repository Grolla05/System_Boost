from frontend.components import retro_sprite


def test_retro_sprite_frames_exist():
    frames = retro_sprite.PAC_CLEANER_FRAMES
    assert len(frames) >= 4
    for frame in frames:
        assert isinstance(frame, str)
        assert len(frame) > 0


def test_get_sprite_frame_cycles():
    f0 = retro_sprite.get_sprite_frame(0)
    f1 = retro_sprite.get_sprite_frame(1)
    assert f0 != f1
    # Check wrap-around
    total = len(retro_sprite.PAC_CLEANER_FRAMES)
    assert retro_sprite.get_sprite_frame(total) == f0

