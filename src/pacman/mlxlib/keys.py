"""Key codes, expressed as X11 keysyms.

MiniLibX hands over raw X11 keysyms to the key hooks, so the game uses
the very same values.  Each backend is responsible for translating its
native key codes into these constants.
"""

from typing import Final

KEY_BACKSPACE: Final = 0xFF08
KEY_TAB: Final = 0xFF09
KEY_RETURN: Final = 0xFF0D
KEY_ESCAPE: Final = 0xFF1B
KEY_SPACE: Final = 0x0020

KEY_LEFT: Final = 0xFF51
KEY_UP: Final = 0xFF52
KEY_RIGHT: Final = 0xFF53
KEY_DOWN: Final = 0xFF54

KEY_F1: Final = 0xFFBE
KEY_F2: Final = 0xFFBF
KEY_F3: Final = 0xFFC0
KEY_F4: Final = 0xFFC1
KEY_F5: Final = 0xFFC2
KEY_F6: Final = 0xFFC3
KEY_F7: Final = 0xFFC4
KEY_F8: Final = 0xFFC5
KEY_F9: Final = 0xFFC6
KEY_F10: Final = 0xFFC7
KEY_F11: Final = 0xFFC8
KEY_F12: Final = 0xFFC9

KEY_A: Final = ord("a")
KEY_C: Final = ord("c")
KEY_D: Final = ord("d")
KEY_H: Final = ord("h")
KEY_I: Final = ord("i")
KEY_P: Final = ord("p")
KEY_Q: Final = ord("q")
KEY_S: Final = ord("s")
KEY_W: Final = ord("w")

#: Events, mirroring the X11 event numbers used with ``mlx_hook``.
EVENT_KEY_PRESS: Final = 2
EVENT_KEY_RELEASE: Final = 3
EVENT_DESTROY: Final = 17

#: Event masks, mirroring the X11 masks used with ``mlx_hook``.
MASK_KEY_PRESS: Final = 1 << 0
MASK_KEY_RELEASE: Final = 1 << 1
MASK_STRUCTURE_NOTIFY: Final = 1 << 17


def is_printable(keycode: int) -> bool:
    """Return ``True`` when *keycode* maps to a printable ASCII glyph."""
    return 0x20 <= keycode <= 0x7E


def to_char(keycode: int, shifted: bool = False) -> str:
    """Translate *keycode* into a character, or ``""`` when not printable."""
    if not is_printable(keycode):
        return ""
    char = chr(keycode)
    return char.upper() if shifted else char
