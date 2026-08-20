# Hypotheses

What we are currently trying to establish, one file per claim. The forward-looking
counterpart to `changelog/` (what happened) and `STATE.md` (what is true now); the goal
they serve is in `problem_statement.md`.

## Read `open/` and stop

```text
open/         at most THREE, and they are the only ones a session normally reads
supported/    resolved; the current account of the world
falsified/    resolved; kept because the reason a hypothesis died is what stops it
              being re-run
```

**Status is the folder.** A hypothesis moves between folders when it resolves; the `Status`
line inside the file carries the date and any nuance the folder cannot.

Resolved hypotheses are archive. Read one when a specific claim is in question — a link
from an open file, or a number you are about to quote — not as orientation. The standing
result lives in `AGENTS.md` and `STATE.md`, which is what to read instead.

## The cap: three open hypotheses

Hard cap, and it is the point of the layout. A directory of a dozen live questions is one
a session skims instead of reads, and it stops being able to answer "what next?" — which is
the only thing it is for.

If a fourth wants to exist, one of these is true and you resolve it before adding:

- an open one is actually answered — move it to `supported/` or `falsified/`
- an open one is not going to be tested in any foreseeable session — move it to
  `falsified/` with `Status: abandoned` and the reason, or fold it into a live one
- the new question is a sub-case of one already open — say it inside that file's
  `What it predicts next`, not in a new file

Three is a working set, not a quota: two is fine and better than three padded.

## Schema

```markdown
# H<n>: <one-sentence claim>

**Status:** open | supported | falsified | abandoned — <date>
**Bears on:** <which part of problem_statement.md's contribution>

## Claim
## What would falsify it        <- write this BEFORE the experiment, not after
## Evidence                     <- append-only, dated, each line naming a run id
## What it predicts next
```

Numbers are permanent and never reused, so `H4` means one thing across the changelog and
the code comments even after the file moves folders.

## Rules

- **`What would falsify it` is written before the evidence, and is not edited afterwards.**
  A falsifier rewritten once the result is in is not a falsifier. If it was wrong, say so
  in `Evidence` and open a new hypothesis.
- **`Evidence` is append-only.** Every line dates itself and names a run id, so a claim can
  be traced to `data/results/<experiment>/<run_id>/`. Superseded readings stay, annotated.
- **Status changes are recorded in the changelog** for that session, not silently.
- A falsified hypothesis is kept, not deleted.

## Choosing the next experiment

Two halves: *which question* to attack, and *how the run must be built*. This file covers
the first; `AGENTS.md` → "Experiment design" covers the second, and a design that skips it
produces a number nobody can interpret however good the question was.

Pick the one that most changes belief across `open/` per unit cost. Stated in prose in the
changelog's `Next`, with the cost estimate — deliberately a judgment call and not a scoring
rubric. The `What would falsify it` sections make that judgment cheap: an experiment that
cannot move any of the three is not worth running.

## Maintenance

`wind-up` updates any hypothesis a session touched, and moves resolved ones out of `open/`.
Unlike the changelog these files are mutable, so they rot silently if that step is skipped
— and a stale `open/` breaks the cap, which is what keeps the directory readable at all.
