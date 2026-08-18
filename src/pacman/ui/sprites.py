"""Pixel-art drawing routines.

Every shape here is painted by writing pixels into an
:class:`~pacman.mlxlib.image.Image`; nothing calls a drawing primitive
that MiniLibX does not provide, because the only primitive used is
"set this pixel to that colour".
"""

import math
from typing import Final

from ..game.direction import Direction
from ..mlxlib.image import Image
from . import theme

_SKIRT_BUMPS: Final = 3


def draw_pacman(image: Image, center_x: int, center_y: int, radius: int,
                heading: Direction, openness: float,
                color: int = theme.PACMAN) -> None:
    """Draw Pac-Man as a disc with a wedge cut out for the mouth."""
    radius = max(2, radius)
    face_x, face_y = (heading.dx, heading.dy)
    if face_x == 0 and face_y == 0:
        face_x, face_y = 1, 0
    half_angle = 0.08 + 0.72 * max(0.0, min(1.0, openness))
    threshold = math.cos(half_angle)
    squared = radius * radius
    for offset_y in range(-radius, radius + 1):
        span = int(math.sqrt(max(0, squared - offset_y * offset_y)))
        for offset_x in range(-span, span + 1):
            if _in_mouth(offset_x, offset_y, face_x, face_y, threshold):
                continue
            image.pixel_put(center_x + offset_x, center_y + offset_y, color)


def _in_mouth(offset_x: int, offset_y: int, face_x: int, face_y: int,
              threshold: float) -> bool:
    """Return ``True`` when the pixel falls inside the mouth wedge."""
    length = math.hypot(offset_x, offset_y)
    if length < 1.0:
        return True
    dot = offset_x * face_x + offset_y * face_y
    return dot > length * threshold


def draw_ghost(image: Image, center_x: int, center_y: int, size: int,
               color: int, heading: Direction, frightened: bool = False,
               flashing: bool = False) -> None:
    """Draw a ghost: round head, wavy skirt and a pair of eyes."""
    half = max(3, size // 2)
    foot = max(2, half // 3)
    body = color
    if frightened:
        body = theme.FRIGHTENED_FLASH if flashing else theme.FRIGHTENED
    limits = _skirt_limits(half, foot)
    for offset_y in range(-half, half + 1):
        if offset_y < 0:
            span = int(math.sqrt(max(0, half * half - offset_y * offset_y)))
        else:
            span = half
        for offset_x in range(-span, span + 1):
            if offset_y > limits[offset_x + half]:
                continue
            image.pixel_put(center_x + offset_x, center_y + offset_y, body)
    if frightened:
        _draw_scared_face(image, center_x, center_y, half)
    else:
        draw_eyes(image, center_x, center_y, half, heading)


def _skirt_limits(half: int, foot: int) -> list[int]:
    """Return, per column, the lowest row the ghost body reaches."""
    width = half * 2 + 1
    limits: list[int] = []
    for column in range(width):
        phase = _SKIRT_BUMPS * column / float(width)
        wave = abs(math.sin(math.pi * phase))
        limits.append(half - foot + int(round(foot * wave)))
    return limits


def draw_eyes(image: Image, center_x: int, center_y: int, half: int,
              heading: Direction) -> None:
    """Draw two eyes looking towards *heading*."""
    white = max(2, half // 2)
    pupil = max(1, white // 2)
    shift = max(1, white // 2)
    eye_y = center_y - max(1, half // 4)
    for side in (-1, 1):
        eye_x = center_x + side * max(2, half // 2)
        image.fill_disc(eye_x, eye_y, white, theme.EYE_WHITE)
        image.fill_disc(eye_x + heading.dx * shift, eye_y + heading.dy
                        * shift, pupil, theme.EYE_PUPIL)


def _draw_scared_face(image: Image, center_x: int, center_y: int,
                      half: int) -> None:
    """Draw the two dots and the zigzag of a frightened ghost."""
    dot = max(1, half // 4)
    eye_y = center_y - max(1, half // 4)
    for side in (-1, 1):
        image.fill_disc(center_x + side * max(2, half // 2), eye_y, dot,
                        theme.EYE_WHITE)
    mouth_y = center_y + max(1, half // 3)
    step = max(1, half // 3)
    for index in range(-half + 1, half - 1):
        lift = (index + half) % (step * 2) < step
        image.fill_rect(center_x + index, mouth_y - (1 if lift else 0), 1,
                        max(1, half // 5), theme.EYE_WHITE)


def draw_pacgum(image: Image, center_x: int, center_y: int,
                radius: int) -> None:
    """Draw a small dot."""
    if radius <= 1:
        image.fill_rect(center_x, center_y, 2, 2, theme.PACGUM)
        return
    image.fill_disc(center_x, center_y, radius, theme.PACGUM)


def draw_super_pacgum(image: Image, center_x: int, center_y: int,
                      radius: int, pulse: float) -> None:
    """Draw a power pellet whose size breathes with *pulse*."""
    scaled = max(2, int(radius * (0.75 + 0.25 * pulse)))
    image.fill_disc(center_x, center_y, scaled, theme.SUPER_PACGUM)


def draw_life_icon(image: Image, x: int, y: int, size: int) -> None:
    """Draw the little Pac-Man used to show the remaining lives."""
    radius = max(3, size // 2)
    draw_pacman(image, x + radius, y + radius, radius, Direction(1, 0), 0.7)
