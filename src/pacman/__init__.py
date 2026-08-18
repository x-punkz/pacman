"""Pac-Man: a 42 school project.

The package is organised in four independent layers:

``pacman.mlxlib``
    A minimal, MLX-like graphics layer (window, image buffer, hooks,
    event loop).  Every public function has a direct MiniLibX
    equivalent; see ``pacman/mlxlib/mlx.py`` for the mapping table.
``pacman.settings`` / ``pacman.jsonc``
    Configuration parsing (JSON with comments) and validation.
``pacman.game``
    Pure game logic: maze, entities, ghosts, levels, session.
``pacman.ui``
    Everything that turns the game state into pixels.
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
