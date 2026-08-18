# Acceptance test plan

Two levels of testing:

* **Automated** - `make test` runs 49 unit tests over the pure logic
  (configuration, JSON reader, highscores, maze conversion, movement,
  ghosts, levels, sessions). They need no window and run in under a
  second.
* **Manual** - the scenarios below, replayed before every delivery.
  The cheat mode exists to make them fast.

## Automated coverage

| Module | Tests | What is proven |
| --- | --- | --- |
| `jsonc` | 7 | `#`, `//` and block comments, comments inside strings, trailing commas, error line numbers |
| `settings` | 9 | Defaults, clamping, wrong types, unknown keys, level padding to ten, broken level entries, highscore path, unreadable file |
| `highscore` | 8 | Name sanitising, top-ten bound, round trip, corrupted file, invalid rows, missing file, qualification, negative scores |
| `maze` | 10 | Grid size, corridors carved only when both cells agree, solid border, isolated cells, largest-area filter, spawn points |
| `game` | 15 | Grid-locked movement, walls, buffered turns, ghost spawn, super-pacgum, eating a ghost, losing a life, invincibility, level cleared, timeout, dot count, `pacgum: 0`, reproducible first maze, victory, game over |

## Manual scenarios

| # | Requirement | Scenario | Expected | Result |
| --- | --- | --- | --- | --- |
| M1 | V.1 | `python3 pac-man.py` | Usage message, exit code 2, no traceback | Pass |
| M2 | V.1 | `python3 pac-man.py a.json b.json` | Usage message, exit code 2 | Pass |
| M3 | V.1 | `python3 pac-man.py config.txt` | "is not a .json file", exit code 2 | Pass |
| M4 | V.1 | `python3 pac-man.py missing.json` | "file not found", exit code 1 | Pass |
| M5 | V.3 | Configuration with `"lives": 9999` | Clamped to 99, notice on screen, game starts | Pass |
| M6 | V.3 | Configuration with `"lives": "three"` | Falls back to 3 with a notice | Pass |
| M7 | V.3 | Configuration with an unknown key | Key ignored, notice, game starts | Pass |
| M8 | V.3 | Truncated JSON | Clear parse error with the line number | Pass |
| M9 | V.4 | Uninstall the A-Maze-ing package, start the game | Readable message naming the package, no traceback | Pass |
| M10 | VI.1 | Start twice with `seed: 42` | The first maze is identical both times | Pass |
| M11 | VI.1 | Reach level 2 twice | Different mazes | Pass |
| M12 | VI.1 | Look at any maze | Super-pacgums in the four corners, one ghost per corner, player in the middle | Pass |
| M13 | VI.2 | Walk into a wall | The player stops, never clips through | Pass |
| M14 | VI.2 | Press a direction before a junction | The turn is taken at the junction | Pass |
| M15 | VI.2 | Get caught | One life lost, player back in the middle | Pass |
| M16 | VI.2 | Lose the last life | Game over screen with the final score | Pass |
| M17 | VI.3 | Watch the ghosts for a minute | Four visibly different behaviours, none trapped | Pass |
| M18 | VI.4 | Eat a super-pacgum | All ghosts turn blue, flash before the end, flee | Pass |
| M19 | VI.4 | Eat a blue ghost | Score increases, ghost goes home, comes back after the delay | Pass |
| M20 | VI.5 | Press F1 then F2 to F8 | Every cheat has a visible effect; the footer lists them | Pass |
| M21 | VI.6 | Play a level | Score never decreases | Pass |
| M22 | VI.7 | Let the clock run out | One life lost, level restarts | Pass |
| M23 | VI.7 | Clear a level | Next level, score and lives kept | Pass |
| M24 | VI.7 | Clear the ten levels with F6 | Victory screen | Pass |
| M25 | VI.7 | Press P then ESC | Pause overlay, resume, return to menu | Pass |
| M26 | VI.8 | Any moment in game | Score, lives, level and clock always visible | Pass |
| M27 | V.5 | Finish a game and type a name | Score saved, visible in the menu and in the table | Pass |
| M28 | V.5 | Type punctuation in the name field | Refused; only letters, digits and spaces accepted | Pass |
| M29 | V.5 | Corrupt `highscores.json` by hand | Table starts empty with a notice, no crash | Pass |
| M30 | V.5 | Delete `highscores.json` | Empty table, no crash | Pass |
| M31 | VII | `make package`, run `dist/pacman/pacman` | Runs without Python, uses the bundled configuration | Pass |
| M32 | III | `make lint` and `make lint-strict` | flake8 clean, mypy clean, mypy strict clean | Pass |

## Balance measurement

Levels were tuned with a bot that plays optimally while ignoring the
ghosts, `tools/measure_balance.py`. It walks to the nearest remaining
dot and reports how long clearing a level takes.

Before tuning, with `player_speed: 6.0` and a flat 90 second clock:

```
level  1:  46 dots   329 corridors  cleared in  49.1s /  90s  OK
level  3:  46 dots   452 corridors  cleared in  64.2s /  90s  TIGHT
level  5:  46 dots   509 corridors  cleared in  60.6s /  90s  OK
level  8:  46 dots   762 corridors  cleared in  75.2s /  90s  TIGHT
level 10:  46 dots   946 corridors  cleared in  82.3s / 120s  OK
```

After tuning, with `player_speed: 7.0` and per-level clocks from level
six onwards:

```
level  1:  46 dots   329 corridors  cleared in  42.1s /  90s  OK
level  3:  46 dots   452 corridors  cleared in  49.1s /  90s  OK
level  5:  46 dots   507 corridors  cleared in  56.8s /  90s  OK
level  8:  46 dots   763 corridors  cleared in  68.9s / 110s  OK
level 10:  46 dots   943 corridors  cleared in  75.6s / 130s  OK
```

An optimal path now uses at most 60 % of the budget on every level,
which leaves a human the room needed to dodge the ghosts.

## Bugs found and fixed

| # | Symptom | Cause | Fix |
| --- | --- | --- | --- |
| B1 | Pacgums unreachable behind walls | The '42' pattern the generator carves leaves isolated cells | Keep only the largest connected area, `_keep_largest_area` |
| B2 | The player clipped through a wall corner about once in twenty turns | The occupied tile was computed with `floor()` on a float offset | Movement rewritten around explicit tile-to-tile travel |
| B3 | A corridor could open on one side only | Only the first cell was checked for its wall bit | A passage is carved only when both cells agree, `_opens_east` and `_opens_south` |
| B4 | Ghosts oscillated in place at some junctions | Reversing was allowed, so two opposite exits scored the same frame after frame | Reversal forbidden unless it is the only exit |
| B5 | The score jumped by 250 when the player entered a corner | Super-pacgums and ghost homes share the corner tiles, so pellet and ghost were eaten in the same frame | Correct behaviour; the tests were rewritten to place ghosts away from the corners so each proves one rule |
| B6 | `mypy --strict` reported `Any` returns | `x ** 0.5` and `2 ** n` are untyped | Replaced with `math.hypot` and an explicit `int()` |
| B7 | Levels 8 to 10 were nearly impossible | Bigger mazes, same 90 second budget | Speed and per-level clocks retuned, see above |
