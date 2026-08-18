# Requirement analysis and technical choices

## 1. Reading the subject

The subject was split into 38 atomic requirements, each traceable to a
chapter. They fall into six groups:

| Group | Requirements | Chapter |
| --- | --- | --- |
| Command line and configuration | 7 | V.1 - V.3 |
| Maze generation via the assigned package | 4 | V.4, VI.1 |
| Highscores | 8 | V.5 |
| Gameplay (player, ghosts, pacgums, scoring, progression) | 11 | VI.2 - VI.7 |
| User interface | 5 | VI.8 |
| Packaging and documentation | 3 | VII - IX |

Two requirements were flagged as *interpretation needed* and settled by
writing the reasoning down before coding:

1. **`pacgum: 42` versus "pacgums in most corridors".** A 15x11 maze has
   about 330 corridor tiles, so 42 dots is not "most" of them. The two
   statements only reconcile if `pacgum` is a *count*: 42 dots collected
   in the suggested 90 second budget is a balanced level, whereas 330
   dots in 90 seconds is impossible. The count reading was adopted, and
   `pacgum: 0` was added as an explicit switch that fills every corridor
   for people who prefer the classic look. Both are documented in the
   README.
2. **"A graphical library similar to MLX".** See section 3.

## 2. Architecture decision: four layers

The code is split so that the game logic never touches a pixel and the
drawing code never decides a rule:

```
pacman.mlxlib   window, image buffer, hooks, event loop  (MLX-shaped)
pacman.settings configuration parsing and validation
pacman.game     maze, entities, ghosts, levels, session  (pure logic)
pacman.ui       renderer, sprites, screens
pacman.app      input routing and the state machine
```

The benefit showed up immediately: the whole game logic is testable
without opening a window, which is what made the 49 unit tests and the
automated balance measurements possible.

## 3. Decision: which graphics library

The subject only allows a library whose functions all have a MiniLibX
equivalent. Three options were compared:

| Option | Verdict |
| --- | --- |
| `pygame` used normally (`draw.circle`, `draw.rect`, `font`) | **Rejected**: none of these exist in MiniLibX |
| `tkinter` canvas items (`create_oval`, `create_rectangle`) | **Rejected**: same problem |
| A pixel buffer pushed whole to a window | **Chosen** |

The chosen design mirrors what a 42 student does in C: allocate an
image with `mlx_new_image`, get the raw buffer with
`mlx_get_data_addr`, write pixels, then call
`mlx_put_image_to_window`. Every shape - walls, Pac-Man, ghosts, the
bitmap font - is drawn by our own code writing bytes into that buffer.

The backend is therefore reduced to four operations (open a window,
push an image, read key events, close the window), which both pygame
and Tk can provide. pygame is preferred for speed, Tk is the fallback
so the game runs on a bare Python install. The full mapping table is in
the README and in `src/pacman/mlxlib/mlx.py`.

## 4. Decision: ghost behaviour

The subject leaves the chase behaviour free. Rather than four copies of
"walk towards the player", the original arcade targeting was
implemented: at every tile centre a ghost picks the exit that minimises
the distance to *its own* target tile and never turns back. Blinky
targets the player, Pinky four tiles ahead, Inky mirrors Blinky through
a point two tiles ahead, Clyde gives up when he gets within eight
tiles. Frightened ghosts invert the rule and maximise the distance,
which is the literal "run away from the player" the subject asks for.

Cost: about 40 lines. Benefit: four ghosts that visibly behave
differently, and a pincer movement that emerges on its own.

## 5. Decision: what happens when the clock runs out

The subject leaves this open. Losing a life and restarting the level
was chosen because it keeps the timer meaningful without throwing away
the whole run. `timeout_costs_life: false` in the configuration turns
it into a free retry.

## 6. Non-goals

Deliberately left out, to protect the schedule: sound, a level editor,
network highscores, sprite sheets loaded from disk. None of them is
required by the subject.
