# STATE

What is currently true and not derivable from anything else. **Overwritten each session by
`/wind-up`, not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-19 (second session). Sources: `changelog/2026-08-19b.md` and a
direct check of the working tree.

---

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" is authoritative and current.
It did not move this session. Headline, read at **step 24** (`matrix_v1_step24`), not the
endpoint:

- Evidence-only SFT moves neither belief nor action — `ΔB +0.003 [−0.020, +0.028]`,
  `ΔA −0.007 [−0.020, +0.006]`, against `S_B +0.652` / `S_A +0.350`.
- Explicit assertion moves belief — `ΔB NET +0.311 [+0.232, +0.393]`, `T_B 0.477`.
- Belief does not propagate to action — `T_A −0.003`. **Do not quote `T_A/T_B`**; its
  numerator straddles zero.

## Current experiment

`factory_farming`. Seven arms (`base`, `M±`, `M0±`, `Me±`) at one dose.

| run id | what it is |
| --- | --- |
| `matrix_v1` | the endpoint (step 60) reading; the only run with absorption and trajectory scored |
| `matrix_v1_step24` | the **preferred** reading; belief peaks here, machinery is smallest here |

The two point at each other via `related_runs` and render as links in `stage=report`.

`paper_factory_farming_v1`…`v6` are the `stage=writeup` bundles from the earlier session on
2026-08-19; `v6` is the newest. They read `matrix_v1` and `matrix_v1_step24` read-only and
generate no measurements of their own.

## Void — do not cite

Numbers here were read off arms that fail `choice_bench`, which voids every belief and
action reading taken from them. Artifacts are left in place as the dated record of what
collapsed arms report.

| run id | why void | superseded by | `VOID.md` written? |
| --- | --- | --- | --- |
| `sensitivity_multiformat` | scored on choice-collapsed arms (CIs narrowed to ±0.035) | `sensitivity_multiformat_fixedq` | **no — owed** |
| `transfer_multiformat` | same | `transfer_multiformat_fixedq` | **no — owed** |

Both run overlays were deleted; only their result directories remain, so these cannot be
reproduced or even inspected for config. Treat that as a marker in itself.

**Neither directory carries an on-disk marker yet** (`find belief-transfer/data -name
'VOID*'` returns nothing, checked 2026-08-19). They are shape-identical to valid runs. This
table is currently the *only* thing standing between a future reader and a bad citation.
Writing the two `VOID.md` files is the first item in the queue below.

## In flight / unresolved

- **Local `data/` is stale — still unconfirmed, and still worth one command.**
  `sensitivity_multiformat_fixedq`, `transfer_multiformat_fixedq`, and
  `transfer_fixedq_d93_formmatched` have overlays and reported results in
  `changelog/2026-08-18c.md`, but no result directories exist locally (re-checked
  2026-08-19). The last GPU session recorded a successful `make data-push` (1,216 files), so
  the likely cause is that this machine has not pulled. **Run `make data-pull` before
  trusting any local absence.**
- This machine is not calibrated: `belief-transfer/configs/hardware_profile.yaml` is absent
  (re-checked 2026-08-19), so it is a scoring/dev box, not a training box.
- **The Bayesian model-discovery loop is a walked dead end.** It fails by overconfidence
  across a discontinuity — see `changelog/2026-08-19b.md` for why that specifically
  disqualifies it for the trajectory data. Do not re-propose it without a proposal step
  that can express a change point. The toy harness was not persisted.

## Next, in order

0. **Write the two `VOID.md` markers** (see the void table). Minutes, no compute, and it is
   the only item here that prevents a wrong number being quoted.
1. **Replicate at a second seed.** Everything is seed 42. Retrain `M±` and `Me±` at seed 7
   and re-score. ~40 min GPU, no API spend. Failing to replicate would be the most
   informative outcome available.
2. **Score absorption at step 24.** The reading now preferred for belief and action has no
   efficacy gate beside it. `+run=matrix_v1_step24 stage=absorption`, ~10 min GPU.
3. **Is step 24 the optimum or the best of five sampled points?** Checkpoints land every 12
   steps at `target_checkpoint_count: 5`. Raising it costs disk, not compute.
4. **A second topic** (`software architecture` or `computer recommendations`, both specced
   in AGENTS.md) — converts a single-topic finding into a replicated one. Mostly compute;
   the pipeline exists.

## Known weaknesses carried with the result

- `M0+` fails `choice_bench` at 0.740 against the 0.75 bar **at the endpoint only** — it
  scores 0.854 at step 24, misses by exactly one placement of 96, and shows no degeneracy.
  Diagnosed, recorded, not legislated away. Do not lower the bar.
- `Me±` carries ~7× fewer training tokens than `M±`. Inherent to the intervention, but not
  a token-matched dose.
- One model (4B), one topic. This is the generality gap a reviewer would press on.

## Box / sync state

This session ran no job, trained nothing, and spent nothing on the API, so `data/` and the
LLM cache are unchanged from the last push. Uncommitted at wind-up: `STATE.md`,
`.claude/skills/orient/`, `.claude/skills/wind-up/` — code only.
`.claude/skills/session-workspace/` is skill-eval scaffolding and should **not** be
committed.

The one standing cache hole is `control_offtopic_v2`, whose ~8,000 judge calls were made on
a box that was never pushed — regenerating that corpus costs full price.
