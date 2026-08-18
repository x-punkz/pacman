"""SDL backend, used when pygame is installed.

Only four pygame entry points are used, and each one exists in
MiniLibX:

===============================  ==============================
pygame                           MiniLibX
===============================  ==============================
``pygame.display.init``          ``mlx_init``
``pygame.display.set_mode``      ``mlx_new_window``
``Surface.blit`` + ``flip``      ``mlx_put_image_to_window``
``pygame.event.get``             dispatch performed by ``mlx_loop``
``pygame.display.quit``          ``mlx_destroy_window``
===============================  ==============================

``pygame.image.frombuffer`` is not a drawing routine: it only wraps the
bytes the game already owns, exactly like the pointer returned by
``mlx_get_data_addr``.
"""

import os
from typing import Any

from .. import keys
from ..image import Image
from .base import Backend, BackendUnavailable, WindowEvent

_SPECIAL_KEYS: dict[int, int] = {}


def _build_key_table(pygame: Any) -> dict[int, int]:
    """Map SDL key codes onto the X11 keysyms MiniLibX reports."""
    table = {
        pygame.K_ESCAPE: keys.KEY_ESCAPE,
        pygame.K_RETURN: keys.KEY_RETURN,
        pygame.K_KP_ENTER: keys.KEY_RETURN,
        pygame.K_BACKSPACE: keys.KEY_BACKSPACE,
        pygame.K_TAB: keys.KEY_TAB,
        pygame.K_SPACE: keys.KEY_SPACE,
        pygame.K_LEFT: keys.KEY_LEFT,
        pygame.K_RIGHT: keys.KEY_RIGHT,
        pygame.K_UP: keys.KEY_UP,
        pygame.K_DOWN: keys.KEY_DOWN,
    }
    for index in range(12):
        table[getattr(pygame, "K_F%d" % (index + 1))] = keys.KEY_F1 + index
    return table


class PygameBackend(Backend):
    """A window served by SDL through pygame."""

    name = "pygame"

    def __init__(self) -> None:
        """Import pygame and prepare the key translation table."""
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame
        except ImportError as error:
            raise BackendUnavailable("pygame is not installed") from error
        self._pygame = pygame
        self._surface: Any = None
        self._keys = _build_key_table(pygame)

    def open_window(self, width: int, height: int, title: str) -> None:
        """Create the SDL window."""
        try:
            self._pygame.display.init()
            self._surface = self._pygame.display.set_mode((width, height))
            self._pygame.display.set_caption(title)
            self._pygame.key.set_repeat(0)
        except Exception as error:  # pragma: no cover - driver specific
            raise BackendUnavailable(str(error)) from error

    def put_image(self, image: Image, x: int, y: int) -> None:
        """Blit the whole pixel buffer and show it."""
        if self._surface is None:
            return
        frame = self._pygame.image.frombuffer(
            image.to_bytes(), (image.width, image.height), "RGB")
        self._surface.blit(frame, (x, y))
        self._pygame.display.flip()

    def poll(self) -> list[WindowEvent]:
        """Drain the SDL event queue."""
        events: list[WindowEvent] = []
        for event in self._pygame.event.get():
            if event.type == self._pygame.QUIT:
                events.append(WindowEvent(keys.EVENT_DESTROY, 0))
            elif event.type == self._pygame.KEYDOWN:
                events.append(WindowEvent(keys.EVENT_KEY_PRESS,
                                          self._translate(event.key)))
            elif event.type == self._pygame.KEYUP:
                events.append(WindowEvent(keys.EVENT_KEY_RELEASE,
                                          self._translate(event.key)))
        return events

    def close(self) -> None:
        """Destroy the SDL window."""
        try:
            self._pygame.display.quit()
        except Exception:  # pragma: no cover - shutdown is best effort
            pass
        self._surface = None

    def _translate(self, code: int) -> int:
        """Return the keysym matching the SDL *code*."""
        special = self._keys.get(code)
        if special is not None:
            return special
        if 0x20 <= code <= 0x7E:
            return code
        return -code
