#!/usr/bin/env python3
"""Build the standalone game with PyInstaller.

The result is ``dist/pacman/``: a folder that runs without a Python
installation and that can be zipped and pushed to itch.io.  See
``packaging/README.md`` for the publishing steps.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "pacman.spec"
DIST = ROOT / "dist" / "pacman"
EXTRA_FILES = ("config.json", "packaging/INSTRUCTIONS.txt")


def check_tooling() -> bool:
    """Return ``True`` when PyInstaller and the game can be found."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("error: PyInstaller is missing")
        print("hint: pip install -r requirements-dev.txt")
        return False
    if not SPEC.is_file():
        print("error: %s is missing" % SPEC.name)
        return False
    try:
        __import__("mazegenerator")
    except ImportError:
        print("error: the A-Maze-ing package is not installed")
        print("hint: python3 install_generator.py")
        return False
    return True


def build() -> int:
    """Run PyInstaller on the specification file."""
    command = [sys.executable, "-m", "PyInstaller", str(SPEC),
               "--noconfirm", "--clean", "--distpath", str(ROOT / "dist"),
               "--workpath", str(ROOT / "build")]
    print("$ %s" % " ".join(command))
    try:
        return subprocess.call(command, cwd=str(ROOT))
    except OSError as error:
        print("error: cannot run PyInstaller (%s)" % error)
        return 1


def copy_extras() -> None:
    """Make sure the shipped folder carries its documentation."""
    if not DIST.is_dir():
        return
    for name in EXTRA_FILES:
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, DIST / source.name)
            print("added %s" % source.name)


def main() -> int:
    """Build the package and explain what to do with it."""
    if not check_tooling():
        return 1
    status = build()
    if status != 0:
        print("error: the build failed with status %d" % status)
        return status
    copy_extras()
    print()
    print("build ready in %s" % DIST)
    print("zip that folder and upload it, for example with butler:")
    print("  butler push %s <user>/<game>:windows" % DIST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
