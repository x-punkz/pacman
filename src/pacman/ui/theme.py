"""Colours and layout constants, gathered in one place."""

from typing import Final

from ..game.ghosts import GhostKind

BLACK: Final = 0x000000
BACKGROUND: Final = 0x05050F
PANEL: Final = 0x11112B
WALL: Final = 0x2121DE
WALL_EDGE: Final = 0x5A5AFF
PACGUM: Final = 0xFFB897
SUPER_PACGUM: Final = 0xFFE1B8
PACMAN: Final = 0xFFF200
TEXT: Final = 0xFFFFFF
TEXT_DIM: Final = 0x8A8AB0
ACCENT: Final = 0xFFF200
DANGER: Final = 0xFF5555
SUCCESS: Final = 0x6BFF8C
EYE_WHITE: Final = 0xFFFFFF
EYE_PUPIL: Final = 0x1A1AB0
FRIGHTENED: Final = 0x2121DE
FRIGHTENED_FLASH: Final = 0xF0F0F0
SHADOW: Final = 0x000000

GHOST_COLORS: Final[dict[GhostKind, int]] = {
    GhostKind.BLINKY: 0xFF3B30,
    GhostKind.PINKY: 0xFFB8DE,
    GhostKind.INKY: 0x3BE8FF,
    GhostKind.CLYDE: 0xFFA53B,
}

HUD_HEIGHT: Final = 58
FOOTER_HEIGHT: Final = 30
MARGIN: Final = 10
MIN_TILE: Final = 6
MAX_TILE: Final = 40


def ghost_color(kind: GhostKind) -> int:
    """Return the body colour of the ghost *kind*."""
    return GHOST_COLORS.get(kind, 0xFFFFFF)
