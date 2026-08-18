"""MLX-like graphics layer.

This sub-package exposes exactly the primitives offered by the
MiniLibX library used at 42: create a window, create an image, write
pixels into that image, push the image to the window, draw a string,
register event hooks and run a loop.

Nothing else is exposed, so the game code physically cannot call a
drawing routine that MiniLibX does not provide.
"""

from .image import Image
from .mlx import Mlx, MlxError
from . import keys

__all__ = ["Image", "Mlx", "MlxError", "keys"]
