# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for the standalone Pac-Man build.

Build it with `make package`, or directly with:

    pyinstaller pacman.spec --noconfirm --clean

The result is a self-contained folder in `dist/pacman/` that runs
without a Python installation.  It is the folder uploaded to itch.io.
"""

import os

ROOT = os.path.abspath(os.getcwd())
SOURCES = os.path.join(ROOT, 'src')

# The game only imports these lazily, so PyInstaller cannot see them.
HIDDEN = [
    'mazegenerator',
    'pacman',
    'pacman.app',
    'pacman.main',
    'pacman.mlxlib.backends.pygame_backend',
    'pacman.mlxlib.backends.tk_backend',
]

# Shipped next to the executable: the default configuration and the
# in-package instructions required by the subject.
DATA = [
    ('config.json', '.'),
    (os.path.join('packaging', 'INSTRUCTIONS.txt'), '.'),
]

analysis = Analysis(
    ['pac-man.py'],
    pathex=[ROOT, SOURCES],
    binaries=[],
    datas=DATA,
    hiddenimports=HIDDEN,
    hookspath=[],
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'setuptools', 'pytest', 'mypy', 'flake8'],
    noarchive=False,
)

archive = PYZ(analysis.pure)

executable = EXE(
    archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name='pacman',
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name='pacman',
)
