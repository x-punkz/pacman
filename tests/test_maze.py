"""Tests for the cell grid to tile grid conversion."""

import pytest

from pacman.game.maze import CORRIDOR, MazeError, from_cells

from .mazes import EAST, WEST, corridor, open_field


def test_tile_grid_size() -> None:
    """A w x h cell maze becomes a (2w+1) x (2h+1) tile maze."""
    maze = from_cells(corridor(3))
    assert (maze.width, maze.height) == (7, 3)


def test_corridor_is_carved_between_open_cells() -> None:
    """Two cells that agree on an open wall are linked."""
    maze = from_cells(corridor(3))
    assert maze.is_open(1, 1) and maze.is_open(2, 1) and maze.is_open(3, 1)


def test_wall_needs_both_cells_to_agree() -> None:
    """A one-sided opening stays closed."""
    # left cell has no east wall, right cell still has its west wall
    maze = from_cells([[1 + 4 + WEST, 1 + 4 + WEST, 1 + 4 + EAST]])
    assert maze.is_wall(2, 1)


def test_borders_are_walls() -> None:
    """The outer ring of the tile grid is always solid."""
    maze = from_cells(corridor(3))
    for x in range(maze.width):
        assert maze.is_wall(x, 0) and maze.is_wall(x, maze.height - 1)
    for y in range(maze.height):
        assert maze.is_wall(0, y) and maze.is_wall(maze.width - 1, y)


def test_isolated_cells_become_walls() -> None:
    """The '42' pattern cells are solid, never unreachable pockets."""
    maze = from_cells([[1 + 4 + WEST, 15, 1 + 4 + EAST]])
    assert maze.is_wall(3, 1)


def test_only_the_largest_area_is_kept() -> None:
    """Corridors cut off from the main area are walled off."""
    row = corridor(5)[0]
    row[3] = 15
    maze = from_cells([row])
    assert all(maze.is_open(*tile) for tile in maze.open_tiles)
    assert maze.is_wall(9, 1)


def test_spawn_points_are_walkable_and_distinct() -> None:
    """The player and the four corners land on real corridors."""
    maze = from_cells(open_field(5, 3))
    assert maze.is_open(*maze.player_start)
    assert len(maze.corners) == 4
    assert len(set(maze.corners)) == 4
    for corner in maze.corners:
        assert maze.is_open(*corner)


def test_empty_grid_is_reported() -> None:
    """An empty grid raises a clear error."""
    with pytest.raises(MazeError):
        from_cells([])


def test_ragged_grid_is_reported() -> None:
    """A grid whose rows differ in length raises a clear error."""
    with pytest.raises(MazeError):
        from_cells([[10, 10], [10]])


def test_ascii_dump_matches_the_grid() -> None:
    """The debug dump agrees with the tile values."""
    maze = from_cells(corridor(3))
    lines = maze.to_ascii().splitlines()
    for y, row in enumerate(maze.rows()):
        for x, value in enumerate(row):
            expected = " " if value == CORRIDOR else "#"
            assert lines[y][x] == expected
