"""The four cardinal directions used by every moving entity."""

from typing import Final, NamedTuple


class Direction(NamedTuple):
    """A unit step on the tile grid."""

    dx: int
    dy: int

    @property
    def is_none(self) -> bool:
        """Return ``True`` for the standing-still direction."""
        return self.dx == 0 and self.dy == 0

    def opposite(self) -> "Direction":
        """Return the direction pointing the other way."""
        return Direction(-self.dx, -self.dy)


NONE: Final = Direction(0, 0)
UP: Final = Direction(0, -1)
LEFT: Final = Direction(-1, 0)
DOWN: Final = Direction(0, 1)
RIGHT: Final = Direction(1, 0)

#: Candidate order used to break ties, as in the original arcade game.
DIRECTIONS: Final[tuple[Direction, ...]] = (UP, LEFT, DOWN, RIGHT)
