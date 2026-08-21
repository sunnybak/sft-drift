# UNBLOCK

Read this **in addition to** `GOAL.md`, not instead of it — set together as
`/goal @GOAL.md @UNBLOCK.md`. Its presence means: extra resources exist right now (a
bigger box, more VRAM, more budget) that don't normally exist, and this session's job is
to spend them on whichever `hypotheses/resource_constrained/` file they unblock, cleanly,
then stop.

## What this changes about the loop

`GOAL.md`'s loop runs "as many times as it can do honestly" — the right default when
compute is cheap and ambient. That default is wrong here: the resource this file exists
for is rented, priced by the hour, and not meant to become a standing dependency.

**Run ONE full cycle, not the indefinite loop.** One cycle means: read the target
`resource_constrained/` file, confirm the resource is actually active (don't assume —
check), do the run(s) the file's `What it predicts next` describes, read the result,
update the hypothesis file and move it out of `resource_constrained/` (to `open/` if
inconclusive-but-testable-again, `supported/`/`falsified/` if resolved), wind up
(`STATE.md`, changelog, push), and stop. Do not start a second experiment on the
expensive resource without the user confirming they want to keep paying for it — surface
that as a question, don't assume the answer either way.

## Before spending anything

1. **Confirm which `resource_constrained/` hypothesis this resource is for.** Don't
   guess from box specs alone — ask if it's ambiguous. As of 2026-08-21 there is one:
   `H19` (needs ~64-68GB for a clean full fine-tune; a 96GB instance covers it).
2. **Check whether an adjacent resource-constrained item is worth batching into the same
   rental**, since the marginal cost of doing so is usually far below a second rental
   later — e.g. `STATE.md`'s note that H8's 8B-model leg needs >16GB. Bringing this up is
   this file's job; deciding scope is the user's.
3. **Settle the storage plan before training, not after hitting a quota.** A full
   fine-tune's checkpoints are far larger than this project's usual LoRA adapters (~8GB
   per full checkpoint vs ~150-200MB) and can blow through the 100GB private HF quota
   this project has already hit once this history. The options — HF Pro's 1TB private
   tier (~$9/mo, no change to who can see the work), a public repo (much more storage,
   but makes unpublished research artifacts world-readable) — trade off very differently
   against **anonymity for peer review and scoop risk on unpublished work**, which is
   the user's call, not a default to pick for cheapness. Ask, don't assume public.
4. **Re-derive anything the resource-constrained file flags as calibrated for the old
   resource.** `H19` specifically: the frozen training schedule was tuned and gated for
   LoRA — don't reuse its learning rate/epochs unmodified for full fine-tuning without
   redoing the trajectory-gate sweep, or a null or positive result is equally explained
   by "wrong hyperparameters for this method" as by the hypothesis itself.

## When the cycle ends

Report what happened, whether the hypothesis resolved or just moved back to `open/` for
a future ordinary cycle, and **explicitly ask whether to keep the expensive instance
running** or wind down to the standing box — don't decide either way unprompted. If nothing
in `resource_constrained/` remains, say so; this file staying set with nothing left to
unblock is a sign to clear it (`/goal clear` on this half, or just stop passing it).
