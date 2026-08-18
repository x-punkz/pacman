"""A whole play-through: score, lives and the ladder of levels."""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..settings import Config
from . import generator, level as level_module
from .cheats import Cheats
from .level import Level, LevelOutcome

CLEARED_BANNER = 2.0
LIFE_LOST_BANNER = 1.6
READY_BANNER = 1.4


class SessionState(Enum):
    """Where the play-through currently stands."""

    READY = "ready"
    PLAYING = "playing"
    LEVEL_CLEARED = "level-cleared"
    LIFE_LOST = "life-lost"
    GAME_OVER = "game-over"
    VICTORY = "victory"
    FAILED = "failed"


@dataclass
class Session:
    """One game, from the first level to the game-over screen."""

    config: Config
    cheats: Cheats
    rng: random.Random
    level: Level
    state: SessionState = SessionState.READY
    score: int = 0
    lives: int = 3
    banner: str = "READY!"
    banner_left: float = READY_BANNER
    error: str = ""

    @property
    def level_number(self) -> int:
        """Return the 1-based number of the level being played."""
        return self.level.number

    @property
    def level_count(self) -> int:
        """Return how many levels the game holds."""
        return max(1, self.config.level_count)

    @property
    def is_over(self) -> bool:
        """Return ``True`` once the play-through cannot continue."""
        return self.state in (SessionState.GAME_OVER, SessionState.VICTORY,
                              SessionState.FAILED)

    @property
    def won(self) -> bool:
        """Return ``True`` when every level was completed."""
        return self.state is SessionState.VICTORY

    def add_life(self) -> None:
        """Grant one extra life; used by the cheat menu."""
        self.lives = min(99, self.lives + 1)

    def update(self, delta: float) -> None:
        """Advance the play-through by *delta* seconds."""
        if self.is_over:
            return
        if self.banner_left > 0.0:
            self.banner_left = max(0.0, self.banner_left - delta)
            if self.banner_left > 0.0:
                return
            self._banner_elapsed()
            return
        if self.state is not SessionState.PLAYING:
            return
        events = self.level.update(delta, self.cheats)
        self.score += events.score
        self._handle(events.outcome)

    def _handle(self, outcome: LevelOutcome) -> None:
        """React to the outcome reported by the level."""
        if outcome is LevelOutcome.RUNNING:
            return
        if outcome is LevelOutcome.CLEARED:
            self.state = SessionState.LEVEL_CLEARED
            self.banner = "LEVEL %d COMPLETE" % self.level.number
            self.banner_left = CLEARED_BANNER
            return
        if outcome is LevelOutcome.TIMED_OUT:
            self.banner = "TIME UP"
            if not self.config.timeout_costs_life:
                self.state = SessionState.LIFE_LOST
                self.banner_left = LIFE_LOST_BANNER
                return
        else:
            self.banner = "CAUGHT!"
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.state = SessionState.GAME_OVER
            return
        self.state = SessionState.LIFE_LOST
        self.banner_left = LIFE_LOST_BANNER

    def _banner_elapsed(self) -> None:
        """Resume playing once the current banner has been shown."""
        if self.state is SessionState.READY:
            self.state = SessionState.PLAYING
            return
        if self.state is SessionState.LIFE_LOST:
            self.level.restart()
            self.state = SessionState.READY
            self.banner = "READY!"
            self.banner_left = READY_BANNER
            return
        if self.state is SessionState.LEVEL_CLEARED:
            self._next_level()

    def _next_level(self) -> None:
        """Load the next level, or declare victory."""
        following = self.level.number + 1
        if following > self.level_count:
            self.state = SessionState.VICTORY
            return
        loaded = _load_level(self.config, following, self.rng)
        if loaded is None:
            self.state = SessionState.FAILED
            self.error = ("the maze generator failed on level %d"
                          % following)
            return
        self.level = loaded
        self.state = SessionState.READY
        self.banner = "LEVEL %d" % following
        self.banner_left = READY_BANNER


def new_session(config: Config, cheats: Cheats) -> tuple[Optional[Session],
                                                         str]:
    """Start a play-through, or explain why it could not start.

    Args:
        config: The validated configuration.
        cheats: The shared cheat switches.

    Returns:
        A tuple holding the session (or ``None``) and an error message
        that is empty on success.
    """
    rng = random.Random(config.seed or None)
    first = _load_level(config, 1, rng)
    if first is None:
        return None, ("the maze generator could not build the first level; "
                      "check that the A-Maze-ing package is installed")
    return Session(config=config, cheats=cheats, rng=rng, level=first,
                   lives=config.lives, banner="LEVEL 1",
                   banner_left=READY_BANNER), ""


def _load_level(config: Config, number: int,
                rng: random.Random) -> Optional[Level]:
    """Generate the maze of level *number* and populate it."""
    spec = level_module.spec_for(config, number)
    # The subject pins the first maze to the configured seed; every
    # later maze is random, which the package spells "seed = 0".
    seed = config.seed if number == 1 else 0
    for attempt in range(3):
        try:
            maze = generator.generate(spec.width, spec.height, seed)
        except generator.GeneratorError:
            if attempt == 2:
                return None
            seed = 0
            continue
        return level_module.build(config, number, maze, rng)
    return None
