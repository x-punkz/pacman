"""Everything that moves on the tile grid.

Entities live at floating point tile coordinates but may only travel
from one tile centre to the next, which is what gives Pac-Man its
characteristic grid-locked feel: a turn is only taken once the entity
is exactly on a tile centre.
"""

import math
from typing import Optional

from . import direction as compass
from .direction import Direction
from .maze import Maze, Tile

_EPSILON = 1e-9
_MAX_STEPS_PER_FRAME = 64


class Mover:
    """A body that slides from tile centre to tile centre."""

    __slots__ = ("x", "y", "direction", "pending", "speed", "travelled",
                 "_at", "_target")

    def __init__(self, tile: Tile, speed: float) -> None:
        """Place the body on *tile*, standing still."""
        self.x = float(tile[0])
        self.y = float(tile[1])
        self.direction: Direction = compass.NONE
        self.pending: Direction = compass.NONE
        self.speed = speed
        self.travelled = 0.0
        self._at: Tile = tile
        self._target: Optional[Tile] = None

    @property
    def tile(self) -> Tile:
        """Return the tile the body currently overlaps the most."""
        return int(round(self.x)), int(round(self.y))

    @property
    def anchor(self) -> Tile:
        """Return the last tile centre the body sat on."""
        return self._at

    @property
    def is_centred(self) -> bool:
        """Return ``True`` when the body sits exactly on a tile centre."""
        return self._target is None

    def place(self, tile: Tile,
              heading: Direction = compass.NONE) -> None:
        """Teleport the body to *tile*, facing *heading*."""
        self.x = float(tile[0])
        self.y = float(tile[1])
        self._at = tile
        self._target = None
        self.direction = heading
        self.pending = compass.NONE

    def distance_to(self, other: "Mover") -> float:
        """Return the euclidean distance to *other*, in tiles."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def reverse(self) -> None:
        """Turn around, even in the middle of a corridor."""
        if self.direction.is_none:
            return
        if self._target is not None:
            self._at, self._target = self._target, self._at
        self.direction = self.direction.opposite()

    def update(self, delta: float, maze: Maze) -> None:
        """Advance the body for *delta* seconds."""
        budget = max(0.0, self.speed * delta)
        steps = 0
        while budget > _EPSILON and steps < _MAX_STEPS_PER_FRAME:
            steps += 1
            if self._target is None and not self._start_step(maze):
                break
            budget = self._advance(budget)

    def choose_direction(self, maze: Maze) -> Direction:
        """Return the direction to take from the current tile centre."""
        if self._can_go(maze, self.pending):
            return self.pending
        if self._can_go(maze, self.direction):
            return self.direction
        return compass.NONE

    def on_tile_reached(self) -> None:
        """Hook called every time a tile centre is reached."""

    def _can_go(self, maze: Maze, heading: Direction) -> bool:
        """Return ``True`` when *heading* leaves the current tile."""
        if heading.is_none:
            return False
        return maze.is_open(self._at[0] + heading.dx,
                            self._at[1] + heading.dy)

    def _start_step(self, maze: Maze) -> bool:
        """Pick the next tile to walk into; ``False`` when blocked."""
        heading = self.choose_direction(maze)
        if heading.is_none or not self._can_go(maze, heading):
            self.direction = compass.NONE
            return False
        self.direction = heading
        self._target = (self._at[0] + heading.dx, self._at[1] + heading.dy)
        return True

    def _advance(self, budget: float) -> float:
        """Move towards the current target and return the leftover."""
        target = self._target
        if target is None:
            return 0.0
        remaining = abs(target[0] - self.x) + abs(target[1] - self.y)
        if remaining <= budget:
            self.x = float(target[0])
            self.y = float(target[1])
            self._at = target
            self._target = None
            self.travelled += remaining
            self.on_tile_reached()
            return budget - remaining
        self.x += self.direction.dx * budget
        self.y += self.direction.dy * budget
        self.travelled += budget
        return 0.0


class Player(Mover):
    """Pac-Man himself."""

    __slots__ = ("start_tile",)

    def __init__(self, tile: Tile, speed: float) -> None:
        """Create the player on its spawn tile."""
        super().__init__(tile, speed)
        self.start_tile = tile
        self.direction = compass.LEFT
        self.pending = compass.LEFT

    def steer(self, heading: Direction) -> None:
        """Ask the player to turn as soon as the maze allows it."""
        self.pending = heading

    def respawn(self) -> None:
        """Send the player back to the middle of the maze."""
        self.place(self.start_tile, compass.LEFT)
        self.pending = compass.LEFT

    @property
    def mouth_openness(self) -> float:
        """Return the mouth aperture, from 0.0 (shut) to 1.0 (wide)."""
        if self.direction.is_none:
            return 0.35
        phase = (self.travelled * 2.4) % 2.0
        return phase if phase <= 1.0 else 2.0 - phase
