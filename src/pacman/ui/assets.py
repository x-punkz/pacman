"""Loading and blitting the "hack the world" artwork.

The rest of the game only ever draws through :mod:`pacman.ui.sprites`,
which paints everything one pixel at a time.  This module adds a
second way to fill those same pixels: decode a themed PNG once, cache
it, and stamp it onto the frame with nearest-neighbour scaling plus
the odd flip or quarter turn -- still nothing fancier than repeated
``pixel_put`` calls under the hood.

Every public entry point here is defensive on purpose: a missing or
unreadable file never raises past this module.  Callers ask
:func:`sheet` for artwork and get ``None`` back when it is not
available, at which point they fall back to the hand-drawn shapes in
:mod:`pacman.ui.sprites`.  The subject's "never crash" rule applies to
artwork too.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..mlxlib.image import BYTES_PER_PIXEL, Image
from ..mlxlib.png import PngError, decode as decode_png

_cache: dict[str, Optional["Sheet"]] = {}
_warnings: list[str] = []


def warnings() -> list[str]:
    """Return every warning collected while loading artwork so far."""
    return list(_warnings)


@dataclass(frozen=True)
class Sheet:
    """A decoded RGBA image, optionally sliced into an animation grid."""

    rgba: bytes
    width: int
    height: int
    columns: int = 1
    rows: int = 1

    @property
    def frame_width(self) -> int:
        """Return the pixel width of one grid cell."""
        return max(1, self.width // self.columns)

    @property
    def frame_height(self) -> int:
        """Return the pixel height of one grid cell."""
        return max(1, self.height // self.rows)

    def blit(self, image: Image, center_x: int, center_y: int, box: int,
             column: int = 0, row: int = 0, flip_x: bool = False,
             quarter_turns: int = 0) -> None:
        """Stamp one grid cell onto *image*, scaled to a *box* square.

        Args:
            image: The frame buffer to paint into.
            center_x: Column the sprite is centred on.
            center_y: Row the sprite is centred on.
            box: Side length, in pixels, of the destination square.
            column: Which frame column to sample (0-based).
            row: Which frame row to sample (0-based).
            flip_x: Mirror the artwork left-right before drawing.
            quarter_turns: Rotate the artwork clockwise, in 90-degree
                steps (0-3), after the optional mirror.
        """
        box = max(1, box)
        frame_w, frame_h = self.frame_width, self.frame_height
        source_x = min(self.columns - 1, max(0, column)) * frame_w
        source_y = min(self.rows - 1, max(0, row)) * frame_h
        left = center_x - box // 2
        top = center_y - box // 2
        turns = quarter_turns % 4
        stride = self.width * 4
        data = self.rgba
        out = image.data
        out_stride = image.stride
        out_w, out_h = image.width, image.height
        for dest_y in range(box):
            screen_y = top + dest_y
            if screen_y < 0 or screen_y >= out_h:
                continue
            v = (dest_y + 0.5) / box
            for dest_x in range(box):
                screen_x = left + dest_x
                if screen_x < 0 or screen_x >= out_w:
                    continue
                u = (dest_x + 0.5) / box
                sample_u, sample_v = _orient(u, v, flip_x, turns)
                sx = source_x + min(frame_w - 1, int(sample_u * frame_w))
                sy = source_y + min(frame_h - 1, int(sample_v * frame_h))
                pixel = (sy * stride) + sx * 4
                alpha = data[pixel + 3]
                if alpha == 0:
                    continue
                out_offset = screen_y * out_stride + screen_x * \
                    BYTES_PER_PIXEL
                if alpha == 255:
                    out[out_offset] = data[pixel]
                    out[out_offset + 1] = data[pixel + 1]
                    out[out_offset + 2] = data[pixel + 2]
                    continue
                ratio = alpha / 255.0
                out[out_offset] = _blend(out[out_offset], data[pixel], ratio)
                out[out_offset + 1] = _blend(out[out_offset + 1],
                                             data[pixel + 1], ratio)
                out[out_offset + 2] = _blend(out[out_offset + 2],
                                             data[pixel + 2], ratio)


def _blend(background: int, foreground: int, ratio: float) -> int:
    """Alpha-blend one channel; *ratio* is the foreground's weight."""
    return int(background + (foreground - background) * ratio)


def _orient(u: float, v: float, flip_x: bool,
            quarter_turns: int) -> tuple[float, float]:
    """Map a destination-space coordinate back into source space."""
    if flip_x:
        u = 1.0 - u
    if quarter_turns == 1:
        return v, 1.0 - u
    if quarter_turns == 2:
        return 1.0 - u, 1.0 - v
    if quarter_turns == 3:
        return 1.0 - v, u
    return u, v


def sheet(name: str, columns: int = 1, rows: int = 1) -> Optional[Sheet]:
    """Return the decoded, cached sheet for ``images/<name>``.

    Every failure -- missing file, unreadable PNG, unsupported PNG
    feature -- is swallowed and recorded in :func:`warnings` instead
    of raised, so a broken or absent asset never stops the game.
    """
    key = "%s:%dx%d" % (name, columns, rows)
    if key in _cache:
        return _cache[key]
    path = images_dir() / name
    try:
        data, width, height = decode_png(path)
    except PngError as error:
        _warnings.append("artwork '%s' could not be loaded (%s), "
                         "using the built-in shapes instead" % (name, error))
        _cache[key] = None
        return None
    result = Sheet(data, width, height, columns, rows)
    _cache[key] = result
    return result


def images_dir() -> Path:
    """Return the directory the themed artwork ships in."""
    frozen_base = getattr(sys, "_MEIPASS", None)
    if frozen_base is not None:
        return Path(frozen_base) / "images"
    return Path(__file__).resolve().parents[3] / "images"
