# Kanban board

Work in progress was capped at **3** items. A card only moved to *Done*
when `make lint` was clean, `make test` was green, the feature was
reachable from the running game, and the documentation was updated in
the same commit.

## Backlog -> Done

| # | Card | Iteration | State |
| --- | --- | --- | --- |
| 1 | Split the subject into atomic requirements | I1 | Done |
| 2 | Decide the graphics approach against the MLX rule | I1 | Done |
| 3 | Image buffer with pixel, rect and disc writes | I1 | Done |
| 4 | 5x7 bitmap font and `string_put` | I1 | Done |
| 5 | pygame backend | I1 | Done |
| 6 | Tk fallback backend | I1 | Done |
| 7 | JSON-with-comments reader | I1 | Done |
| 8 | Configuration validation and clamping | I1 | Done |
| 9 | Adapter over the assigned A-Maze-ing package | I2 | Done |
| 10 | Cell grid to Pac-Man tile grid conversion | I2 | Done |
| 11 | Largest-area filter for the '42' pockets | I2 | Done |
| 12 | Spawn points: centre for the player, four corners | I2 | Done |
| 13 | Grid-locked movement | I3 | Done (rewritten once) |
| 14 | Pacgums, super-pacgums, scoring | I3 | Done |
| 15 | Ghost state machine | I3 | Done |
| 16 | Arcade targeting for the four personalities | I3 | Done |
| 17 | Lives, respawn, level clock | I3 | Done |
| 18 | Level ladder and victory condition | I3 | Done |
| 19 | Maze renderer with connected wall blocks | I4 | Done |
| 20 | Pac-Man and ghost sprites | I4 | Done |
| 21 | HUD: score, lives, level, clock | I4 | Done |
| 22 | Main menu, instructions, highscores screen | I4 | Done |
| 23 | Pause overlay | I4 | Done |
| 24 | Game over / victory and name entry | I4 | Done |
| 25 | Persistent highscore file with fallback location | I4 | Done |
| 26 | Cheat mode | I4 | Done |
| 27 | Automated balance measurement | I5 | Done |
| 28 | PyInstaller packaging | I5 | Done |
| 29 | README and project management documents | I5 | Done |
| 30 | Animated level transition | I4 | **Dropped** (see timeline) |
| 31 | Sound effects | - | **Dropped** (out of scope) |

## Snapshot at the end of I3

```
BACKLOG            IN PROGRESS (3)     REVIEW              DONE
19 wall renderer   16 ghost targeting  14 scoring          1..13
20 sprites         17 lives / clock    15 ghost states     
21 HUD             18 level ladder                         
22 menus                                                   
```
