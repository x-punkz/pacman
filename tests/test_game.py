"""Tests for the moving parts: entities, ghosts, levels and sessions."""

import random
from typing import Any

from pacman.game import direction as compass
from pacman.game.cheats import Cheats
from pacman.game.entities import Player
from pacman.game.ghosts import GhostKind, GhostState, build_ghosts
from pacman.game.level import LevelOutcome, build
from pacman.game.maze import Maze, from_cells
from pacman.game.session import SessionState, new_session
from pacman.settings import Config, LevelSpec

from .mazes import corridor, open_field


def small_maze() -> Maze:
    """Return a small, fully connected maze."""
    return from_cells(open_field(9, 7))


def make_config(**overrides: Any) -> Config:
    """Return a configuration made of ten identical small levels."""
    levels = tuple(LevelSpec(15, 11, 6, 90.0) for _ in range(10))
    return Config(levels=levels, **overrides)


def test_player_walks_towards_the_next_tile() -> None:
    """A mover slides from tile centre to tile centre."""
    maze = from_cells(corridor(5))
    player = Player((1, 1), speed=1.0)
    player.steer(compass.RIGHT)
    player.update(0.5, maze)
    assert 1.4 < player.x < 1.6
    player.update(0.5, maze)
    assert player.tile == (2, 1)
    assert player.is_centred


def test_player_cannot_walk_into_a_wall() -> None:
    """Walking into a wall simply stops the player."""
    maze = from_cells(corridor(5))
    player = Player((1, 1), speed=4.0)
    player.steer(compass.UP)
    player.update(1.0, maze)
    assert player.tile == (1, 1)


def test_turn_is_buffered_until_it_becomes_possible() -> None:
    """A direction pressed early is applied at the next opening."""
    cells = open_field(3, 2)
    cells[1][0] = 15
    cells[1][2] = 15
    maze = from_cells(cells)
    player = Player((3, 1), speed=2.0)
    player.steer(compass.DOWN)
    player.update(2.0, maze)
    assert player.tile[1] > 1


def test_ghosts_start_in_their_corner() -> None:
    """One ghost per corner, in the canonical order."""
    maze = small_maze()
    ghosts = build_ghosts(maze.corners, 4.0, 2.0)
    assert [ghost.kind for ghost in ghosts] == list(GhostKind)
    assert [ghost.tile for ghost in ghosts] == list(maze.corners)


def test_super_pacgum_makes_every_ghost_edible() -> None:
    """Eating a power pellet flips the whole board."""
    level = build(make_config(), 1, small_maze(), random.Random(1))
    for ghost in level.ghosts:            # away from the corner pellets
        ghost.place(level.maze.player_start)
    level.player.place(sorted(level.supers)[0])
    level.update(0.001, Cheats())
    assert all(ghost.is_edible for ghost in level.ghosts)
    assert level.frightened_left > 0.0


def test_eating_an_edible_ghost_scores_and_sends_it_home() -> None:
    """An edible ghost is worth points and goes back to its corner."""
    config = make_config()
    level = build(config, 1, small_maze(), random.Random(1))
    ghost = level.ghosts[0]
    ghost.place(level.maze.player_start)  # not on a corner pellet
    ghost.frighten(5.0)
    level.player.place(ghost.tile)
    events = level.update(0.001, Cheats())
    assert events.ghosts == 1
    assert events.score >= config.points_per_ghost
    assert ghost.state is GhostState.EATEN
    assert ghost.tile == ghost.home


def test_touching_a_ghost_costs_a_life() -> None:
    """A hunting ghost ends the run."""
    level = build(make_config(), 1, small_maze(), random.Random(1))
    ghost = level.ghosts[0]
    ghost.state = GhostState.CHASE
    ghost.place(level.player.tile)
    events = level.update(0.001, Cheats())
    assert events.outcome is LevelOutcome.LIFE_LOST


def test_invincibility_cheat_protects_the_player() -> None:
    """The cheat switch really disables the collision."""
    level = build(make_config(), 1, small_maze(), random.Random(1))
    ghost = level.ghosts[0]
    ghost.state = GhostState.CHASE
    ghost.place(level.player.tile)
    cheats = Cheats(enabled=True, invincible=True)
    assert level.update(0.001, cheats).outcome is LevelOutcome.RUNNING


def test_level_is_cleared_when_every_dot_is_gone() -> None:
    """Clearing the board reports the right outcome."""
    level = build(make_config(), 1, small_maze(), random.Random(1))
    level.skip()
    assert level.update(0.001, Cheats()).outcome is LevelOutcome.CLEARED


def test_running_out_of_time_is_reported() -> None:
    """The level clock is enforced."""
    level = build(make_config(), 1, small_maze(), random.Random(1))
    level.time_left = 0.001
    assert level.update(0.5, Cheats()).outcome is LevelOutcome.TIMED_OUT


def test_pacgum_count_follows_the_configuration() -> None:
    """The configured number of dots is what lands on the board."""
    config = make_config()
    level = build(config, 1, small_maze(), random.Random(7))
    assert len(level.pacgums) == config.levels[0].pacgum
    assert len(level.supers) == 4


def test_zero_pacgum_fills_every_corridor() -> None:
    """The documented '0 means fill everything' behaviour."""
    config = Config(levels=(LevelSpec(15, 11, 0, 90.0),))
    maze = small_maze()
    level = build(config, 1, maze, random.Random(1))
    assert level.remaining_pacgums == len(maze.open_tiles) - 1


def test_first_maze_is_reproducible() -> None:
    """A fixed seed always produces the very same first level."""
    config = make_config(seed=42)
    first, _ = new_session(config, Cheats())
    second, _ = new_session(config, Cheats())
    assert first is not None and second is not None
    assert first.level.maze.to_ascii() == second.level.maze.to_ascii()


def test_session_reaches_victory_when_every_level_is_cleared() -> None:
    """Clearing all ten levels wins the game."""
    session, error = new_session(make_config(), Cheats())
    assert session is not None and error == ""
    for _ in range(400):
        if session.state is SessionState.VICTORY:
            break
        session.level.skip()
        session.update(0.5)
    assert session.state is SessionState.VICTORY
    assert session.won


def test_session_ends_when_every_life_is_lost() -> None:
    """Losing every life ends the game."""
    session, _ = new_session(make_config(lives=1), Cheats())
    assert session is not None
    session.banner_left = 0.0
    session.state = SessionState.PLAYING
    ghost = session.level.ghosts[0]
    ghost.state = GhostState.CHASE
    ghost.place(session.level.player.tile)
    session.update(0.001)
    assert session.state is SessionState.GAME_OVER
    assert session.is_over
