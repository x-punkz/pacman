"""Interface shared by every window backend."""

from abc import ABC, abstractmethod
from typing import NamedTuple

from ..image import Image


class BackendUnavailable(Exception):
    """Raised when a backend cannot be initialised on this machine."""


class WindowEvent(NamedTuple):
    """A single event, using the X11 numbering MiniLibX exposes."""

    kind: int
    code: int


class Backend(ABC):
    """Minimal window server abstraction.

    The four operations below are the strict superset of what MiniLibX
    offers: ``mlx_new_window``, ``mlx_put_image_to_window``, the event
    dispatch performed by ``mlx_loop`` and ``mlx_destroy_window``.
    """

    name = "base"

    @abstractmethod
    def open_window(self, width: int, height: int, title: str) -> None:
        """Create the window (``mlx_new_window``)."""

    @abstractmethod
    def put_image(self, image: Image, x: int, y: int) -> None:
        """Push *image* to the window (``mlx_put_image_to_window``)."""

    @abstractmethod
    def poll(self) -> list[WindowEvent]:
        """Return the events queued since the previous call."""

    @abstractmethod
    def close(self) -> None:
        """Destroy the window (``mlx_destroy_window``)."""
