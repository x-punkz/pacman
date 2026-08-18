# Retrospective

## Blocking points

1. **The movement model, half a day lost.** The first implementation
   mixed a tile index with a float offset; every rounding decision
   became a new special case. Rewriting it around a single rule - a
   body always travels from one tile centre to the next, and only
   decides where to go when it sits exactly on a centre - removed the
   whole bug class and made the ghosts simpler as a side effect.
   Lesson: when a bug needs a third special case, the model is wrong,
   not the code.

2. **The '42' pattern inside the generated mazes.** The assigned
   package carves a '42' into every maze by isolating cells. Those
   cells become pockets no player can enter, so dots placed there made
   a level impossible to finish. The subject forbids touching the
   package, so the fix had to live on our side: keep only the largest
   connected area of the tile grid. Lesson: "adapt to their interface,
   not the opposite" also means adapting to their output.

3. **Reading `pacgum: 42`.** Chapter V.2 suggests 42 pacgums, chapter
   VI.4 asks for dots in most corridors. In a 330 tile maze the two
   cannot both hold. Rather than picking one silently, the reasoning
   was written down, the count reading was implemented because it is
   the one consistent with the 90 second budget, and `pacgum: 0` was
   added for the other reading. Lesson: when a subject is ambiguous,
   implement one reading, support the other, and document why.

## Conflicts

There was no team conflict: the project was solo. The one point that
needed arbitration was internal, and it is worth recording because it
shaped the whole codebase: is pygame allowed or not? The tempting
answer is "it is a graphical library, so yes". Re-reading the box in
chapter IV settles it the other way: the rule applies per *function*,
not per library. `pygame.draw.circle` has no MiniLibX equivalent and
therefore cannot be used, while pushing a pixel buffer to a window has
one and can. The outcome is the `pacman.mlxlib` layer, its mapping
table, and the fact that every shape in the game is drawn by our own
code writing bytes.

## What worked

* Cutting the subject into 38 atomic requirements up front. Nothing
  was discovered late.
* Keeping the game logic free of any drawing code. That is what made
  the 49 tests and the automated balance measurement possible at all.
* Ending every iteration on a runnable build. The day lost in
  iteration three never threatened the delivery.
* Writing the cheat mode early rather than as an afterthought: it made
  manual testing about five times faster.

## What to do differently next time

* Measure balance earlier. The bot that plays a level optimally took
  half an hour to write and would have caught the difficulty problem
  in iteration three instead of iteration five.
* Set the packaging up on day one, even empty. Discovering on the last
  day that a windowed build has no console to print into would have
  been unpleasant.
* Write the tests for the faulty configuration paths before the happy
  path. They are the ones the defence actually exercises.

## Metrics

| | |
| --- | --- |
| Requirements extracted from the subject | 38 |
| Kanban cards | 31, of which 29 done and 2 dropped |
| Python modules | 29 |
| Unit tests | 49, green |
| Manual scenarios | 32, all passing |
| flake8 | clean |
| mypy with the mandatory flags | clean |
| mypy `--strict` | clean |
| Iterations delivered on time | 4 of 5 |
