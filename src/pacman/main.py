"""Command line entry point.

Usage:
    python3 pac-man.py config.json
"""

import sys
from pathlib import Path
from typing import Optional, Sequence

from .app import Application
from .settings import Config, ConfigError, default_config, load_config

USAGE = "usage: python3 pac-man.py config.json"


def resolve_config_path(argv: Sequence[str]) -> tuple[Optional[Path], str]:
    """Turn the command line into a configuration path.

    Args:
        argv: The arguments, without the program name.

    Returns:
        The path to use and an error message; exactly one of the two
        is meaningful.
    """
    if len(argv) != 1:
        bundled = _bundled_config()
        if not argv and bundled is not None:
            return bundled, ""
        given = "no argument" if not argv else "%d arguments" % len(argv)
        return None, "exactly one argument is required, got %s" % given
    path = Path(argv[0]).expanduser()
    if path.suffix.lower() != ".json":
        return None, "'%s' is not a .json file" % path
    return path, ""


def is_frozen() -> bool:
    """Return ``True`` when running from a PyInstaller build."""
    return getattr(sys, "frozen", False) is True


def _bundled_config() -> Optional[Path]:
    """Return the config shipped inside a packaged build, if any."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        return None
    candidate = Path(base) / "config.json"
    return candidate if candidate.is_file() else None


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the game and return the process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    path, error = resolve_config_path(arguments)
    if path is None:
        print("error: %s" % error, file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    try:
        config, warnings = load_config(path)
    except ConfigError as error_message:
        print("error: %s" % error_message, file=sys.stderr)
        print("hint: see the Configuration section of README.md",
              file=sys.stderr)
        if not is_frozen():
            return 1
        # A packaged build has no terminal to complain into, so it
        # starts on the built-in defaults and says so on screen.
        config = default_config()
        warnings = ["cannot read %s (%s)" % (path.name, error_message),
                    "the built-in default settings are used instead"]
    for warning in warnings:
        print("config: %s" % warning)
    return _launch(config, warnings)


def _launch(config: Config, warnings: Sequence[str]) -> int:
    """Start the application, converting crashes into messages."""
    try:
        return Application(config, warnings).run()
    except KeyboardInterrupt:
        print("interrupted")
        return 130
    except Exception as error:  # pragma: no cover - last resort net
        print("error: unexpected failure (%s: %s)"
              % (type(error).__name__, error), file=sys.stderr)
        return 1
