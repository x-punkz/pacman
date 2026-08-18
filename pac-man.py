#!/usr/bin/env python3
"""Pac-Man launcher.

Run the game with:
    python3 pac-man.py config.json
"""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SOURCES = os.path.join(_ROOT, "src")
if os.path.isdir(_SOURCES) and _SOURCES not in sys.path:
    sys.path.insert(0, _SOURCES)


def _run() -> int:
    """Import the game lazily so a missing dependency stays readable."""
    try:
        from pacman.main import main
    except ImportError as error:
        print("error: cannot import the game (%s)" % error, file=sys.stderr)
        print("hint: run 'make install' first", file=sys.stderr)
        return 1
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(_run())
