"""Animated retro ASCII/Unicode sprites for terminal loading screens."""

# Pac-Cleaner chomp animation frames
PAC_CLEANER_FRAMES = [
    "C • • • •",
    " C• • • •",
    "  C • • •",
    "   C• • •",
    "    C • •",
    "     C• •",
    "      C •",
    "       C•",
    "        C",
    "    ★ OK!",
]

# Sweeping broom animation
BROOM_FRAMES = [
    "  /▌ ░░",
    " //▌ ▒▒",
    "---▌ ▓▓",
    " \\\\▌ ▒▒",
]


def get_sprite_frame(frame_index: int) -> str:
    """Returns the sprite frame corresponding to the index, cycling continuously."""
    idx = frame_index % len(PAC_CLEANER_FRAMES)
    return PAC_CLEANER_FRAMES[idx]


def get_broom_frame(frame_index: int) -> str:
    """Returns the broom sprite frame corresponding to the index."""
    idx = frame_index % len(BROOM_FRAMES)
    return BROOM_FRAMES[idx]

