# Team organisation

## Composition

The project was carried out solo by **daniviei**. There was therefore
no work split to negotiate, but two habits replaced it:

* **Explain before implementing.** Every risky decision (the graphics
  approach, the reading of `pacgum`, the movement rewrite) had to be
  written down and justified before any code was produced. Peer review
  is the checkpoint for these decisions; the log of the sessions
  actually held belongs at the end of this document.
* **Written decisions.** Anything that could be questioned during the
  defence was written down in `01-analysis.md` at the time the decision
  was taken, not reconstructed afterwards.

## How decisions were taken

| Decision | Method | Result |
| --- | --- | --- |
| Graphics approach | Compared three options against the "each function has an MLX equivalent" rule | Own pixel buffer, backend reduced to four operations |
| Meaning of `pacgum: 42` | Cross-read chapters V.2, VI.1 and VI.4, checked which reading fits the 90 second budget | Number of dots, with `0` as the "fill everything" switch |
| Ghost behaviour | Prototyped "everybody chases" first, judged boring, replaced with arcade targeting | Four distinct personalities |
| Timeout behaviour | Free choice in the subject | Costs a life, configurable |
| Movement model | First implementation was buggy; rewritten rather than patched | Explicit tile-to-tile travel |

## Decisions that were revisited

1. The first cheat mode was a single "god mode" key. Reviewing it
   against its actual purpose - letting a reviewer reach *every*
   feature, not merely survive - it was split into seven switches.
   *Skip level* and *leave a single pacgum* in particular make the
   end-of-level path and the victory screen reachable in seconds.
2. The first instructions screen hard-coded the scoring values. Since
   those come from the configuration file, the screen now reads them
   from the loaded `Config`, so it always matches the file in use.

## Peer review log

| Date | Peer | Subject discussed | Outcome |
| --- | --- | --- | --- |
| | | | |

*To be completed with the sessions actually held.*

## How issues were handled

Anything found while playing went straight to the board as a card with
a reproduction case. Bugs blocking the current iteration were fixed
immediately; the others waited for the next iteration boundary. The
bug list and its outcome is in `06-test-plan.md`.

## Traceability

Each of the 38 requirements extracted from the subject maps to at
least one Kanban card and at least one acceptance test. The mapping is
the `#` column of `03-kanban.md` and the *Requirement* column of
`06-test-plan.md`.
