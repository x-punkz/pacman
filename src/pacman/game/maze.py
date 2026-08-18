"""The playfield: a grid of walls and corridors.

The A-Maze-ing package describes a maze as cells carrying wall bits.
Pac-Man instead needs corridors one tile wide, so a maze of
``width x height`` cells is expanded into a ``(2*width+1) x
(2*height+1)`` tile grid: odd coordinates are cell centres, even ones
are the walls between them.
"""

from collections import deque
from typing import Final, Iterable, Iterator, Optional

from .direction import DIRECTIONS

WALL: Final = 0
CORRIDOR: Final = 1

NORTH_WALL: Final = 1
EAST_WALL: Final = 2
SOUTH_WALL: Final = 4
WEST_WALL: Final = 8
ISOLATED_CELL: Final = 15

Tile = tuple[int, int]


class MazeError(Exception):
    """Raised when the generated cell grid cannot be used."""


class Maze:
    """A rectangular grid of walls and corridors."""

    __slots__ = ("width", "height", "_tiles", "_open", "player_start",
                 "corners")

    def __init__(self, tiles: list[bytearray]) -> None:
        """Wrap a ready-made tile grid and derive the spawn points."""
        if not tiles or not tiles[0]:
            raise MazeError("the maze is empty")
        self.height = len(tiles)
        self.width = len(tiles[0])
        self._tiles = tiles
        self._open: tuple[Tile, ...] = tuple(
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if tiles[y][x] == CORRIDOR)
        if not self._open:
            raise MazeError("the maze has no corridor at all")
        self.player_start: Tile = self._closest_open(
            self.width // 2, self.height // 2, ())
        self.corners: tuple[Tile, ...] = self._pick_corners()

    def is_open(self, x: int, y: int) -> bool:
        """Return ``True`` when the tile can be walked on."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._tiles[y][x] == CORRIDOR
        return False

    def is_wall(self, x: int, y: int) -> bool:
        """Return ``True`` when the tile blocks movement."""
        return not self.is_open(x, y)

    @property
    def open_tiles(self) -> tuple[Tile, ...]:
        """Return every walkable tile of the maze."""
        return self._open

    def rows(self) -> Iterator[bytearray]:
        """Iterate over the raw tile rows, top to bottom."""
        return iter(self._tiles)

    def to_ascii(self) -> str:
        """Render the maze as text; handy for tests and debugging."""
        return "\n".join(
            "".join("#" if tile == WALL else " " for tile in row)
            for row in self._tiles)

    def _closest_open(self, x: int, y: int, taken: Iterable[Tile]) -> Tile:
        """Return the free corridor tile closest to (*x*, *y*)."""
        excluded = set(taken)
        best: Optional[Tile] = None
        best_score = 0
        for tile in self._open:
            if tile in excluded:
                continue
            score = abs(tile[0] - x) + abs(tile[1] - y)
            if best is None or score < best_score:
                best, best_score = tile, score
        if best is None:
            return self._open[0]
        return best

    def _pick_corners(self) -> tuple[Tile, ...]:
        """Return four distinct corridor tiles, one per maze corner."""
        anchors = ((1, 1), (self.width - 2, 1),
                   (1, self.height - 2), (self.width - 2, self.height - 2))
        chosen: list[Tile] = []
        for anchor_x, anchor_y in anchors:
            chosen.append(self._closest_open(anchor_x, anchor_y, chosen))
        return tuple(chosen)


def from_cells(cells: list[list[int]]) -> Maze:
    """Expand an A-Maze-ing cell grid into a Pac-Man tile grid.

    Args:
        cells: The ``MazeGenerator.maze`` property, a grid of wall bit
            fields indexed as ``cells[row][column]``.

    Returns:
        A :class:`Maze` whose corridors are all reachable from one
        another.

    Raises:
        MazeError: When the grid is empty or not rectangular.
    """
    cell_height = len(cells)
    if cell_height == 0:
        raise MazeError("the generator returned an empty maze")
    cell_width = len(cells[0])
    if cell_width == 0:
        raise MazeError("the generator returned an empty maze")
    for row in cells:
        if len(row) != cell_width:
            raise MazeError("the generator returned a ragged maze")

    width = cell_width * 2 + 1
    height = cell_height * 2 + 1
    tiles = [bytearray(width) for _ in range(height)]

    for cell_y in range(cell_height):
        for cell_x in range(cell_width):
            if int(cells[cell_y][cell_x]) == ISOLATED_CELL:
                continue
            tiles[cell_y * 2 + 1][cell_x * 2 + 1] = CORRIDOR
            if _opens_east(cells, cell_x, cell_y, cell_width):
                tiles[cell_y * 2 + 1][cell_x * 2 + 2] = CORRIDOR
            if _opens_south(cells, cell_x, cell_y, cell_height):
                tiles[cell_y * 2 + 2][cell_x * 2 + 1] = CORRIDOR

    _keep_largest_area(tiles, width, height)
    return Maze(tiles)


def _opens_east(cells: list[list[int]], x: int, y: int, width: int) -> bool:
    """Return ``True`` when both cells agree the east wall is gone."""
    if x + 1 >= width:
        return False
    here = int(cells[y][x])
    there = int(cells[y][x + 1])
    if here == ISOLATED_CELL or there == ISOLATED_CELL:
        return False
    return not (here & EAST_WALL) and not (there & WEST_WALL)


def _opens_south(cells: list[list[int]], x: int, y: int, height: int) -> bool:
    """Return ``True`` when both cells agree the south wall is gone."""
    if y + 1 >= height:
        return False
    here = int(cells[y][x])
    there = int(cells[y + 1][x])
    if here == ISOLATED_CELL or there == ISOLATED_CELL:
        return False
    return not (here & SOUTH_WALL) and not (there & NORTH_WALL)


def _keep_largest_area(tiles: list[bytearray], width: int,
                       height: int) -> None:
    """Wall off every corridor that is not part of the main area.

    The '42' pattern the generator carves into the maze leaves small
    isolated pockets behind.  Keeping only the biggest connected area
    guarantees that every pacgum can be reached by the player.
    """
    seen = [bytearray(width) for _ in range(height)]
    best: list[Tile] = []
    for start_y in range(height):
        for start_x in range(width):
            if tiles[start_y][start_x] != CORRIDOR or seen[start_y][start_x]:
                continue
            area = _flood(tiles, seen, start_x, start_y, width, height)
            if len(area) > len(best):
                best = area
    keep = set(best)
    for y in range(height):
        for x in range(width):
            if tiles[y][x] == CORRIDOR and (x, y) not in keep:
                tiles[y][x] = WALL


def _flood(tiles: list[bytearray], seen: list[bytearray], start_x: int,
           start_y: int, width: int, height: int) -> list[Tile]:
    """Collect the corridor tiles connected to (*start_x*, *start_y*)."""
    seen[start_y][start_x] = 1
    area: list[Tile] = [(start_x, start_y)]
    queue = deque(area)
    while queue:
        x, y = queue.popleft()
        for step in DIRECTIONS:
            next_x, next_y = x + step.dx, y + step.dy
            if not (0 <= next_x < width and 0 <= next_y < height):
                continue
            if seen[next_y][next_x] or tiles[next_y][next_x] != CORRIDOR:
                continue
            seen[next_y][next_x] = 1
            area.append((next_x, next_y))
            queue.append((next_x, next_y))
    return area
