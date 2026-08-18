#!/usr/bin/env python3
"""Install the A-Maze-ing package assigned to the group.

The package is delivered either as a wheel or as a zip archive holding
that wheel.  Both are handled here so that a reviewer only has to drop
the file next to this script and run ``make install``.
"""

import glob
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

PATTERNS = ("*.whl", "mazegenerator*.zip", "*maze*.zip")


def find_archive() -> Optional[Path]:
    """Return the first A-Maze-ing archive found next to this script."""
    root = Path(__file__).resolve().parent
    for pattern in PATTERNS:
        for candidate in sorted(root.glob(pattern)):
            return candidate
    return None


def wheel_from_zip(archive: Path, workdir: Path) -> Optional[Path]:
    """Extract *archive* and return the wheel it contains."""
    try:
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(workdir)
    except (zipfile.BadZipFile, OSError) as error:
        print("error: cannot read '%s' (%s)" % (archive, error))
        return None
    wheels = sorted(glob.glob(str(workdir / "**" / "*.whl"), recursive=True))
    if not wheels:
        print("error: no wheel inside '%s'" % archive)
        return None
    return Path(wheels[0])


def install(wheel: Path) -> int:
    """Run pip on *wheel* and report the result."""
    command = [sys.executable, "-m", "pip", "install",
               "--force-reinstall", str(wheel)]
    print("installing %s" % wheel.name)
    try:
        return subprocess.call(command)
    except OSError as error:
        print("error: cannot run pip (%s)" % error)
        return 1


def main() -> int:
    """Locate the assigned package and install it."""
    archive = find_archive()
    if archive is None:
        print("no A-Maze-ing archive found next to install_generator.py")
        print("drop the .whl or .zip delivered by the other group here")
        return 1
    if archive.suffix == ".whl":
        return install(archive)
    with tempfile.TemporaryDirectory() as temporary:
        wheel = wheel_from_zip(archive, Path(temporary))
        if wheel is None:
            return 1
        return install(wheel)


if __name__ == "__main__":
    sys.exit(main())
