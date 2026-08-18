"""Hand-made cell grids used by the tests.

Wall bits, as documented by the A-Maze-ing package: 1 north, 2 east,
4 south, 8 west.
"""

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8


def open_field(width: int, height: int) -> list[list[int]]:
    """Return a grid whose inner walls are all removed."""
    cells: list[list[int]] = []
    for y in range(height):
        row: list[int] = []
        for x in range(width):
            value = 0
            value |= NORTH if y == 0 else 0
            value |= SOUTH if y == height - 1 else 0
            value |= WEST if x == 0 else 0
            value |= EAST if x == width - 1 else 0
            row.append(value)
        cells.append(row)
    return cells


def corridor(length: int) -> list[list[int]]:
    """Return a single east-west corridor of *length* cells."""
    row = [NORTH | SOUTH] * length
    row[0] |= WEST
    row[-1] |= EAST
    return [row]
