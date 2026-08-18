"""Turning the game state into a frame buffer."""

import math
from dataclasses import dataclass
from typing import Optional

from ..game.cheats import Cheats
from ..game.ghosts import Ghost
from ..game.level import Level
from ..game.maze import CORRIDOR, Maze
from ..game.session import Session
from ..mlxlib import Mlx
from ..mlxlib.image import Image
from . import sprites, theme


@dataclass(frozen=True)
class Layout:
    """Where the maze sits inside the window."""

    tile: int
    origin_x: int
    origin_y: int

    def screen_x(self, tile_x: float) -> int:
        """Return the pixel column of the centre of *tile_x*."""
        return int(self.origin_x + (tile_x + 0.5) * self.tile)

    def screen_y(self, tile_y: float) -> int:
        """Return the pixel row of the centre of *tile_y*."""
        return int(self.origin_y + (tile_y + 0.5) * self.tile)


class Renderer:
    """Owns the frame buffer and knows how to fill it."""

    def __init__(self, mlx: Mlx, width: int, height: int) -> None:
        """Allocate the frame and background images."""
        self.mlx = mlx
        self.width = width
        self.height = height
        self.frame = mlx.new_image(width, height)
        self._background = mlx.new_image(width, height)
        self._layout = Layout(theme.MIN_TILE, 0, 0)
        self._maze: Optional[Maze] = None

    @property
    def layout(self) -> Layout:
        """Return the layout computed for the current maze."""
        return self._layout

    def text(self, x: int, y: int, message: str, color: int = theme.TEXT,
             scale: int = 1) -> None:
        """Draw *message* with its top-left corner at (*x*, *y*)."""
        self.mlx.string_put(self.frame, x, y, color, message, scale)

    def text_center(self, y: int, message: str, color: int = theme.TEXT,
                    scale: int = 1) -> None:
        """Draw *message* horizontally centred on the window."""
        width = self.mlx.text_width(message, scale)
        self.text((self.width - width) // 2, y, message, color, scale)

    def text_right(self, right: int, y: int, message: str,
                   color: int = theme.TEXT, scale: int = 1) -> None:
        """Draw *message* so that it ends at the *right* column."""
        width = self.mlx.text_width(message, scale)
        self.text(right - width, y, message, color, scale)

    def clear(self, color: int = theme.BACKGROUND) -> None:
        """Blank the frame buffer."""
        self.mlx.clear_window(self.frame, color)

    def present(self) -> None:
        """Push the frame buffer to the window."""
        self.mlx.put_image_to_window(self.frame, 0, 0)

    def prepare(self, maze: Maze) -> None:
        """Compute the layout for *maze* and cache its walls."""
        self._maze = maze
        self._layout = _compute_layout(maze, self.width, self.height)
        self._background.clear(theme.BACKGROUND)
        _paint_walls(self._background, maze, self._layout)

    def draw_level(self, level: Level, cheats: Cheats,
                   clock: float) -> None:
        """Draw the maze, the dots, the ghosts and the player."""
        if self._maze is not level.maze:
            self.prepare(level.maze)
        self.frame.copy_from(self._background)
        layout = self._layout
        pulse = 0.5 + 0.5 * math.sin(clock * 6.0)
        radius = max(1, layout.tile // 8)
        for tile_x, tile_y in level.pacgums:
            sprites.draw_pacgum(self.frame, layout.screen_x(tile_x),
                                layout.screen_y(tile_y), radius)
        big = max(2, layout.tile // 3)
        for tile_x, tile_y in level.supers:
            sprites.draw_super_pacgum(self.frame, layout.screen_x(tile_x),
                                      layout.screen_y(tile_y), big, pulse)
        if cheats.targets_visible:
            self._draw_targets(level)
        for ghost in level.ghosts:
            self._draw_ghost(ghost, layout)
        player = level.player
        sprites.draw_pacman(self.frame, layout.screen_x(player.x),
                            layout.screen_y(player.y),
                            max(2, int(layout.tile * 0.42)),
                            player.direction, player.mouth_openness)

    def _draw_ghost(self, ghost: Ghost, layout: Layout) -> None:
        """Draw one ghost, or just its eyes when it has been eaten."""
        x = layout.screen_x(ghost.x)
        y = layout.screen_y(ghost.y)
        size = max(4, int(layout.tile * 0.82))
        if not ghost.is_active:
            sprites.draw_eyes(self.frame, x, y, max(3, size // 2),
                              ghost.direction)
            return
        sprites.draw_ghost(self.frame, x, y, size,
                           theme.ghost_color(ghost.kind), ghost.direction,
                           ghost.is_edible, ghost.is_flashing)

    def _draw_targets(self, level: Level) -> None:
        """Mark where each ghost is heading; a cheat-mode helper."""
        layout = self._layout
        marker = max(2, layout.tile // 4)
        for ghost in level.ghosts:
            if not ghost.is_active:
                continue
            self.frame.rect_outline(
                layout.screen_x(ghost.target[0]) - marker,
                layout.screen_y(ghost.target[1]) - marker,
                marker * 2, marker * 2, theme.ghost_color(ghost.kind))

    def dim_screen(self, factor: float = 0.35) -> None:
        """Darken the whole frame, used behind the overlays."""
        self.frame.dim_rect(0, 0, self.width, self.height, factor)

    def banner(self, session: Session) -> None:
        """Draw the READY / LEVEL COMPLETE style message."""
        if session.banner_left <= 0.0:
            return
        message = session.banner
        scale = 3
        width = self.mlx.text_width(message, scale)
        height = self.mlx.text_height(scale)
        left = (self.width - width) // 2
        top = self.height // 2 - height
        self.frame.fill_rect(left - 18, top - 14, width + 36, height + 28,
                             theme.PANEL)
        self.frame.rect_outline(left - 18, top - 14, width + 36,
                                height + 28, theme.ACCENT)
        self.text(left, top, message, theme.ACCENT, scale)


def _compute_layout(maze: Maze, width: int, height: int) -> Layout:
    """Fit the maze between the HUD and the footer, centred."""
    usable_width = max(1, width - 2 * theme.MARGIN)
    usable_height = max(1, height - theme.HUD_HEIGHT
                        - theme.FOOTER_HEIGHT - 2 * theme.MARGIN)
    tile = min(usable_width // maze.width, usable_height // maze.height)
    tile = max(theme.MIN_TILE, min(theme.MAX_TILE, tile))
    origin_x = (width - maze.width * tile) // 2
    spare = usable_height - maze.height * tile
    origin_y = theme.HUD_HEIGHT + theme.MARGIN + max(0, spare // 2)
    return Layout(tile, origin_x, origin_y)


def _paint_walls(image: Image, maze: Maze, layout: Layout) -> None:
    """Paint the maze walls as connected rounded blocks."""
    tile = layout.tile
    pad = max(1, tile // 4)
    for y, row in enumerate(maze.rows()):
        for x, value in enumerate(row):
            if value == CORRIDOR:
                continue
            left = layout.origin_x + x * tile
            top = layout.origin_y + y * tile
            _blob(image, maze, x, y, left, top, tile, pad - 1
                  if pad > 1 else pad, theme.WALL_EDGE)
            _blob(image, maze, x, y, left, top, tile, pad, theme.WALL)


def _blob(image: Image, maze: Maze, x: int, y: int, left: int, top: int,
          tile: int, pad: int, color: int) -> None:
    """Draw one wall tile and its links to the neighbouring walls."""
    inner = max(1, tile - 2 * pad)
    image.fill_rect(left + pad, top + pad, inner, inner, color)
    if x + 1 < maze.width and maze.is_wall(x + 1, y):
        image.fill_rect(left + tile - pad, top + pad, pad * 2, inner, color)
    if y + 1 < maze.height and maze.is_wall(x, y + 1):
        image.fill_rect(left + pad, top + tile - pad, inner, pad * 2, color)
    if (x + 1 < maze.width and y + 1 < maze.height
            and maze.is_wall(x + 1, y) and maze.is_wall(x, y + 1)
            and maze.is_wall(x + 1, y + 1)):
        image.fill_rect(left + tile - pad, top + tile - pad, pad * 2,
                        pad * 2, color)
