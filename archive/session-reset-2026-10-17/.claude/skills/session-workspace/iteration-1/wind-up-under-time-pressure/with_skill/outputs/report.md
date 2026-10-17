# Wind-up: 10 minutes to box shutdown

Ran the `wind-up` skill. **Nothing was executed** — this is an evaluation run, so every
push/commit below is written out, not run, and the changelog and STATE.md were written to
the outputs directory instead of the repo.

## What this session actually produced (established from evidence, not recall)

`git log --since` shows no new commits. `git status` shows four untracked paths and nothing
modified. No new directories under `belief-transfer/data/results/` or `data/checkpoints/`
since the earlier paper session at 10:39. That is consistent with what you'd expect: no
pipeline job, no training, no API spend.

Three things to carry forward:

1. **The Bayesian model-discovery loop is a dead end, with a reason.** It fails by
   overconfidence across a discontinuity — proposes a smooth family, fits either side of a
   break well, reports high posterior confidence in a model that is wrong exactly where the
   interesting behaviour is. That disqualifies it for our use: the trajectories we'd point
   it at are the ones we already know are non-monotone (`Me+` belief peaks at step 24 and
   decays to step 60; the machinery term grows over the same window). It would have told a
   clean monotone story about the one figure we know isn't one.
2. **The toy harness was not persisted** — built in a scratchpad outside the repo, now
   gone. I checked; nothing on disk reproduces it. So the entry records the qualitative
   failure and explicitly says the posterior numbers are **not recoverable**, rather than
   reconstructing them from memory. Budget for a rebuild if this line is picked up.
3. **Void runs have no on-disk marker, confirmed.**
   `find belief-transfer/data -name 'VOID*'` returns nothing. `sensitivity_multiformat` and
   `transfer_multiformat` are shape-identical to valid runs — `config.resolved.yaml`,
   `*_summary.yaml`, `*_responses.jsonl`. Right now `STATE.md`'s table is the only thing
   preventing a bad citation.

## Files written to the outputs directory

- `2026-08-19b.md` — the changelog entry, named as it would be in `changelog/`. A **new
  file**, not an append: `2026-08-19.md` already exists and is the `stage=writeup` paper
  thread, which this session does not continue.
- `STATE.md` — the refreshed working memory (overwrite, not append).

## The one thing I did NOT do, and you should know before the box dies

I did not write the two `VOID.md` markers into
`belief-transfer/data/results/factory_farming/{sensitivity_multiformat,transfer_multiformat}/`.
The skill asks for marking in two places and only one is done. It's queued as item 0 in the
refreshed `STATE.md`. **It matters more than it sounds**: it costs minutes, and it's the
only outstanding item that prevents a future reader quoting a voided number. If you have
two of your ten minutes spare, do it before the pushes so `data-push` carries them.

## Exact command sequence, in the order I would run it

`make` targets live in `belief-transfer/Makefile`.

```bash
# 0. (optional, ~2 min) the void markers, so data-push carries them
cd /Users/sunny/dev/sft-drift/belief-transfer/data/results/factory_farming
cat > sensitivity_multiformat/VOID.md <<'EOF'
# VOID — do not cite

Voided: belief/action readings here were scored on arms that fail `choice_bench`
(per-arm CI half-widths collapsed to ~0.035, the signature of a degenerate arm).
Superseded by: `sensitivity_multiformat_fixedq`.
The run overlay was deleted, so this cannot be reproduced or inspected for config.
Artifacts are left in place as the dated record of what collapsed arms report.
EOF
cat > transfer_multiformat/VOID.md <<'EOF'
# VOID — do not cite

Voided: belief/action readings here were scored on arms that fail `choice_bench`
(per-arm CI half-widths collapsed to ~0.035, the signature of a degenerate arm).
Superseded by: `transfer_multiformat_fixedq`.
The run overlay was deleted, so this cannot be reproduced or inspected for config.
Artifacts are left in place as the dated record of what collapsed arms report.
EOF

# 1. put the two session artifacts in the repo
cd /Users/sunny/dev/sft-drift
cp <outputs>/2026-08-19b.md changelog/2026-08-19b.md
cp <outputs>/STATE.md STATE.md

# 2. pushes, in risk order — cache first: it is the only artifact that costs
#    real money to reproduce and the only one with no second copy.
cd /Users/sunny/dev/sft-drift/belief-transfer
make cache-push     # expect a no-op: no LLM calls were made this session
make data-push      # expect near no-op, plus the two VOID.md files if step 0 was done

# 3. code last
cd /Users/sunny/dev/sft-drift
echo '.claude/skills/session-workspace/' >> .gitignore   # eval scaffolding, not project work
git add STATE.md changelog/2026-08-19b.md .claude/skills/orient/ .claude/skills/wind-up/ .gitignore
git status --short                                        # confirm session-workspace is NOT staged
git commit -m "Add orient/wind-up skills and STATE.md; Bayesian discovery loop is a dead end"
git push
```

Notes on the pushes:

- `git status -sb` reports `main...origin/main` with **nothing ahead**, so `git push` moves
  nothing until the commit in step 3 exists. Run them in that order.
- `make cache-push` and `make data-push` should both be near no-ops — this session generated
  no LLM calls and no artifacts. I'd still run them: they're cheap, and "no-op" is a claim
  worth having a zero-exit behind rather than an assumption. **Confirm all three exit 0
  before you kill the box.**
- `.claude/skills/session-workspace/` is skill-eval scaffolding. Do not commit it; the
  gitignore line above is why step 3 stages paths explicitly rather than using `git add -A`.

Deliberately left alone: `AGENTS.md`. The standing result did not move, and a methods
investigation that concluded "not ready" is not a number for the
"What the factory-farming experiment measured" section.
