---
name: orient
description: Orient at the start of a work session in the sft-drift belief-transfer repo — read the current state, the standing result, and recent history in a bounded order, then report what is established, what is in flight, and what the next decision is. Use this whenever a session begins on this repo, whenever the user says "orient", "catch up", "where are we", "what's the state", "pick up where we left off", or after SETUP.md has been run on a fresh box. Also use it before proposing any experiment, since proposing without knowing which runs are void or which dead ends are already walked is how a session gets re-done.
---

# Orient

A session here starts with no memory and ~190KB of methodology on disk. Reading all of it
is slow and, worse, flattens everything to the same importance. This gets you to a decision
in a bounded number of reads.

The output is a written orientation the user can correct in one message. That correction
loop is the point — a summary you keep to yourself cannot be fixed.

## Read in this order, and stop when you have enough

Ordered by information density, not by chronology.

1. **`STATE.md`** — what is currently true. Void runs, in-flight work, next decisions.
   If it does not exist, say so; it means the last session did not wind up cleanly and
   you should expect gaps.
2. **`hypotheses/open/`** — at most three files, and the whole directory is capped there so
   this stays a cheap read. What the project is currently trying to establish and what
   would falsify each. **Do not read `supported/` or `falsified/`** as orientation; they
   are archive, consulted only when a specific claim comes into question. Reading them all
   loads the project's history to answer a question about its future.
3. **`GOAL.md`** — the north star and, more usefully, what is explicitly out
   of scope. Read it when the request is open-ended or touches the paper; skip it for a
   narrow re-scoring request. It is revised occasionally on the user's feedback, so do not
   assume a remembered version is current — the changelog records when it moved.
4. **`AGENTS.md`** → "What the factory-farming experiment measured" — the standing
   scientific result. Read this section, not the whole file. Read the rest of AGENTS.md
   only when you are about to change something it governs.
5. **`changelog/`, newest first** — usually the latest 1–2 files. Stop when entries stop
   being relevant to what the user is asking for. Each file's `Learnings` and `Next`
   sections carry most of the value; the addenda are working detail.
6. **Box and repo state** — `git log --oneline -5`, `git status`, whether
   `configs/hardware_profile.yaml` exists (means this box is calibrated), and what is in
   `data/checkpoints/` and `data/results/`.

If the user's request is narrow ("re-score the step-24 matrix"), steps 1, 2 and 4 plus a
targeted look are enough. Read wider only when the request is open-ended.

## Check for void runs explicitly

A voided result directory is byte-identical in shape to a valid one. Before quoting any
number from `data/results/`, check `STATE.md`'s void table and look for a `VOID.md` in the
run directory. If you find a number that contradicts the standing result, suspect a void
run before suspecting a new finding.

## Report back in this shape

Keep it short. Long orientations do not get read, and an unread orientation cannot be
corrected.

```
## Established
<2-4 lines from the standing result, with the numbers and their CIs>

## Void — do not cite
<run ids and why, or "none recorded">

## In flight
<work started and not finished, or "nothing">

## Open questions
<the three from hypotheses/open/, one line each -- what would settle it>

## Next, as recorded
<the ordered list from STATE.md, with cost estimates if known>

## What I am unsure about
<anything ambiguous, stale-looking, or contradictory between sources>

## Proposed next action
<one concrete thing, with the command, and the decision you need from the user>
```

## Things worth flagging when you see them

These are recorded traps in this repo. Mention any that bear on what the user is asking:

- **Read at step 24, not the endpoint.** The frozen 5-epoch schedule is past the optimum
  for belief; the endpoint understates `ΔB` by 3.3×.
- **Machinery is control-specific.** Re-derive it whenever the control changes; a carried-over
  machinery term corrupted three sessions of conclusions.
- **`stage=sft` silently reuses a `COMPLETED` checkpoint.** Pass `force=true` to retrain.
- **`n_items` is mandatory and unset** in every experiment spec — a run overlay supplies it.
- **`CLAUDE.md` is a symlink to `AGENTS.md`.** Edit `AGENTS.md` only.
- **Never change an eval because of what it showed.** Iterating while exploratory is fine,
  under a new run id.
- **An experiment that cannot move an open hypothesis is not worth running.** If the user
  proposes one that does not, say which of the three it bears on — or that it bears on
  none, which is worth knowing before the spend.
- **`AGENTS.md` → "Experiment design"** is the checklist a new run has to satisfy: matched
  control, gate first, positive and null controls for a new instrument, matched dose, pilot
  before spend. Read it before proposing a run, not while writing one up.

## Do not

- Do not re-derive the standing result from raw artifacts. It is maintained in AGENTS.md;
  if you think it is stale, say so rather than quietly computing your own version.
- Do not propose an experiment in the orientation itself beyond the single next action.
  Orientation is for establishing where things stand; choosing what to run is a separate
  decision the user should make with the state in front of them.
- Do not read the resolved hypotheses to orient. `open/` is capped at three precisely so
  that orientation is bounded; pulling in `supported/` and `falsified/` defeats the layout
  and re-introduces the flattening problem this skill exists to avoid.
- Do not report confidence you do not have. "The last session ended mid-run and I cannot
  tell whether it finished" is a useful sentence.
