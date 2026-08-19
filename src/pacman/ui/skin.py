"""The "hack the world" reskin: themed artwork over the same shapes.

Every function below mirrors one drawing routine from :mod:`sprites`
and takes the same kind of arguments, but stamps a themed PNG instead
of painting a shape pixel by pixel. When the artwork cannot be loaded
-- missing file, unsupported PNG feature -- it falls back to the
matching :mod:`sprites` routine, so the game is always playable even
with the ``images/`` folder removed.
"""

from typing import Final

from ..game import direction as compass
from ..game.direction import Direction
from ..game.ghosts import GhostKind
from ..mlxlib.image import Image
from . import assets, sprites, theme

_GHOST_FILES: Final[dict[GhostKind, str]] = {
    GhostKind.BLINKY: "blinky.png",
    GhostKind.PINKY: "fbi_pinky.png",
    GhostKind.INKY: "federal_ink.png",
    GhostKind.CLYDE: "police_clyde.png",
}

_EYE_FILES: Final[dict[Direction, str]] = {
    compass.UP: "olho_cima.png",
    compass.DOWN: "olho_baixo.png",
    compass.LEFT: "olho_esquerda.png",
    compass.RIGHT: "olho_direita.png",
}

#: (quarter turns clockwise, mirror) needed to steer the right-facing
#: source artwork towards each direction. Measured directly off the
#: pixels (centroid of the mouth wedge) rather than eyeballed: the
#: sunglasses make the open/shut wedge easy to misjudge by eye at this
#: resolution.
_ORIENTATIONS: Final[dict[Direction, tuple[int, bool]]] = {
    compass.RIGHT: (0, False),
    compass.LEFT: (0, True),
    compass.DOWN: (1, False),
    compass.UP: (3, False),
}

_SUPER_FILES: Final[tuple[str, ...]] = (
    "bonus_cadeado.png", "bonus_disket.png", "bonus_terminal.png",
)

_WALK_HZ = 6.0
_FLASH_HZ = 8.0


def draw_pacman(image: Image, center_x: int, center_y: int, radius: int,
                heading: Direction, openness: float, clock: float) -> None:
    """Draw the player, themed sprite first, hand-drawn disc as backup."""
    sheet = assets.sheet("pacmano.png", columns=2, rows=2)
    if sheet is None:
        sprites.draw_pacman(image, center_x, center_y, radius, heading,
                            openness)
        return
    del clock  # the sheet only tells open from shut, no need for time
    turns, flip = _ORIENTATIONS.get(heading, _ORIENTATIONS[compass.LEFT])
    column, row = (0, 0) if openness < 0.15 else (1, 0)
    sheet.blit(image, center_x, center_y, radius * 2, column=column,
               row=row, flip_x=flip, quarter_turns=turns)


def draw_ghost(image: Image, center_x: int, center_y: int, size: int,
               kind: GhostKind, heading: Direction, is_edible: bool,
               is_flashing: bool, clock: float) -> None:
    """Draw one ghost's body, themed sprite first."""
    walk_row = int(clock * _WALK_HZ) % 2
    if is_edible:
        sheet = assets.sheet("medroso.png", columns=2, rows=2)
        if sheet is None:
            sprites.draw_ghost(image, center_x, center_y, size,
                               theme.ghost_color(kind), heading, True,
                               is_flashing)
            return
        blinking = is_flashing and int(clock * _FLASH_HZ) % 2 == 0
        sheet.blit(image, center_x, center_y, size,
                   column=1 if blinking else 0, row=walk_row)
        return
    sheet = assets.sheet(_GHOST_FILES[kind], columns=1, rows=2)
    if sheet is None:
        sprites.draw_ghost(image, center_x, center_y, size,
                           theme.ghost_color(kind), heading, False, False)
        return
    sheet.blit(image, center_x, center_y, size, row=walk_row)


def draw_eyes(image: Image, center_x: int, center_y: int, half: int,
              heading: Direction) -> None:
    """Draw the eyes of a ghost on its way back home."""
    filename = _EYE_FILES.get(heading, "olho_baixo.png")
    sheet = assets.sheet(filename, columns=1, rows=2)
    if sheet is None:
        sprites.draw_eyes(image, center_x, center_y, half, heading)
        return
    sheet.blit(image, center_x, center_y, half * 2)


def draw_super_pacgum(image: Image, center_x: int, center_y: int,
                      box: int, corner_index: int, pulse: float) -> None:
    """Draw a power pellet as one of the three themed icons."""
    filename = _SUPER_FILES[corner_index % len(_SUPER_FILES)]
    sheet = assets.sheet(filename)
    if sheet is None:
        sprites.draw_super_pacgum(image, center_x, center_y, box // 2,
                                  pulse)
        return
    scaled = max(2, int(box * (0.85 + 0.15 * pulse)))
    sheet.blit(image, center_x, center_y, scaled)


def draw_life_icon(image: Image, x: int, y: int, size: int) -> None:
    """Draw the little Pac-Man used to show the remaining lives."""
    radius = max(3, size // 2)
    draw_pacman(image, x + radius, y + radius, radius, compass.RIGHT, 0.7,
                0.0)


def draw_bonus(image: Image, center_x: int, center_y: int, box: int,
               pulse: float) -> None:
    """Draw the bonus item, themed sprite first, pulsing dot as backup."""
    sheet = assets.sheet("virus.png")
    if sheet is None:
        sprites.draw_bonus(image, center_x, center_y, box // 2, pulse)
        return
    scaled = max(2, int(box * (0.85 + 0.15 * pulse)))
    sheet.blit(image, center_x, center_y, scaled)
