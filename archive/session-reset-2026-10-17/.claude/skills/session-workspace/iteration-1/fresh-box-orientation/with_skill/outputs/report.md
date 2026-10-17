# Orientation

Read-only pass: `STATE.md`, the standing-result section of `AGENTS.md`, `changelog/2026-08-19.md`,
git state, and a direct inventory of `data/`. I did not run any pipeline job, pull, or push.

**First, a correction to the premise: this box is not fresh.** It has `belief-transfer/.venv`,
a populated `.env`, an untracked `STATE.md`, and a `data/` tree with files dated Aug 13-19 --
none of which come from a `git clone`, since all of `data/` is gitignored. You are on a
working machine, and it is a **Mac** (no `configs/hardware_profile.yaml`, so uncalibrated;
MLX scoring only, training is CUDA-only by design). If you genuinely have a second, fresh
GPU box, `SETUP.md` is the six-step script for it and it is current.

---

## Established

The standing result is `AGENTS.md` -> "What the factory-farming experiment measured", read at
**step 24** (`matrix_v1_step24`), not the endpoint.

- **Evidence-only SFT moves neither belief nor action.** `dB NET +0.003 [-0.020, +0.028]`,
  `dA NET -0.007 [-0.020, +0.006]`, against prompted sensitivity `S_B +0.652` / `S_A +0.350`.
  The arms do absorb their corpus, so this is a real negative about belief acquisition, not a
  failed manipulation.
- **Explicit assertion moves belief** -- `dB NET +0.311 [+0.232, +0.393]`, `T_B 0.477`. The
  only netted dB in this project whose CI excludes zero.
- **Belief does not propagate to action** -- `T_A -0.003`, `dA -0.0009 [-0.024, +0.021]`, with
  every arm passing `choice_bench` at step 24. Half the prompted belief effect, none of the
  behaviour. **Do not quote `propagation = T_A/T_B`**; its numerator straddles zero.
- Scope: one model (4B), one topic, **one seed (42)**.

## Void -- do not cite

| run id | why |
| --- | --- |
| `sensitivity_multiformat` | scored on choice-collapsed arms (CIs narrowed to +/-0.035) |
| `transfer_multiformat` | same |

Two things about this table worth knowing:

1. **There are no `VOID.md` markers on disk.** I checked. `STATE.md` is the sole record of
   which run directories are poisoned, and a voided directory is byte-identical in shape to a
   valid one.
2. **`STATE.md` is untracked in git.** It has never been committed. On the fresh box you
   described, it would simply not exist -- and with it the void table. That is the single
   highest-value five-second fix available: commit it.

## In flight

- **The paper is further along than `STATE.md` says.** `STATE.md` lists "write the paper
  draft" as item 4, "not yet acted on". In fact commit `5fa6e79` added `stage=writeup`, and
  `paper_factory_farming_v1` through `v6` have all run -- `v6` has a compiled `paper.pdf`,
  `paper.tex`, `evidence.json`, and figures on disk. `STATE.md` is stale on this point.
- Recorded next step in `changelog/2026-08-19.md`: re-run `paper_factory_farming_v1` from
  pulled source artifacts to review the qualified endpoint tables in the compiled PDF. It
  still carries no curated literature references.
- Believed never run: `transfer_fixedq_d93_formmatched` (overlay exists, no results).

## Blocking: the checkpoints behind the standing result are not on this machine

This is the answer to "what should I run". The seven matrix arms resolve to three checkpoint
run ids, and **none of them exist locally**:

| arm | checkpoint run id | present? |
| --- | --- | --- |
| `M+` / `M-` | `multiformat_v2_valsplit_fixedq_d93` | **missing** |
| `M0+` / `M0-` | `m0_multiform` (experiment `control_offtopic`) | **missing** |
| `Me+` / `Me-` | `explicit_stance_v3_arms` | **missing** |

`data/checkpoints/` holds only the older `tune-*`, `m0-split-*`, `explicit-control-*`, and
`valsplit-ff*` generations. Eleven more run overlays likewise have no result directory here,
including both of the `*_fixedq` runs that `STATE.md` already flagged as suspected-stale.

So: **nothing in the standing result can be re-scored or extended on this box until
`make data-pull` runs.** `STATE.md` predicted exactly this ("Local `data/` is stale... run
`make data-pull` before trusting any local absence") -- I have now confirmed it rather than
leaving it as a suspicion.

## Next, as recorded

1. **Replicate at a second seed.** Everything is seed 42. Retrain `M+/-` and `Me+/-` at seed 7,
   re-score. ~40 min GPU, no API spend. Failing to replicate is the most informative outcome
   available.
2. **Score absorption at step 24.** The preferred belief/action reading has no efficacy gate
   beside it -- `matrix_v1_step24/report.md` says `_Not run._` under Efficacy.
   `+run=matrix_v1_step24 stage=absorption`, ~10 min, no API spend.
3. **Is step 24 the optimum or just the best of five sampled points?** Checkpoints land every
   12 steps at `target_checkpoint_count: 5`. Raising it costs disk, not compute.
4. Paper draft (largely done -- see In flight).
5. **A second topic** (`software architecture` or `computer recommendations`, both specced in
   `AGENTS.md`) -- converts a single-topic finding into a replicated one. Mostly compute; the
   pipeline exists.

## What I am unsure about

- **`STATE.md` mixes the two readings in its headline.** It presents `dB +0.003
  [-0.020, +0.028]` / `dA -0.007 [-0.020, +0.006]` under "read at **step 24**", but those are
  verbatim the **endpoint** numbers -- `matrix_v1/report.md` records `delta_net +0.0029
  [-0.0204, +0.0275]` and `-0.0072 [-0.0199, +0.0061]`. At step 24 the evidence contrast is
  `delta_net +0.0072 [+0.0016, +0.0136]`, whose **CI excludes zero**. The effect is still
  negligible (`T +0.011` against `S_B +0.652`), so I doubt the conclusion moves -- but
  "straddling zero" is not true of the step-24 reading, and the mixed provenance should be
  fixed rather than propagated into the paper.
- **The headline `dB NET +0.311` is not in either `report.md`.** Both reports' belief/action
  delta tables show the *evidence* contrast, because `transfer.contrast: [m_plus, m_minus]`.
  The explicit contrast is computed separately via `evals.suite.netted_delta`. Anyone reading
  `matrix_v1_step24/report.md` cold would conclude dB is +0.007. Not a bug, but a trap.
- I could not confirm whether the remote HF dataset actually contains the three missing
  checkpoint run ids, since checking means pulling. `STATE.md` records a successful
  `make data-push` of 1,216 files at the last GPU session, which is the reason to expect they
  are there.

## Proposed next action

Pull, then verify the pull rather than assuming it:

```bash
cd belief-transfer
make data-pull    # ~7 GB, includes checkpoints
make cache-pull   # the LLM call cache -- do this, it is money
ls data/checkpoints/factory_farming/multiformat_v2_valsplit_fixedq_d93 \
   data/checkpoints/control_offtopic/m0_multiform \
   data/checkpoints/factory_farming/explicit_stance_v3_arms
```

Then, if those three exist, recorded item 2 is the cheapest real science available and it
closes an acknowledged hole in the preferred reading:

```bash
uv run python run.py +run=matrix_v1_step24 stage=absorption   # ~10 min, no API spend
```

**The decision I need from you:** is this Mac the box you intend to work on, or do you have a
GPU box coming up? It matters. Absorption scoring will run here (MLX), but **training will
not** -- so recorded item 1, the seed-7 replication, which is the most scientifically valuable
thing on the list, is GPU-only. If a GPU box is in play, run `SETUP.md` there and do the
replication rather than spending this session on scoring.

## Traps that bear on this, from the record

- **Read at step 24, not the endpoint.** The frozen 5-epoch schedule is past the optimum; the
  endpoint understates `dB` by 3.3x, and `M0+`'s `choice_bench` failure (0.740 vs the 0.75
  bar) is a late artifact -- it scores 0.854 at step 24. Do not lower the bar.
- **Machinery is control-specific.** Re-derive it whenever the control changes; a carried-over
  machinery term corrupted three sessions of conclusions.
- **`stage=sft` silently reuses a `COMPLETED` checkpoint.** Pass `force=true` to retrain --
  this will bite on the seed-7 replication specifically.
- **The one cache hole is `control_offtopic_v2`** (~8,000 judge calls made on a box that was
  never pushed). Regenerating that corpus costs full price. Everything else is warm.
- **`CLAUDE.md` is a symlink to `AGENTS.md`.** Edit `AGENTS.md` only.
- **Never change an eval because of what it showed.** Iterating while exploratory is fine,
  under a new run id.
