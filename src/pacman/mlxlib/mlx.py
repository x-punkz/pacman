"""The MLX-like facade the whole game draws through.

Every public method below mirrors one MiniLibX function, and nothing
outside this table is offered to the rest of the code base:

=================================  =============================
``pacman.mlxlib``                  MiniLibX
=================================  =============================
``Mlx()``                          ``mlx_init``
``Mlx.new_window``                 ``mlx_new_window``
``Mlx.new_image``                  ``mlx_new_image``
``Image.data``                     ``mlx_get_data_addr``
``Image.pixel_put``                ``mlx_pixel_put``
``Mlx.put_image_to_window``        ``mlx_put_image_to_window``
``Mlx.string_put``                 ``mlx_string_put``
``Mlx.clear_window``               ``mlx_clear_window``
``Mlx.hook`` / ``Mlx.key_hook``    ``mlx_hook`` / ``mlx_key_hook``
``Mlx.loop_hook``                  ``mlx_loop_hook``
``Mlx.loop`` / ``Mlx.loop_end``    ``mlx_loop`` / ``mlx_loop_end``
``Mlx.destroy_image``              ``mlx_destroy_image``
``Mlx.destroy_window``             ``mlx_destroy_window``
=================================  =============================

Rectangles, discs and text are *not* library calls: they are written
here on top of raw pixel writes, exactly as a 42 student would layer
them on ``mlx_pixel_put``.
"""

import os
import time
from typing import Callable, Optional

from . import font, keys
from .backends.base import Backend, BackendUnavailable
from .image import Image

EventHandler = Callable[[int], None]
LoopHandler = Callable[[float], None]

_MAX_FRAME_TIME = 0.05


class MlxError(Exception):
    """Raised when no window can be opened at all."""


class Mlx:
    """A tiny MiniLibX work-alike backed by pygame or Tk."""

    def __init__(self, backend_name: str = "auto") -> None:
        """Initialise the display connection (``mlx_init``)."""
        self._backend = _open_backend(backend_name)
        self._window_open = False
        self._hooks: dict[int, list[EventHandler]] = {}
        self._loop_hook: Optional[LoopHandler] = None
        self._running = False
        self._target_fps = 60

    @property
    def backend_name(self) -> str:
        """Return the name of the backend actually in use."""
        return self._backend.name

    def new_window(self, width: int, height: int, title: str) -> None:
        """Open the game window (``mlx_new_window``)."""
        self._backend.open_window(width, height, title)
        self._window_open = True

    def new_image(self, width: int, height: int) -> Image:
        """Allocate an off-screen image (``mlx_new_image``)."""
        return Image(width, height)

    def destroy_image(self, image: Image) -> None:
        """Release an image (``mlx_destroy_image``)."""
        image.data = bytearray()

    def put_image_to_window(self, image: Image, x: int = 0,
                            y: int = 0) -> None:
        """Copy *image* into the window (``mlx_put_image_to_window``)."""
        if self._window_open:
            self._backend.put_image(image, x, y)

    def string_put(self, image: Image, x: int, y: int, color: int,
                   text: str, scale: int = 1) -> None:
        """Draw *text* into *image* (``mlx_string_put``)."""
        font.draw_text(image, x, y, color, text, scale)

    def text_width(self, text: str, scale: int = 1) -> int:
        """Return the pixel width *text* will occupy."""
        return font.text_width(text, scale)

    def text_height(self, scale: int = 1) -> int:
        """Return the pixel height of one line of text."""
        return font.text_height(scale)

    def clear_window(self, image: Image, color: int = 0x000000) -> None:
        """Blank the frame buffer (``mlx_clear_window``)."""
        image.clear(color)

    def hook(self, event: int, mask: int, handler: EventHandler) -> None:
        """Register an event handler (``mlx_hook``)."""
        del mask  # kept for signature parity with mlx_hook
        self._hooks.setdefault(event, []).append(handler)

    def key_hook(self, handler: EventHandler) -> None:
        """Register a key press handler (``mlx_key_hook``)."""
        self.hook(keys.EVENT_KEY_PRESS, keys.MASK_KEY_PRESS, handler)

    def loop_hook(self, handler: LoopHandler) -> None:
        """Register the per-frame handler (``mlx_loop_hook``)."""
        self._loop_hook = handler

    def set_target_fps(self, fps: int) -> None:
        """Cap the loop rate; MiniLibX loops as fast as it can."""
        self._target_fps = max(1, min(240, fps))

    def loop(self) -> None:
        """Run the event loop until :meth:`loop_end` (``mlx_loop``)."""
        self._running = True
        previous = time.perf_counter()
        frame_time = 1.0 / float(self._target_fps)
        while self._running:
            for event in self._backend.poll():
                for handler in self._hooks.get(event.kind, ()):
                    handler(event.code)
                if not self._running:
                    break
            if not self._running:
                break
            now = time.perf_counter()
            delta = min(now - previous, _MAX_FRAME_TIME)
            previous = now
            if self._loop_hook is not None:
                self._loop_hook(delta)
            spare = frame_time - (time.perf_counter() - now)
            if spare > 0.0:
                time.sleep(spare)

    def loop_end(self) -> None:
        """Ask :meth:`loop` to return (``mlx_loop_end``)."""
        self._running = False

    def destroy_window(self) -> None:
        """Close the window (``mlx_destroy_window``)."""
        if self._window_open:
            self._backend.close()
            self._window_open = False


def _open_backend(name: str) -> Backend:
    """Instantiate the requested backend, falling back when needed."""
    requested = (os.environ.get("PACMAN_BACKEND") or name or "auto").lower()
    order = {
        "pygame": ("pygame",),
        "tk": ("tk",),
        "tkinter": ("tk",),
    }.get(requested, ("pygame", "tk"))
    failures: list[str] = []
    for candidate in order:
        try:
            if candidate == "pygame":
                from .backends.pygame_backend import PygameBackend
                return PygameBackend()
            from .backends.tk_backend import TkBackend
            return TkBackend()
        except BackendUnavailable as error:
            failures.append("%s: %s" % (candidate, error))
    raise MlxError("no usable graphics backend (%s)" % "; ".join(failures))
