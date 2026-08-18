# Packaging and publishing

The game is shipped as a self-contained folder built with
[PyInstaller](https://pyinstaller.org). No Python installation is
required on the player's machine.

## Build

```bash
make install      # dependencies + the assigned A-Maze-ing package
make package      # or: pyinstaller pacman.spec --noconfirm --clean
```

The build lands in `dist/pacman/`:

```
dist/pacman/
├── pacman(.exe)        the game
├── config.json         the default configuration, editable by players
├── INSTRUCTIONS.txt    controls, options and configuration reference
└── _internal/          the interpreter and the libraries
```

Launched without an argument the executable loads the `config.json`
bundled next to it; launched with one, it loads that file instead:

```bash
./pacman              # uses the bundled configuration
./pacman other.json   # uses another configuration
```

## Publish on itch.io

1. Create the project page on itch.io, kind **Downloadable**, pricing
   **Free**, visibility **Draft / restricted** (the subject asks for an
   unlisted build).
2. Install [butler](https://itch.io/docs/butler/) and log in once:
   ```bash
   butler login
   ```
3. Push the folder produced above, one channel per platform:
   ```bash
   butler push dist/pacman <user>/pacman-42:windows
   butler push dist/pacman <user>/pacman-42:linux
   ```
4. Check the upload:
   ```bash
   butler status <user>/pacman-42
   ```
5. On the project page, tick *This file will be played in the browser?*
   **no**, and set the executable to `pacman`/`pacman.exe`.

## Publish on Steam

Steamworks expects the same folder. Point the depot at `dist/pacman`,
set the launch executable to `pacman(.exe)`, and upload with
`steamcmd +run_app_build`. A Steam release additionally requires a
paid Steamworks account, which is why itch.io is the primary target.

## Regenerating the build during the peer review

Everything needed is committed: `pacman.spec` and `package.py` at the
root of the repository, this folder for the documentation. A reviewer
only needs `make install && make package`.

## Notes

* `--clean` is passed so that a stale `build/` folder never leaks into
  a release.
* `numpy`, `Pillow`, `pytest`, `mypy` and `flake8` are excluded from
  the bundle: the game does not need them at run time.
* To add an icon, drop an `.ico` (Windows) or `.icns` (macOS) file in
  this folder and add `icon='packaging/pacman.ico'` to the `EXE(...)`
  call of `pacman.spec`.
