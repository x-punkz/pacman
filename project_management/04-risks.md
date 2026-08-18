# Risk analysis

Scored before starting, reviewed at the end of every iteration.
P = probability, I = impact, both from 1 (low) to 3 (high).

| # | Risk | P | I | Mitigation | Outcome |
| --- | --- | --- | --- | --- | --- |
| R1 | The graphics library is judged "not MLX-like" during the review | 2 | 3 | Confine every library call behind `pacman.mlxlib`, keep the mapping table in the code and in the README, draw every shape ourselves from raw pixel writes | **Did not happen.** The facade exposes 13 methods, each with a named MiniLibX counterpart |
| R2 | The assigned A-Maze-ing package has a different interface than expected | 3 | 2 | Discover the constructor signature at run time, look for the grid under several attribute names, wrap everything in one adapter module | **Materialised in a mild form.** The package takes `size=(w, h)` rather than `width`/`height`; the adapter handled it without a change |
| R3 | The assigned package is missing or broken on the review machine | 2 | 3 | Clear error message plus `install_generator.py`, which installs from the delivered `.whl` or `.zip` | **Did not happen**, but the path is tested |
| R4 | The generated mazes are not playable (dead ends, unreachable areas) | 3 | 3 | Force `perfect=False` as the subject requires, filter the tile grid down to its largest connected area | **Materialised.** The '42' pattern carved into every maze leaves isolated pockets; the filter removes them |
| R5 | Pure Python rendering is too slow for 60 fps | 2 | 3 | Cache the static wall layer, blit it with one buffer copy per frame, only redraw what moves | **Did not happen.** The maze layer is a single `bytearray` copy |
| R6 | Levels are unbalanced: impossible, or over in ten seconds | 3 | 2 | Write a bot that plays a level optimally and measure the time it needs | **Materialised.** The first measurements showed levels 8 to 10 needed 75 s of a 90 s budget; speeds and per-level clocks were retuned (see the test plan) |
| R7 | The configuration file crashes the game during the defence | 2 | 3 | Every key clamped, every failure downgraded to an on-screen notice, unknown keys ignored, dedicated unit tests | **Did not happen.** Nine tests cover the faulty configuration paths |
| R8 | The packaged build does not run on a machine without Python | 2 | 3 | Build and test the PyInstaller bundle during I5, not on the last day | **Did not happen.** The bundle carries its own `config.json` and instructions |
| R9 | The packaged build fails silently because it has no console | 2 | 2 | Show configuration notices on screen; a packaged build with an unreadable config starts on the built-in defaults instead of exiting | **Anticipated and handled** |
| R10 | Highscores cannot be written from a read-only install folder | 2 | 2 | Fall back to the per-user data directory and report it | **Anticipated and handled** |
| R11 | Running out of time before the packaging step | 2 | 3 | Iterations always end on a runnable build; packaging scheduled in I5, not last | **Materialised once** (one day lost in I3), absorbed by dropping two cosmetic features |

## Residual risks accepted

* The game has no sound. The subject does not ask for any.
* Only one graphics backend is exercised on the review machine; the
  other is kept working but is only smoke-tested.
* The itch.io upload itself depends on an account the school does not
  provide; the `butler` commands are documented and scripted but the
  final push is a manual step.
