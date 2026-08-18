"""Adapter around the assigned A-Maze-ing package.

The subject forbids writing our own generator and forbids touching the
assigned one, so this module is deliberately defensive: it discovers
the constructor signature at run time and only passes the arguments
that the installed package actually accepts.  If their interface
differs slightly from the one we developed against, the loader adapts
instead of the package.
"""

import inspect
from typing import Any, Optional

from .maze import Maze, MazeError, from_cells

PACKAGE_NAME = "mazegenerator"
CLASS_NAME = "MazeGenerator"

_INSTALL_HINT = (
    "install the A-Maze-ing package assigned to the group, for example "
    "'pip install mazegenerator-2.1.0-py3-none-any.whl'")

_GRID_ATTRIBUTES = ("maze", "grid", "cells", "get_maze", "get_grid")


class GeneratorError(Exception):
    """Raised when no maze can be obtained from the package."""


def load_generator_class() -> Any:
    """Import the assigned package and return its generator class.

    Raises:
        GeneratorError: When the package is missing or does not expose
            a ``MazeGenerator`` class.
    """
    try:
        module = __import__(PACKAGE_NAME, fromlist=[CLASS_NAME])
    except ImportError as error:
        raise GeneratorError(
            "the '%s' package is not installed (%s); %s"
            % (PACKAGE_NAME, error, _INSTALL_HINT)) from error
    generator = getattr(module, CLASS_NAME, None)
    if generator is None or not callable(generator):
        raise GeneratorError(
            "the '%s' package does not expose a callable '%s'"
            % (PACKAGE_NAME, CLASS_NAME))
    return generator


def generate(width: int, height: int, seed: int = 0) -> Maze:
    """Build a Pac-Man playfield of *width* x *height* generator cells.

    Args:
        width: Number of maze cells on the horizontal axis.
        height: Number of maze cells on the vertical axis.
        seed: Seed handed to the generator; ``0`` means fully random,
            which is how the package itself defines it.

    Returns:
        A ready to play :class:`~pacman.game.maze.Maze`.

    Raises:
        GeneratorError: When the package fails or returns something
            unusable.
    """
    generator_class = load_generator_class()
    try:
        instance = _instantiate(generator_class, width, height, seed)
        cells = _extract_grid(instance)
    except GeneratorError:
        raise
    except Exception as error:
        raise GeneratorError(
            "the maze generator failed for a %dx%d maze (%s: %s)"
            % (width, height, type(error).__name__, error)) from error
    try:
        return from_cells(cells)
    except MazeError as error:
        raise GeneratorError(
            "the generated maze cannot be used (%s)" % error) from error


def _instantiate(generator_class: Any, width: int, height: int,
                 seed: int) -> Any:
    """Call the generator with whatever arguments it understands."""
    accepted = _accepted_parameters(generator_class)
    kwargs: dict[str, Any] = {}
    if "size" in accepted:
        kwargs["size"] = (width, height)
    else:
        if "width" in accepted:
            kwargs["width"] = width
        if "height" in accepted:
            kwargs["height"] = height
    if "perfect" in accepted:
        # Mandated by the subject: imperfect mazes give Pac-Man the
        # loops it needs, and no dead end can trap the player.
        kwargs["perfect"] = False
    if "seed" in accepted:
        kwargs["seed"] = seed
    if kwargs:
        return generator_class(**kwargs)
    return generator_class((width, height))


def _accepted_parameters(generator_class: Any) -> frozenset[str]:
    """Return the keyword arguments the constructor accepts."""
    try:
        signature = inspect.signature(generator_class)
    except (TypeError, ValueError):  # pragma: no cover - exotic callables
        return frozenset(("size", "perfect", "seed"))
    names = set()
    for name, parameter in signature.parameters.items():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            return frozenset(("size", "width", "height", "perfect", "seed"))
        if parameter.kind is not inspect.Parameter.VAR_POSITIONAL:
            names.add(name)
    return frozenset(names)


def _extract_grid(instance: Any) -> list[list[int]]:
    """Pull the cell grid out of the generator instance."""
    raw: Optional[Any] = None
    for name in _GRID_ATTRIBUTES:
        candidate = getattr(instance, name, None)
        if candidate is None:
            continue
        raw = candidate() if callable(candidate) else candidate
        if raw:
            break
    if not raw:
        raise GeneratorError(
            "the generator did not expose a maze grid (looked for %s)"
            % ", ".join(_GRID_ATTRIBUTES))
    try:
        return [[int(cell) for cell in row] for row in raw]
    except (TypeError, ValueError) as error:
        raise GeneratorError(
            "the generator returned a grid of non-integers (%s)"
            % error) from error
