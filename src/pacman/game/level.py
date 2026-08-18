"""One level: a maze, its pacgums, the player and the four ghosts."""

import random
from dataclasses import dataclass, field
from enum import Enum

from ..settings import Config, LevelSpec
from .cheats import Cheats
from .entities import Player
from .ghosts import Ghost, build_ghosts
from .maze import Maze, Tile

EAT_DISTANCE = 0.6


class LevelOutcome(Enum):
    """What happened during the last update."""

    RUNNING = "running"
    CLEARED = "cleared"
    LIFE_LOST = "life-lost"
    TIMED_OUT = "timed-out"


@dataclass
class LevelEvents:
    """A summary of everything worth reacting to in one frame."""

    outcome: LevelOutcome = LevelOutcome.RUNNING
    score: int = 0
    pacgums: int = 0
    supers: int = 0
    ghosts: int = 0

    @property
    def anything_eaten(self) -> bool:
        """Return ``True`` when the player swallowed something."""
        return bool(self.pacgums or self.supers or self.ghosts)


@dataclass
class Level:
    """The mutable state of the level currently being played."""

    number: int
    config: Config
    maze: Maze
    player: Player
    ghosts: list[Ghost]
    pacgums: set[Tile]
    supers: set[Tile]
    time_left: float
    max_time: float
    scatter_left: float
    ghost_chain: int = 0
    frightened_left: float = 0.0
    elapsed: float = 0.0
    base_speed: float = field(default=6.0, repr=False)

    @property
    def remaining_pacgums(self) -> int:
        """Return how many edible dots are still on the board."""
        return len(self.pacgums) + len(self.supers)

    @property
    def is_cleared(self) -> bool:
        """Return ``True`` when every dot has been eaten."""
        return self.remaining_pacgums == 0

    def update(self, delta: float, cheats: Cheats) -> LevelEvents:
        """Advance the level by *delta* seconds."""
        events = LevelEvents()
        self.elapsed += delta
        self.player.speed = self.base_speed * cheats.player_speed_factor
        self.player.update(delta, self.maze)
        self._eat(events)
        self._update_ghosts(delta, cheats)
        self._collide(events, cheats)
        self._countdown(delta, events)
        return events

    def skip(self) -> None:
        """Clear every dot at once; used by the cheat menu."""
        self.pacgums.clear()
        self.supers.clear()

    def leave_one_pacgum(self) -> None:
        """Leave a single dot on the board; used by the cheat menu."""
        if self.supers:
            self.supers = {sorted(self.supers)[0]}
            self.pacgums.clear()
        elif self.pacgums:
            self.pacgums = {sorted(self.pacgums)[0]}

    def restart(self) -> None:
        """Put everybody back in place after a life is lost."""
        self.player.respawn()
        for ghost in self.ghosts:
            ghost.reset()
        self.scatter_left = self.config.scatter_duration
        self.frightened_left = 0.0
        self.ghost_chain = 0

    def _eat(self, events: LevelEvents) -> None:
        """Swallow whatever sits on the player tile."""
        tile = self.player.tile
        if tile in self.pacgums:
            self.pacgums.discard(tile)
            events.pacgums += 1
            events.score += self.config.points_per_pacgum
        elif tile in self.supers:
            self.supers.discard(tile)
            events.supers += 1
            events.score += self.config.points_per_super_pacgum
            self._frighten()

    def _frighten(self) -> None:
        """Make every ghost edible for a while."""
        self.ghost_chain = 0
        self.frightened_left = self.config.super_pacgum_duration
        for ghost in self.ghosts:
            ghost.frighten(self.config.super_pacgum_duration)

    def _update_ghosts(self, delta: float, cheats: Cheats) -> None:
        """Tick the ghost state machines and move them."""
        blinky = self.ghosts[0] if self.ghosts else None
        frozen = cheats.ghosts_are_frozen
        for ghost in self.ghosts:
            ghost.tick(delta)
            ghost.frozen = frozen
            if self.scatter_left <= 0.0:
                ghost.start_chase()
            ghost.aim(self.player, blinky)
            if ghost.is_active and not frozen:
                ghost.update(delta, self.maze)

    def _collide(self, events: LevelEvents, cheats: Cheats) -> None:
        """Resolve contacts between the player and the ghosts."""
        for ghost in self.ghosts:
            if not ghost.is_active:
                continue
            if self.player.distance_to(ghost) > EAT_DISTANCE:
                continue
            if ghost.is_edible:
                self.ghost_chain += 1
                events.ghosts += 1
                events.score += self._ghost_value()
                ghost.eat(self.config.ghost_respawn_delay)
            elif not cheats.is_invincible:
                events.outcome = LevelOutcome.LIFE_LOST
                return

    def _ghost_value(self) -> int:
        """Return the score awarded for the ghost just eaten."""
        base = self.config.points_per_ghost
        if not self.config.ghost_score_doubling:
            return base
        return int(base * 2 ** max(0, self.ghost_chain - 1))

    def _countdown(self, delta: float, events: LevelEvents) -> None:
        """Run the level clock and the scatter / frightened timers."""
        if self.scatter_left > 0.0:
            self.scatter_left = max(0.0, self.scatter_left - delta)
        if self.frightened_left > 0.0:
            self.frightened_left = max(0.0, self.frightened_left - delta)
            if self.frightened_left == 0.0:
                self.ghost_chain = 0
        if events.outcome is not LevelOutcome.RUNNING:
            return
        if self.is_cleared:
            events.outcome = LevelOutcome.CLEARED
            return
        self.time_left = max(0.0, self.time_left - delta)
        if self.time_left <= 0.0:
            events.outcome = LevelOutcome.TIMED_OUT


def build(config: Config, number: int, maze: Maze,
          rng: random.Random) -> Level:
    """Assemble level *number* on top of *maze*.

    Args:
        config: The validated game configuration.
        number: The 1-based level number.
        maze: The playfield produced by the A-Maze-ing package.
        rng: The random source used to scatter the pacgums.

    Returns:
        A fully populated :class:`Level`.
    """
    spec = spec_for(config, number)
    speed = ghost_speed(config, number)
    ghosts = build_ghosts(maze.corners, speed, config.ghost_frightened_speed)
    player = Player(maze.player_start, config.player_speed)
    supers = set(maze.corners)
    reserved = supers | {maze.player_start}
    pacgums = _scatter(maze, spec.pacgum, reserved, rng)
    return Level(
        number=number,
        config=config,
        maze=maze,
        player=player,
        ghosts=ghosts,
        pacgums=pacgums,
        supers=supers,
        time_left=spec.max_time,
        max_time=spec.max_time,
        scatter_left=config.scatter_duration,
        base_speed=config.player_speed,
    )


def spec_for(config: Config, number: int) -> LevelSpec:
    """Return the specification of level *number*, 1-based."""
    if not config.levels:
        return LevelSpec(15, 11, config.pacgum, config.level_max_time)
    index = min(max(1, number), len(config.levels)) - 1
    return config.levels[index]


def ghost_speed(config: Config, number: int) -> float:
    """Return the ghost speed used on level *number*."""
    speed = config.ghost_speed + config.ghost_speed_step * (number - 1)
    return min(speed, config.player_speed * 1.4)


def _scatter(maze: Maze, count: int, reserved: set[Tile],
             rng: random.Random) -> set[Tile]:
    """Spread *count* pacgums as evenly as possible over the maze.

    A value of ``0`` -- or any value larger than the number of free
    corridors -- fills every corridor, which gives the classic look.
    Otherwise the dots are picked with farthest-point sampling, so no
    corner of the maze is ever left empty.
    """
    candidates = [tile for tile in maze.open_tiles if tile not in reserved]
    if not candidates:
        return set()
    if count <= 0 or count >= len(candidates):
        return set(candidates)
    first = rng.randrange(len(candidates))
    chosen: list[Tile] = [candidates[first]]
    spread = [_manhattan(tile, candidates[first]) for tile in candidates]
    while len(chosen) < count:
        best = _argmax(spread)
        picked = candidates[best]
        chosen.append(picked)
        for index, tile in enumerate(candidates):
            distance = _manhattan(tile, picked)
            if distance < spread[index]:
                spread[index] = distance
    return set(chosen)


def _argmax(values: list[int]) -> int:
    """Return the index of the largest value; the first one wins."""
    best = 0
    for index in range(1, len(values)):
        if values[index] > values[best]:
            best = index
    return best


def _manhattan(first: Tile, second: Tile) -> int:
    """Return the Manhattan distance between two tiles."""
    return abs(first[0] - second[0]) + abs(first[1] - second[1])
