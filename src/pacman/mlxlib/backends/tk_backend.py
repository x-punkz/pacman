"""Tk backend, used as a fallback when pygame is missing.

Tk is part of the standard library, so the game always has a way to
open a window.  The mapping onto MiniLibX is just as direct:

===============================  ==============================
tkinter                          MiniLibX
===============================  ==============================
``tkinter.Tk``                   ``mlx_init``
``Canvas`` inside a ``Toplevel`` ``mlx_new_window``
``PhotoImage`` + ``create_image``  ``mlx_put_image_to_window``
``bind`` on key events           ``mlx_hook`` / ``mlx_key_hook``
``destroy``                      ``mlx_destroy_window``
===============================  ==============================
"""

from typing import Any

from .. import keys
from ..image import Image
from .base import Backend, BackendUnavailable, WindowEvent

_KEYSYM_ALIASES: dict[int, int] = {
    0xFF8D: keys.KEY_RETURN,  # numeric keypad Enter
}


class TkBackend(Backend):
    """A window served by Tk."""

    name = "tk"

    def __init__(self) -> None:
        """Import tkinter and prepare the event queue."""
        try:
            import tkinter
        except ImportError as error:
            raise BackendUnavailable("tkinter is not available") from error
        self._tkinter = tkinter
        self._root: Any = None
        self._canvas: Any = None
        self._photo: Any = None
        self._events: list[WindowEvent] = []
        self._alive = False

    def open_window(self, width: int, height: int, title: str) -> None:
        """Create the Tk window and its canvas."""
        try:
            self._root = self._tkinter.Tk()
            self._root.title(title)
            self._root.resizable(False, False)
            self._canvas = self._tkinter.Canvas(
                self._root, width=width, height=height,
                highlightthickness=0, borderwidth=0, background="#000000")
            self._canvas.pack()
            self._photo = self._tkinter.PhotoImage(width=width, height=height)
            self._canvas.create_image(0, 0, anchor="nw", image=self._photo)
            self._root.bind("<KeyPress>", self._on_key_press)
            self._root.bind("<KeyRelease>", self._on_key_release)
            self._root.protocol("WM_DELETE_WINDOW", self._on_destroy)
            self._root.update()
            self._alive = True
        except Exception as error:  # pragma: no cover - display specific
            raise BackendUnavailable(str(error)) from error

    def put_image(self, image: Image, x: int, y: int) -> None:
        """Push the pixel buffer to the canvas as a binary PPM."""
        if not self._alive or self._photo is None:
            return
        header = b"P6 %d %d 255 " % (image.width, image.height)
        try:
            self._photo.configure(data=header + image.to_bytes())
            self._root.update_idletasks()
        except Exception:  # pragma: no cover - window closed mid-frame
            self._alive = False

    def poll(self) -> list[WindowEvent]:
        """Pump the Tk main loop once and return the queued events."""
        if self._alive:
            try:
                self._root.update()
            except Exception:  # pragma: no cover - window closed mid-frame
                self._alive = False
                self._events.append(WindowEvent(keys.EVENT_DESTROY, 0))
        collected = self._events
        self._events = []
        return collected

    def close(self) -> None:
        """Destroy the Tk window."""
        self._alive = False
        if self._root is not None:
            try:
                self._root.destroy()
            except Exception:  # pragma: no cover - shutdown is best effort
                pass
        self._root = None
        self._canvas = None
        self._photo = None

    def _on_key_press(self, event: Any) -> None:
        """Queue a key press event."""
        self._events.append(
            WindowEvent(keys.EVENT_KEY_PRESS, self._translate(event)))

    def _on_key_release(self, event: Any) -> None:
        """Queue a key release event."""
        self._events.append(
            WindowEvent(keys.EVENT_KEY_RELEASE, self._translate(event)))

    def _on_destroy(self) -> None:
        """Queue the window destruction event."""
        self._alive = False
        self._events.append(WindowEvent(keys.EVENT_DESTROY, 0))

    @staticmethod
    def _translate(event: Any) -> int:
        """Return the X11 keysym carried by a Tk event."""
        code = int(getattr(event, "keysym_num", 0) or 0)
        return _KEYSYM_ALIASES.get(code, code)
