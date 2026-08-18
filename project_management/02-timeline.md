# Timeline: plan versus reality

Days are counted from **D1**, the day the group received its assigned
A-Maze-ing package. Each iteration ends with a build that runs.

## Planned Gantt

```
                    D1  D2  D3  D4  D5  D6  D7  D8  D9  D10
I1 Foundations      ####====
   subject analysis ####
   MLX-like layer   ####====
   config + jsonc       ====
I2 Maze                     ####====
   generator adapter       ####
   cell -> tile grid       ####====
I3 Gameplay                         ####====####
   movement                        ####
   ghosts + AI                     ####====
   scoring / lives                     ====####
I4 Interface                                    ####====
   menus + HUD                                  ####
   highscores                                   ####====
I5 Delivery                                             ####====
   balance pass                                         ####
   packaging                                            ####====
   documentation                                        ####====
```

## Actual progress

| Iteration | Planned | Actual | Note |
| --- | --- | --- | --- |
| I1 Foundations | D1-D2 | D1-D2 | On time. The bitmap font took longer than expected, the rest was faster. |
| I2 Maze | D3-D4 | D3-D4 | On time. The '42' pattern produced unreachable pockets; fixed the same day with the largest-area filter. |
| I3 Gameplay | D5-D7 | D5-D8 | **One day late.** Grid-locked movement needed a rewrite (see below). |
| I4 Interface | D8-D9 | D8-D9 | Absorbed the slip by cutting the planned animated level transition. |
| I5 Delivery | D9-D10 | D9-D10 | On time. |

## Where the day was lost

The first movement implementation stored a tile plus a float offset and
recomputed the occupied tile with `floor()`. Turning at a junction was
off by one tile roughly one frame in twenty, which made the player
clip into walls. It was replaced by an explicit
"travel from tile centre to tile centre" model with an explicit target
tile (`Mover._start_step` / `Mover._advance`). The rewrite cost half a
day and removed a whole class of bugs: ghosts, player and collision
detection all became exact.

## What was cut to stay on schedule

* Animated transition between two levels (replaced by the banner).
* Sound effects (not required by the subject).
* An application icon for the packaged build (documented as a one-line
  change in `packaging/README.md`).

## Milestones actually reached

| Milestone | Day |
| --- | --- |
| A window opens and shows a pixel buffer | D2 |
| A generated maze is displayed | D3 |
| Pac-Man moves and eats | D5 |
| Four ghosts chase with distinct behaviours | D7 |
| Full loop: menu, game, game over, highscore, menu | D9 |
| Packaged build runs on a machine without Python | D10 |
