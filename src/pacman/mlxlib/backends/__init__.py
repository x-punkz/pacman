"""Window backends behind the MLX-like facade.

Two interchangeable implementations are provided.  Both are limited to
the handful of calls that have a MiniLibX counterpart: open a window,
push a full image to it, collect key events, close the window.
"""

from .base import Backend, BackendUnavailable, WindowEvent

__all__ = ["Backend", "BackendUnavailable", "WindowEvent"]
