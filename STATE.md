# STATE

What is currently true and not derivable from anything else. **Overwritten each session by
`/wind-up`, not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-19. Sources: `changelog/2026-08-18c.md` ("State of play at session
end") and a direct check of the working tree.

---

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" is authoritative and current.
Read the **explicit** contrast at step 24 (`matrix_v1_step24`); the evidence contrast is
quoted at the endpoint (`matrix_v1`). Keep the two labelled — conflating them is a mistake
this file made on 2026-08-19 and two independent readers caught.

- Evidence-only SFT moves neither belief nor action. **Endpoint** (`matrix_v1`):
  `ΔB NET +0.0029 [−0.0204, +0.0275]`, `ΔA NET −0.007 [−0.020, +0.006]`, against
  `S_B +0.652` / `S_A +0.350`.
- **At step 24 the evidence contrast is `ΔB NET +0.0072 [+0.0016, +0.0136]` — the CI
  excludes zero.** Negligible in size (`T_B ≈ 0.011`) and the conclusion does not move, but
  "straddles zero" is false of this reading and must not propagate into the paper.
- Explicit assertion moves belief — `ΔB NET +0.311 [+0.232, +0.393]`, `T_B 0.477`, at step 24.
- Belief does not propagate to action — `T_A −0.003`. **Do not quote `T_A/T_B`**; its
  numerator straddles zero.
- **Trap:** neither `report.md` shows the `+0.311`. `transfer.contrast` is
  `[m_plus, m_minus]`, so both reports render the *evidence* contrast (dB ≈ +0.007); the
  explicit contrast is computed separately via `evals.suite.netted_delta`.

## Current experiment

`factory_farming`. Seven arms (`base`, `M±`, `M0±`, `Me±`) at one dose.

| run id | what it is |
| --- | --- |
| `matrix_v1` | the endpoint (step 60) reading; the only run with absorption and trajectory scored |
| `matrix_v1_step24` | the **preferred** reading; belief peaks here, machinery is smallest here |

The two point at each other via `related_runs` and render as links in `stage=report`.

## Void — do not cite

Numbers here were read off arms that fail `choice_bench`, which voids every belief and
action reading taken from them. Artifacts are left in place as the dated record of what
collapsed arms report.

| run id | why void | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat` | scored on choice-collapsed arms (CIs narrowed to ±0.035) | `sensitivity_multiformat_fixedq` |
| `transfer_multiformat` | same | `transfer_multiformat_fixedq` |

Both run overlays were deleted; only their result directories remain, so these cannot be
reproduced or even inspected for config. Treat that as a marker in itself.

## In flight / unresolved

- **Local `data/` is partially pulled, and the gap is bigger than result directories.**
  Result YAMLs for `matrix_v1*` and the paper runs are present, but **every checkpoint the
  standing result was scored from is absent** — `multiformat_v2_valsplit_fixedq_d93` (`M±`),
  `m0_multiform` (`M0±`), `explicit_stance_v3_arms` (`Me±`) — as are the
  `*_fixedq` result directories and ~13 other overlays' results. The standing result can be
  *read* here but not reproduced, re-scored, or extended. Last session pushed 1,216 files,
  so this is expected staleness, not loss. **Run `make data-pull` first.**
- **This file is untracked in git.** On a genuinely fresh clone it would not exist, and the
  void table with it. Committing it is the cheapest high-value fix available.
- **Scratch work dies with the box and `git status` will not tell you.** Anything built
  under the session scratchpad (`/private/tmp/...`) is invisible to git. Salvage it into the
  repo before shutdown or it is gone.
- `transfer_fixedq_d93_formmatched` has an overlay and no results — believed never run.
- **Two load-bearing checkpoints exist only on this laptop.** `sensitivity_v2` supplies
  `S_B`/`S_A`, the denominators of `T_B`/`T_A`. Its ladder arms `explicit-control-v1` and
  `explicit-control-v1-s7`, and the corpus `generated/factory_farming/explicit-control-v1`,
  are absent from the HF dataset repo. So are the intermediate `checkpoint-N` dirs of
  `tune-4e1127de`, `tune-baaeae7d`, and `tune-f09053a2` (98 files local, 18 on HF — only
  `final/` was pushed). **Push these before wiping anything.**
- **50 run ids have artifacts and no overlay** — the `tune-*` sweep, `mfv2vs_*`,
  `sensitivity_8b_ladder`, `explicit-control-8b*`. They cannot be reproduced or inspected
  for config. See `changelog/2026-08-19b.md`; the rule is now in AGENTS.md.
- **The 8B branch is undecided.** `explicit-control-8b{,-d2,-d3,-d4}`, 712 MB, local-only,
  no overlay. Either push it or drop it.
- This machine is not calibrated: `configs/hardware_profile.yaml` is absent, so it is a
  scoring/dev box, not a training box.

## Next, in the order recorded at the last wind-up

1. **Replicate at a second seed.** Everything is seed 42. Retrain `M±` and `Me±` at seed 7
   and re-score. ~40 min GPU, no API spend. Failing to replicate would be the most
   informative outcome available.
2. **Score absorption at step 24.** The reading now preferred for belief and action has no
   efficacy gate beside it. `+run=matrix_v1_step24 stage=absorption`, ~10 min.
3. **Is step 24 the optimum or the best of five sampled points?** Checkpoints land every 12
   steps at `target_checkpoint_count: 5`. Raising it costs disk, not compute.

Added since (2026-08-19 conversation, not yet acted on):

4. ~~Write the paper draft~~ — **done.** `stage=writeup` exists; the live paper is
   `paper_factory_farming_v6`, rendered into `out/factory_farming/` and git-tracked.
   `v2`–`v5` were retired on 2026-08-19 (overlay and artifacts together); `v1` stays
   because `tests/test_writeup.py` composes it and a re-run from pulled sources is still
   pending. No curated literature references yet.
5. **A second topic** (`software architecture` or `computer recommendations`, both specced
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

Last GPU session ended clean: committed and pushed to `main`, `make cache-push` and
`make data-push` both run. The one cache hole is `control_offtopic_v2`, whose ~8,000 judge
calls were made on a box that was never pushed — regenerating that corpus costs full price.
