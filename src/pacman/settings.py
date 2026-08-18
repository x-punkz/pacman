"""Configuration loading, validation and clamping.

The subject demands that a faulty configuration never crashes the
game: every value is range-checked, every rejected value falls back to
a documented default, every problem is reported once and the game
keeps going.  Unknown keys are ignored.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .jsonc import JsoncError, load_file

MIN_LEVELS = 10
MIN_CELLS = 7
MAX_CELLS = 45

DEFAULT_LEVEL_SIZES: tuple[tuple[int, int], ...] = (
    (15, 11), (15, 11), (17, 13), (17, 13), (19, 13),
    (19, 15), (21, 15), (21, 17), (23, 17), (23, 19),
)

_CORE_KEYS = frozenset((
    "highscore_filename", "levels", "level", "lives", "pacgum",
    "points_per_pacgum", "points_per_super_pacgum", "points_per_ghost",
    "seed", "level_max_time",
))

_EXTRA_KEYS = frozenset((
    "player_speed", "ghost_speed", "ghost_speed_step",
    "ghost_frightened_speed", "super_pacgum_duration",
    "ghost_respawn_delay", "scatter_duration", "ghost_score_doubling",
    "timeout_costs_life", "cheat_mode", "window_width", "window_height",
    "target_fps", "backend", "highscore_size",
))

_LEVEL_KEYS = frozenset(("width", "height", "pacgum", "max_time"))


@dataclass(frozen=True)
class LevelSpec:
    """The maze size and goals of a single level."""

    width: int
    height: int
    pacgum: int
    max_time: float


@dataclass(frozen=True)
class Config:
    """Every tunable value of the game, already validated."""

    source: Path = Path("config.json")
    highscore_path: Path = Path("highscores.json")
    highscore_size: int = 10
    lives: int = 3
    pacgum: int = 42
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: float = 90.0
    levels: tuple[LevelSpec, ...] = field(default_factory=tuple)
    player_speed: float = 6.0
    ghost_speed: float = 5.0
    ghost_speed_step: float = 0.15
    ghost_frightened_speed: float = 3.2
    super_pacgum_duration: float = 8.0
    ghost_respawn_delay: float = 6.0
    scatter_duration: float = 7.0
    ghost_score_doubling: bool = False
    timeout_costs_life: bool = True
    cheat_mode: bool = False
    window_width: int = 960
    window_height: int = 720
    target_fps: int = 60
    backend: str = "auto"

    @property
    def level_count(self) -> int:
        """Return how many levels the game is made of."""
        return len(self.levels)


class ConfigError(Exception):
    """Raised only when the file cannot be used at all."""


class _Reader:
    """Pull typed values out of a raw mapping, clamping as it goes."""

    def __init__(self, raw: dict[str, Any], warnings: list[str],
                 where: str = "") -> None:
        """Wrap *raw*, appending every complaint to *warnings*."""
        self._raw = raw
        self._warnings = warnings
        self._where = where

    def warn(self, message: str) -> None:
        """Record a human readable message about the configuration."""
        self._warnings.append("%s%s" % (self._where, message))

    def integer(self, key: str, default: int, minimum: int, maximum: int,
                required: bool = True) -> int:
        """Read an integer, clamped to the given range."""
        if key not in self._raw:
            if required:
                self.warn("missing key '%s', using %d" % (key, default))
            return default
        value = self._raw[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self.warn("key '%s' must be a number, using %d" % (key, default))
            return default
        number = int(value)
        if number < minimum or number > maximum:
            clamped = max(minimum, min(maximum, number))
            self.warn("key '%s' out of range [%d, %d], clamped to %d"
                      % (key, minimum, maximum, clamped))
            return clamped
        return number

    def number(self, key: str, default: float, minimum: float,
               maximum: float, required: bool = True) -> float:
        """Read a float, clamped to the given range."""
        if key not in self._raw:
            if required:
                self.warn("missing key '%s', using %s" % (key, default))
            return default
        value = self._raw[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self.warn("key '%s' must be a number, using %s" % (key, default))
            return default
        number = float(value)
        if number < minimum or number > maximum:
            clamped = max(minimum, min(maximum, number))
            self.warn("key '%s' out of range [%s, %s], clamped to %s"
                      % (key, minimum, maximum, clamped))
            return clamped
        return number

    def flag(self, key: str, default: bool) -> bool:
        """Read a boolean, accepting the usual textual spellings."""
        if key not in self._raw:
            return default
        value = self._raw[key]
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in ("true", "yes", "on", "1"):
                return True
            if lowered in ("false", "no", "off", "0"):
                return False
        self.warn("key '%s' must be a boolean, using %s" % (key, default))
        return default

    def text(self, key: str, default: str, required: bool = True) -> str:
        """Read a non-empty string."""
        if key not in self._raw:
            if required:
                self.warn("missing key '%s', using '%s'" % (key, default))
            return default
        value = self._raw[key]
        if not isinstance(value, str) or not value.strip():
            self.warn("key '%s' must be a non-empty string, using '%s'"
                      % (key, default))
            return default
        return value.strip()


def default_config() -> Config:
    """Return a fully playable configuration with the built-in levels."""
    defaults = Config()
    return Config(levels=tuple(
        LevelSpec(width, height, defaults.pacgum, defaults.level_max_time)
        for width, height in DEFAULT_LEVEL_SIZES))


def load_config(path: Path) -> tuple[Config, list[str]]:
    """Load *path* and return the configuration plus its warnings.

    Args:
        path: The JSON-with-comments file given on the command line.

    Returns:
        A validated :class:`Config` and the messages produced while
        reading it.

    Raises:
        ConfigError: When the file is unreadable or is not a JSON
            object.  Every other problem is downgraded to a warning.
    """
    try:
        raw = load_file(path)
    except JsoncError as error:
        raise ConfigError(str(error)) from error
    if not isinstance(raw, dict):
        raise ConfigError(
            "the configuration must be a JSON object, found %s"
            % type(raw).__name__)
    warnings: list[str] = []
    reader = _Reader(raw, warnings)
    defaults = Config()
    _report_unknown_keys(raw, reader)

    highscore_name = reader.text("highscore_filename", "highscores.json")
    pacgum = reader.integer("pacgum", defaults.pacgum, 0, 100000)
    level_max_time = reader.number("level_max_time", defaults.level_max_time,
                                   5.0, 3600.0)
    config = Config(
        source=path,
        highscore_path=_resolve_highscore(path, highscore_name),
        highscore_size=reader.integer("highscore_size",
                                      defaults.highscore_size, 1, 100,
                                      required=False),
        lives=reader.integer("lives", defaults.lives, 1, 99),
        pacgum=pacgum,
        points_per_pacgum=reader.integer(
            "points_per_pacgum", defaults.points_per_pacgum, 0, 100000),
        points_per_super_pacgum=reader.integer(
            "points_per_super_pacgum", defaults.points_per_super_pacgum,
            0, 100000),
        points_per_ghost=reader.integer(
            "points_per_ghost", defaults.points_per_ghost, 0, 100000),
        seed=reader.integer("seed", defaults.seed, 0, 2 ** 31 - 1),
        level_max_time=level_max_time,
        levels=_read_levels(raw, warnings, pacgum, level_max_time),
        player_speed=reader.number("player_speed", defaults.player_speed,
                                   1.0, 30.0, required=False),
        ghost_speed=reader.number("ghost_speed", defaults.ghost_speed,
                                  0.5, 30.0, required=False),
        ghost_speed_step=reader.number(
            "ghost_speed_step", defaults.ghost_speed_step, 0.0, 5.0,
            required=False),
        ghost_frightened_speed=reader.number(
            "ghost_frightened_speed", defaults.ghost_frightened_speed,
            0.5, 30.0, required=False),
        super_pacgum_duration=reader.number(
            "super_pacgum_duration", defaults.super_pacgum_duration,
            0.5, 120.0, required=False),
        ghost_respawn_delay=reader.number(
            "ghost_respawn_delay", defaults.ghost_respawn_delay,
            0.0, 120.0, required=False),
        scatter_duration=reader.number(
            "scatter_duration", defaults.scatter_duration, 0.0, 120.0,
            required=False),
        ghost_score_doubling=reader.flag("ghost_score_doubling", False),
        timeout_costs_life=reader.flag("timeout_costs_life", True),
        cheat_mode=reader.flag("cheat_mode", False),
        window_width=reader.integer("window_width", defaults.window_width,
                                    640, 3840, required=False),
        window_height=reader.integer("window_height", defaults.window_height,
                                     480, 2160, required=False),
        target_fps=reader.integer("target_fps", defaults.target_fps, 15, 240,
                                  required=False),
        backend=reader.text("backend", defaults.backend, required=False),
    )
    return config, warnings


def _resolve_highscore(config_path: Path, filename: str) -> Path:
    """Resolve the highscore file relative to the configuration file."""
    candidate = Path(filename).expanduser()
    if candidate.is_absolute():
        return candidate
    try:
        base = config_path.resolve().parent
    except OSError:  # pragma: no cover - exotic filesystems
        base = Path.cwd()
    return base / candidate


def _report_unknown_keys(raw: dict[str, Any], reader: _Reader) -> None:
    """Mention the keys that are simply ignored."""
    known = _CORE_KEYS | _EXTRA_KEYS
    for key in sorted(raw):
        if key not in known:
            reader.warn("unknown key '%s' ignored" % key)


def _read_levels(raw: dict[str, Any], warnings: list[str],
                 default_pacgum: int,
                 default_time: float) -> tuple[LevelSpec, ...]:
    """Build the level list, padded up to :data:`MIN_LEVELS` entries."""
    entries = raw.get("levels", raw.get("level"))
    specs: list[LevelSpec] = []
    if entries is None:
        warnings.append("missing key 'levels', using the built-in levels")
    elif not isinstance(entries, list) or not entries:
        warnings.append("key 'levels' must be a non-empty list, "
                        "using the built-in levels")
    else:
        for index, entry in enumerate(entries):
            spec = _read_level(entry, index, warnings, default_pacgum,
                               default_time)
            if spec is not None:
                specs.append(spec)
    while len(specs) < MIN_LEVELS:
        size = DEFAULT_LEVEL_SIZES[len(specs) % len(DEFAULT_LEVEL_SIZES)]
        specs.append(LevelSpec(size[0], size[1], default_pacgum,
                               default_time))
    return tuple(specs)


def _read_level(entry: Any, index: int, warnings: list[str],
                default_pacgum: int,
                default_time: float) -> Optional[LevelSpec]:
    """Validate a single entry of the ``levels`` array."""
    where = "level %d: " % (index + 1)
    if not isinstance(entry, dict):
        warnings.append("%sentry must be an object, entry dropped" % where)
        return None
    reader = _Reader(entry, warnings, where)
    fallback = DEFAULT_LEVEL_SIZES[index % len(DEFAULT_LEVEL_SIZES)]
    for key in sorted(entry):
        if key not in _LEVEL_KEYS:
            reader.warn("unknown key '%s' ignored" % key)
    return LevelSpec(
        width=reader.integer("width", fallback[0], MIN_CELLS, MAX_CELLS),
        height=reader.integer("height", fallback[1], MIN_CELLS, MAX_CELLS),
        pacgum=reader.integer("pacgum", default_pacgum, 0, 100000,
                              required=False),
        max_time=reader.number("max_time", default_time, 5.0, 3600.0,
                               required=False),
    )
