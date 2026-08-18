# Project management

This folder holds the evidence of how the Pac-Man project was driven,
as required by chapter VIII of the subject.

| Document | What it contains |
| --- | --- |
| [01-analysis.md](01-analysis.md) | Requirement analysis and the technical choices that follow from it |
| [02-timeline.md](02-timeline.md) | Planned schedule, Gantt view and what actually happened |
| [03-kanban.md](03-kanban.md) | The board, task by task, with its final state |
| [04-risks.md](04-risks.md) | Risk register, mitigations and the risks that materialised |
| [05-team.md](05-team.md) | Who did what, how decisions were taken, how issues were handled |
| [06-test-plan.md](06-test-plan.md) | Acceptance test plan, results, bugs found and fixed |
| [07-retrospective.md](07-retrospective.md) | Blocking points, conflicts and lessons learned |

> **Note.** The technical content of these documents - decisions,
> risks, bugs, measurements, test results - describes the project as
> it was actually built and can be checked against the code. The day
> numbers of the timeline and the peer review log are the frame to
> fill in with the real sessions and dates.

## Method in one paragraph

The project ran as five short iterations of roughly two days each, with
a Kanban board capped at three items in progress. Every iteration ended
with a playable build, so that a slip on a late feature could never
leave the project without something to show. Definition of done for
every task: `make lint` clean, `make test` green, the feature reachable
from the running game, and the README updated in the same commit.
