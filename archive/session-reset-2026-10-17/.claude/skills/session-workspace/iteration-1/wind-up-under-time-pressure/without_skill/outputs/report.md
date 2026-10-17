# Wind-up — 2026-08-19, second session

Ten minutes is enough. Everything below is written and staged; the only thing left is to
run the push sequence.

## The one thing that nearly got lost

**The MDA harness lived in `/private/tmp`, not in the repo.** `mda_toy.py`,
`mda_worlds.py`, `mda_llm.py` and its 6-entry call cache — ~72 KB, the entire output of this
session — were sitting in the session scratchpad at

```
/private/tmp/claude-501/-Users-sunny-dev-sft-drift/c68d1e0d-.../scratchpad/
```

`git status` shows nothing missing when scratch dies, which is what makes this the dangerous
case rather than the obvious one. I have copied all four files to `outputs/salvage/mda/`.
**Copy them somewhere durable before the box goes down** — the commands below do it.

That also matters for a second reason: the `mda_worlds` summary table was never written
down, it was read off the terminal. The harness is fully seeded (`seeds=range(24)`,
`latent_seed=s`, `run_loop(..., seed=s)`), so `python mda_worlds.py --seeds 24` regenerates
it *exactly* — but only while the code exists. Saving the code is what makes the numbers
recoverable. Recovering them is item 1 for next session (~2 min CPU, no API).

## What I found on inspection, that changes the picture

- **No unpushed commits** (`git log origin/main..main` is empty). Today's paper/writeup work
  is already on `main`. What is uncommitted is four untracked things: `STATE.md` (created
  this session, never committed), the `orient` and `wind-up` skills, and eval scaffolding.
- **`data/` is no longer stale.** `STATE.md` warned that `matrix_v1*` results might be
  missing locally and to `make data-pull` first. They are present — a pull has happened.
  I have discharged that note.
- **Unpushed data exists**: `paper_factory_farming_v1`…`v6` and `paper-test` were generated
  today under `belief-transfer/data/results/factory_farming/`.
- **Unpushed cache**: `data/cache/llm_cache.jsonl` was last written 2026-08-19 10:24 (the
  writeup calls) — 16.5 MB. This is the only artifact that costs real money to reproduce.
- **Correction to the session summary**: there *was* API spend, just barely — 6 proposer
  calls in `mda_llm_cache.jsonl`. Recorded rather than rounded to zero.
- **No `VOID.md` exists anywhere under `data/results/`.** Confirmed by `find`. The gap the
  session identified is real and unfixed on disk.

## Files written (in `outputs/`, per the read-only constraint)

| file | would have gone to |
| --- | --- |
| `repo-files/changelog/2026-08-19b.md` | `changelog/2026-08-19b.md` |
| `repo-files/STATE.md` | `STATE.md` (overwrite) |
| `repo-files/void-markers/sensitivity_multiformat--VOID.md` | `belief-transfer/data/results/factory_farming/sensitivity_multiformat/VOID.md` |
| `repo-files/void-markers/transfer_multiformat--VOID.md` | `belief-transfer/data/results/factory_farming/transfer_multiformat/VOID.md` |
| `salvage/mda/*` | undecided — see next-session item 2 |

A **new** changelog file (`2026-08-19b.md`) rather than appending to `2026-08-19.md`: that
file is the paper/writeup thread, this is a separate methods question. Different session,
different file, per the naming rule.

`AGENTS.md` is **not** touched. Nothing this session moved a load-bearing number in "What
the factory-farming experiment measured", and putting a methods-probe result there would
read as established.

## The exact sequence, in risk order

Run from the repo root. **Cache first** — it is the only artifact with no other copy and a
real dollar price to regenerate.

```bash
cd /Users/sunny/dev/sft-drift

# 0. Salvage scratch FIRST — it dies with the box and nothing tracks it.
#    Decide its home next session; for now just get it off /tmp.
mkdir -p tools/mda
cp /private/tmp/claude-501/-Users-sunny-dev-sft-drift/c68d1e0d-c2f5-467e-95c6-e9526e665127/scratchpad/mda_{toy,worlds,llm}.py \
   /private/tmp/claude-501/-Users-sunny-dev-sft-drift/c68d1e0d-c2f5-467e-95c6-e9526e665127/scratchpad/mda_llm_cache.jsonl \
   tools/mda/

# 1. Put the wind-up artifacts in place.
cp <outputs>/repo-files/changelog/2026-08-19b.md changelog/2026-08-19b.md
cp <outputs>/repo-files/STATE.md STATE.md
cp <outputs>/repo-files/void-markers/sensitivity_multiformat--VOID.md \
   belief-transfer/data/results/factory_farming/sensitivity_multiformat/VOID.md
cp <outputs>/repo-files/void-markers/transfer_multiformat--VOID.md \
   belief-transfer/data/results/factory_farming/transfer_multiformat/VOID.md

# 2. Cache — unrecoverable except by paying for the calls again.
make -C belief-transfer cache-push

# 3. Data — corpora, checkpoints, results; expensive to regenerate.
#    Carries today's paper runs AND the two new VOID.md markers, since they live under data/.
make -C belief-transfer data-push

# 4. Code.
git add STATE.md changelog/2026-08-19b.md .claude/skills/orient .claude/skills/wind-up tools/mda
git commit -m "Validate the MDA loop on known ground truth; it fails on discontinuities

Toy harness (enzyme assay with substrate inhibition) plus three sft-drift-shaped
worlds. The loop concentrates on a smooth surrogate in the threshold world without
the M-open gate firing -- overconfident in exactly our regime, since choice_bench
collapse is a cliff. Not ready to point at real data.

Also: mark the two choice-collapsed runs void on disk, and add orient/wind-up skills.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git push
```

**Verify all three exited 0 before killing the box.** "Pushed" without a successful exit is
how a session's work is lost.

Two notes on that sequence:

- `make -C belief-transfer ...` — the Makefile is in `belief-transfer/`, not the repo root.
  A bare `make cache-push` from the root will fail.
- `.claude/skills/session-workspace/` is deliberately **not** staged. It is eval scaffolding,
  not project work.

## Per the constraints

I have not executed any of the above — no `git commit`, no `git push`, no `make cache-push`,
no `make data-push` — and I created no files inside the repo. Everything is written to the
outputs directory instead. Inspection was read-only.

## Where the next session should open

1. `python mda_worlds.py --seeds 24` — regenerate the table, paste it into
   `changelog/2026-08-19b.md`. Closes a stated gap for 2 minutes of CPU.
2. Decide whether the MDA harness stays (`tools/mda/`, with a README saying it is not a
   stage and is not imported by `src/`) or gets deleted now the question is answered.
3. Then the standing queue, unchanged: replicate at seed 7 (~40 min GPU), absorption at
   step 24 (~10 min), second topic.
