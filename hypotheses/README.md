# Hypotheses

What we are currently trying to establish, one file per claim. The forward-looking
counterpart to `changelog/` (what happened) and `STATE.md` (what is true now); the goal
they serve is in `GOAL.md`.

## Read `open/` and stop

```text
open/         at most THREE, and they are the only ones a session normally reads
blocked/      well-formed, NOT resolved, but cannot be tested with what's currently
              available -- does not count against the cap of three (see below)
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

## `blocked/`: well-formed but not currently testable

A hypothesis belongs here instead of `open/` when it has a real claim and a real
falsifier, but testing it needs a resource this session doesn't have — more VRAM than
the box provides, a full fine-tune where the project's standing config is LoRA-only, a
larger model, API budget beyond what's approved, anything that isn't just "an experiment
that hasn't been run yet." A hypothesis that's simply next in line belongs in `open/` and
takes its turn; `blocked/` is specifically for "cannot be tested with what exists right
now," recorded in the file's `Prerequisite gates` section.

**It does not count against the cap of three.** That's the entire point: a hypothesis
worth keeping shouldn't have to either occupy a scarce `open/` slot it can make no
progress on, or get abandoned/falsified just to free the slot, when the actual problem is
resourcing, not the claim's validity.

**Moving a hypothesis OUT of `blocked/` is a decision to acquire the missing resource,
and that decision is not the agent's to make alone.** Provisioning more GPU, renting a
bigger box, spending real budget, or relaxing a standing project rule (like the
no-quantization decision in `AGENTS.md`) are exactly the kind of consequential,
hard-to-reverse-by-default actions this project's own working style asks to be surfaced
rather than assumed. **If a session wants to move a `blocked/` hypothesis into `open/`
and start testing it, ask the user for the resource it needs first — do not provision it
and proceed unprompted, even if the technical path is obvious.** Once approved, move the
file to `open/`, note what was provisioned in `Current position`, and it's an ordinary
open hypothesis from there.

## Schema

```markdown
# H<n>: <one-sentence claim>

**Status:** open | blocked | supported | falsified | abandoned — <date>
**Bears on:** <which part of GOAL.md's contribution>

## Current position               <- OVERWRITTEN, not append-only; see Rules
## Claim
## Prerequisite gates             <- optional; instrument/suite validity, not the hypothesis itself
## What would falsify it          <- write this BEFORE the experiment, not after
## Evidence                       <- append-only, dated, each line naming a run id
## What it predicts next
```

Numbers are permanent and never reused, so `H4` means one thing across the changelog and
the code comments even after the file moves folders.

## Rules

- **`What would falsify it` is written before the evidence, and is not edited afterwards.**
  A falsifier rewritten once the result is in is not a falsifier. If it was wrong, say so
  in `Evidence` and open a new hypothesis.
- **`What would falsify it` states only what would kill the claim itself — not whether the
  instrument used to test it is trustworthy.** Added 2026-08-21 after a session where a
  falsifier's own registered clause turned out to invoke a quantity AGENTS.md had already
  ruled out, and a separate run's decisive finding was a suite's null-control facet
  failing — something no falsifier had named because it isn't about the hypothesis, it's
  about whether the test run that cycle is valid at all. That kind of check goes in
  `Prerequisite gates`: things that must hold for a reading to mean anything (a suite's
  null control comes out ≈0, a positive control moves, a corpus passes its eye-read) —
  distinct from, and checked before trusting, the falsifier proper. A prerequisite
  failing doesn't touch the hypothesis; it means re-run once fixed.
- **`Current position` is the one section this file's mutability rule doesn't apply to —
  it is overwritten each time evidence changes what the file would tell a cold reader,
  the same as `STATE.md`.** Everything else here is append-only so nothing is lost;
  without one editable summary, a hypothesis that accumulates many evidence entries and
  corrections becomes something only its own author can skim, which is exactly the
  problem `open/`'s cap-of-three exists to prevent one level up. Keep it to a few
  sentences: what the claim currently looks like, at what quotability level (GOAL.md's
  ladder), and what would need to change that.
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
