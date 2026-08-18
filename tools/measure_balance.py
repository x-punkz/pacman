#!/usr/bin/env python3
"""Measure how long an optimal player needs to clear each level.

The bot walks to the nearest remaining pacgum, ignoring the ghosts, so
the time it reports is a lower bound on what a human needs.  A level is
considered well balanced when that lower bound stays under roughly two
thirds of the level clock.

    python3 tools/measure_balance.py [config.json]
"""

import os
import sys
from collections import deque
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from pacman.game import direction as compass                    # noqa: E402
from pacman.game.cheats import Cheats                            # noqa: E402
from pacman.game.direction import DIRECTIONS, Direction          # noqa: E402
from pacman.game.level import Level                              # noqa: E402
from pacman.game.maze import Maze, Tile                          # noqa: E402
from pacman.settings import Config, load_config                  # noqa: E402
from pacman.game.session import new_session                      # noqa: E402

FRAME = 1.0 / 60.0
TIME_OUT = 900.0


def search(maze: Maze, start: Tile,
           goals: set[Tile]) -> tuple[Optional[Tile], Direction]:
    """Return the closest tile of *goals* and the first step to reach it."""
    previous: dict[Tile, Optional[tuple[Tile, Direction]]] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in goals:
            return current, _first_step(previous, current)
        for step in DIRECTIONS:
            following = (current[0] + step.dx, current[1] + step.dy)
            if following not in previous and maze.is_open(*following):
                previous[following] = (current, step)
                queue.append(following)
    return None, compass.NONE


def _first_step(previous: dict[Tile, Optional[tuple[Tile, Direction]]],
                goal: Tile) -> Direction:
    """Walk the parent chain back and return the very first move."""
    step = compass.NONE
    node = goal
    while previous[node] is not None:
        parent, taken = previous[node]  # type: ignore[misc]
        step = taken
        node = parent
    return step


def _reference_tile(level: Level) -> Tile:
    """Return the tile the player will next be able to turn on."""
    player = level.player
    if player.is_centred:
        return player.anchor
    return (player.anchor[0] + player.direction.dx,
            player.anchor[1] + player.direction.dy)


def clear_time(config: Config, number: int, cheats: Cheats) -> float:
    """Return the seconds an optimal player needs to clear a level."""
    session, error = new_session(config, cheats)
    if session is None:
        raise SystemExit("error: %s" % error)
    while session.level_number < number:
        session.level.skip()
        for _ in range(400):
            session.update(FRAME)
    level = session.level
    total = level.remaining_pacgums
    level.time_left = TIME_OUT * 2.0
    elapsed = 0.0
    goal: Optional[Tile] = None
    while level.remaining_pacgums and elapsed < TIME_OUT:
        dots = level.pacgums | level.supers
        reference = _reference_tile(level)
        if goal is None or goal not in dots:
            goal, _ = search(level.maze, reference, dots)
            if goal is None:
                break
        _, step = search(level.maze, reference, {goal})
        if not step.is_none:
            level.player.steer(step)
        level.update(FRAME, cheats)
        elapsed += FRAME
    _report(number, total, level, elapsed, config)
    return elapsed


def _report(number: int, total: int, level: Level, elapsed: float,
            config: Config) -> None:
    """Print one line summarising a measured level."""
    limit = config.levels[number - 1].max_time if config.levels else 90.0
    if elapsed < limit * 0.7:
        verdict = "OK"
    elif elapsed < limit:
        verdict = "TIGHT"
    else:
        verdict = "FAIL"
    print("level %2d: %3d dots %5d corridors  cleared in %5.1fs / %3.0fs  %s"
          % (number, total, len(level.maze.open_tiles), elapsed, limit,
             verdict))


def main() -> int:
    """Measure every level of the configuration given on the command line."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _ROOT / "config.json"
    config, _ = load_config(path)
    cheats = Cheats(enabled=True, invincible=True)
    for number in range(1, config.level_count + 1):
        clear_time(config, number, cheats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
