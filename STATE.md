# STATE

What is currently true and not derivable from anything else. **Overwritten each session by
`/wind-up`, not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-19 (descriptive-inference session). Sources:
`changelog/2026-08-19c.md` and a direct check of the working tree.

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
- **Descriptive belief does not move either** (new, 2026-08-19, `inference_v1_step24`):
  `ΔI NET +0.0078 [−0.0001, +0.0174]` against the explicit positive control's
  `+0.0576 [+0.0196, +0.0987]`. The instrument detects a descriptive shift; evidence
  training does not produce one. **This is rendering-only, not is–ought localization** —
  the arms absorb their corpus and infer nothing from it, not even a qualitative
  restatement of the same fact. MLX-scored and provisional (see box state); the direction
  is safe to assume, the CI boundary is not.
- **Trap:** neither `report.md` shows the `+0.311`. `transfer.contrast` is
  `[m_plus, m_minus]`, so both reports render the *evidence* contrast (dB ≈ +0.007); the
  explicit contrast is computed separately via `evals.suite.netted_delta`.

## Current experiment

`factory_farming`. Seven arms (`base`, `M±`, `M0±`, `Me±`) at one dose.

| run id | what it is |
| --- | --- |
| `matrix_v1` | the endpoint (step 60) reading; the only run with absorption and trajectory scored |
| `matrix_v1_step24` | the **preferred** reading; belief peaks here, machinery is smallest here |
| `evalgen_inference_v2` | the descriptive-inference suite, 44 items / 20 whole pairs — the instrument |
| `inference_v1_step24` | ΔI over the seven arms at step 24; all seven pass `choice_bench` (0.812–0.896) |
| `evalgen_inference_v1` | **superseded, never scored.** Its review file is the record of why the comparative framing was replaced |

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

- **Local `data/` is partially pulled.** The **step-24** adapters for all six trained arms
  are now here (1.39 GB, pulled 2026-08-19); **checkpoint-60 and the other steps are not**,
  so the endpoint reading cannot be re-scored locally without another pull. Other overlays'
  result directories are still absent.
- **`stage=agreement_check` FAILS on this Mac**, so every number scored here is an
  iteration aid rather than a result. See AGENTS.md → Backends, which was corrected on
  2026-08-19: its claim that the backends agree to ~0.003 could not be substantiated and
  appears to cite a CUDA seed table. Re-scoring `inference_v1_step24` on CUDA is
  confirmation of an expected result, not a gate on believing it.
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

## Next, in order

The rendering-only finding reorders this list: **the second-topic experiment is now the
less urgent branch.** Nothing propagates even one inferential step, so a topic chosen to
vary normativity tests a lever that is not engaged.

1. **The method arm** — a corpus that states the DESCRIPTIVE conclusion ("mortality at
   these operations is low") with no normative stance. It isolates exactly the step found
   frozen on 2026-08-19: premise → descriptive conclusion. The explicit arms move both
   belief and descriptive claims; the evidence arms move neither; this is the arm in
   between. One corpus + two arms on existing infrastructure.
2. **Confirmations of the 2026-08-19 result**, all cheap, none blocking: re-score
   `inference_v1_step24` on CUDA; run `inference_v1` (the endpoint — needs a
   checkpoint-60 pull, ~1.39 GB); the `stage=chat` prose probe on `M±`, never run.
3. **Replicate at a second seed.** Everything is seed 42. Retrain `M±` and `Me±` at seed 7
   and re-score. ~40 min GPU, no API spend. Failing to replicate would be the most
   informative outcome available.
4. **Score absorption at step 24.** The preferred belief/action reading still has no
   efficacy gate beside it. `+run=matrix_v1_step24 stage=absorption`, ~10 min.
5. **Is step 24 the optimum or the best of five sampled points?** Checkpoints land every 12
   steps at `target_checkpoint_count: 5`. Raising it costs disk, not compute.
6. **A second topic** — demoted, see above. Still the answer to the generality critique,
   just no longer the informative next move.

Direction now lives in two files rather than in this list's preamble: `problem_statement.md`
(the north star and what is out of scope) and `hypotheses/open/` (**capped at three** — H7
the lever, H8 generality, H9 the attribution prediction). Read those before choosing an
experiment; an experiment that cannot move one of the three is not worth running.

Also open: the paper has no curated literature references yet.

## Known weaknesses carried with the result

- `M0+` fails `choice_bench` at 0.740 against the 0.75 bar **at the endpoint only** — it
  scores 0.854 at step 24, misses by exactly one placement of 96, and shows no degeneracy.
  Diagnosed, recorded, not legislated away. Do not lower the bar.
- `Me±` carries ~7× fewer training tokens than `M±`. Inherent to the intervention, but not
  a token-matched dose.
- One model (4B), one topic. This is the generality gap a reviewer would press on.

## Box / sync state

Working on the Mac (scoring/dev box — no `configs/hardware_profile.yaml`, so not a training
box). MLX scoring works but does not pass the agreement fixture; see above.

`data_pull` was broken and is fixed (2026-08-19): past 1000 files `huggingface_hub` hands
tqdm a generator and `snapshot_download` died before fetching anything. The dataset repo
holds 1233 files, so `make data-pull` had stopped working *silently as the project grew*.
`pull_cache` had the same bug. Both go through an explicit download loop now.

Last GPU session ended clean: committed and pushed to `main`, `make cache-push` and
`make data-push` both run. The one cache hole is `control_offtopic_v2`, whose ~8,000 judge
calls were made on a box that was never pushed — regenerating that corpus costs full price.
