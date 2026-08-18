"""The four ghosts and their personalities.

Each ghost picks, at every tile centre, the exit that brings it
closest to its own target tile -- never turning back on itself.  The
targets are the ones that made the arcade original famous: Blinky
hunts, Pinky cuts corners, Inky flanks and Clyde loses his nerve.
When the player swallows a super-pacgum the rule is inverted and the
ghosts pick the exit that takes them as far away as possible.
"""

from enum import Enum
from typing import Optional

from . import direction as compass
from .direction import DIRECTIONS, Direction
from .entities import Mover
from .maze import Maze, Tile

CLYDE_PANIC_DISTANCE = 8.0
_FLASH_WARNING = 2.0


class GhostKind(Enum):
    """The four canonical ghosts."""

    BLINKY = "Blinky"
    PINKY = "Pinky"
    INKY = "Inky"
    CLYDE = "Clyde"


class GhostState(Enum):
    """What a ghost is currently doing."""

    SCATTER = "scatter"
    CHASE = "chase"
    FRIGHTENED = "frightened"
    EATEN = "eaten"


class Ghost(Mover):
    """One ghost, with its personality and its state machine."""

    __slots__ = ("kind", "home", "state", "timer", "base_speed",
                 "frightened_speed", "target", "frozen")

    def __init__(self, kind: GhostKind, home: Tile, speed: float,
                 frightened_speed: float) -> None:
        """Create a ghost sitting in its own corner of the maze."""
        super().__init__(home, speed)
        self.kind = kind
        self.home = home
        self.state = GhostState.SCATTER
        self.timer = 0.0
        self.base_speed = speed
        self.frightened_speed = frightened_speed
        self.target: Tile = home
        self.frozen = False

    @property
    def is_edible(self) -> bool:
        """Return ``True`` when the player may eat this ghost."""
        return self.state is GhostState.FRIGHTENED

    @property
    def is_active(self) -> bool:
        """Return ``True`` when the ghost is on the board."""
        return self.state is not GhostState.EATEN

    @property
    def is_flashing(self) -> bool:
        """Return ``True`` when the frightened state is about to end."""
        return self.is_edible and self.timer <= _FLASH_WARNING

    def reset(self) -> None:
        """Send the ghost home and put it back in scatter mode."""
        self.place(self.home, compass.NONE)
        self.state = GhostState.SCATTER
        self.timer = 0.0
        self.speed = self.base_speed

    def start_chase(self) -> None:
        """Leave scatter mode for the hunt."""
        if self.state is GhostState.SCATTER:
            self.state = GhostState.CHASE

    def frighten(self, duration: float) -> None:
        """Make the ghost edible for *duration* seconds."""
        if self.state is GhostState.EATEN:
            return
        if self.state is not GhostState.FRIGHTENED:
            self.reverse()
        self.state = GhostState.FRIGHTENED
        self.timer = duration
        self.speed = self.frightened_speed

    def eat(self, respawn_delay: float) -> None:
        """Send the ghost back to its corner for *respawn_delay*."""
        self.state = GhostState.EATEN
        self.timer = respawn_delay
        self.place(self.home, compass.NONE)
        self.speed = self.base_speed

    def tick(self, delta: float) -> None:
        """Advance the state machine by *delta* seconds."""
        if self.timer <= 0.0:
            return
        self.timer = max(0.0, self.timer - delta)
        if self.timer > 0.0:
            return
        if self.state is GhostState.FRIGHTENED:
            self.state = GhostState.CHASE
            self.speed = self.base_speed
        elif self.state is GhostState.EATEN:
            self.state = GhostState.CHASE
            self.speed = self.base_speed

    def aim(self, player: Mover, blinky: Optional["Ghost"]) -> None:
        """Recompute the tile this ghost is heading for."""
        self.target = self._target_tile(player, blinky)

    def choose_direction(self, maze: Maze) -> Direction:
        """Pick the exit that best serves the current target."""
        if self.frozen or not self.is_active:
            return compass.NONE
        options = [step for step in DIRECTIONS
                   if maze.is_open(self.anchor[0] + step.dx,
                                   self.anchor[1] + step.dy)]
        if not options:
            return compass.NONE
        forward = [step for step in options
                   if step != self.direction.opposite()]
        candidates = forward or options
        away = self.state is GhostState.FRIGHTENED
        best = candidates[0]
        best_score = self._score(best, away)
        for step in candidates[1:]:
            score = self._score(step, away)
            if score < best_score:
                best, best_score = step, score
        return best

    def _score(self, step: Direction, away: bool) -> float:
        """Rank *step*; lower is better."""
        next_x = self.anchor[0] + step.dx
        next_y = self.anchor[1] + step.dy
        squared = ((next_x - self.target[0]) ** 2
                   + (next_y - self.target[1]) ** 2)
        return -squared if away else squared

    def _target_tile(self, player: Mover,
                     blinky: Optional["Ghost"]) -> Tile:
        """Return the tile the ghost aims at, given its personality."""
        if self.state is GhostState.SCATTER:
            return self.home
        if self.state is GhostState.FRIGHTENED:
            return player.tile
        if self.kind is GhostKind.BLINKY:
            return player.tile
        if self.kind is GhostKind.PINKY:
            return _ahead_of(player, 4)
        if self.kind is GhostKind.INKY:
            pivot = _ahead_of(player, 2)
            origin = blinky.tile if blinky is not None else self.home
            return (pivot[0] * 2 - origin[0], pivot[1] * 2 - origin[1])
        player_x, player_y = player.tile
        distance = ((self.x - player_x) ** 2
                    + (self.y - player_y) ** 2) ** 0.5
        if distance > CLYDE_PANIC_DISTANCE:
            return player.tile
        return self.home


def _ahead_of(player: Mover, tiles: int) -> Tile:
    """Return the tile *tiles* steps in front of the player."""
    tile = player.tile
    heading = player.direction
    if heading.is_none:
        return tile
    return tile[0] + heading.dx * tiles, tile[1] + heading.dy * tiles


def build_ghosts(corners: tuple[Tile, ...], speed: float,
                 frightened_speed: float) -> list[Ghost]:
    """Create the four ghosts, one per maze corner."""
    kinds = (GhostKind.BLINKY, GhostKind.PINKY, GhostKind.INKY,
             GhostKind.CLYDE)
    ghosts: list[Ghost] = []
    for index, kind in enumerate(kinds):
        home = corners[index % len(corners)] if corners else (1, 1)
        ghosts.append(Ghost(kind, home, speed, frightened_speed))
    return ghosts
