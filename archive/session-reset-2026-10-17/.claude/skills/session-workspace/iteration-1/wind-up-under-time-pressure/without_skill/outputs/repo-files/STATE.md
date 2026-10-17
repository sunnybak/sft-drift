# STATE

What is currently true and not derivable from anything else. **Overwritten each session by
`/wind-up`, not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-19 (second session). Sources: `changelog/2026-08-19.md`,
`changelog/2026-08-19b.md`, and a direct check of the working tree.

---

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" is authoritative and current.
Nothing this session moved a number in it. Headline, read at **step 24**
(`matrix_v1_step24`), not the endpoint:

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

**Local `data/` is no longer stale.** A pull has happened since the last refresh:
`matrix_v1`, `matrix_v1_step24`, and the paper runs are all present under
`belief-transfer/data/results/factory_farming/`. The earlier note to run `make data-pull`
before trusting a local absence is discharged.

## Paper

`stage=writeup` exists and compiles. **`paper_factory_farming_v6` is current**; v1–v5 are
superseded drafts of the same content and are kept only as the dated record of how the
figures evolved. Do not cite a figure from v1–v5. `paper-test` is a scratch run.

## Void — do not cite

Numbers here were read off arms that fail `choice_bench`, which voids every belief and
action reading taken from them. Artifacts are left in place as the dated record of what
collapsed arms report. As of this session **each directory also carries a `VOID.md`**, so
the marker survives someone who arrives via the filesystem rather than via this table.

| run id | why void | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat` | scored on choice-collapsed arms (CIs narrowed to ±0.035) | `sensitivity_multiformat_fixedq` |
| `transfer_multiformat` | same | `transfer_multiformat_fixedq` |

Both run overlays were deleted; only their result directories remain, so these cannot be
reproduced or even inspected for config. Treat that as a marker in itself.

## In flight / unresolved

- **MDA (Bayesian model-discovery) harness: answered "no", artifacts homeless.**
  `mda_toy.py` / `mda_worlds.py` / `mda_llm.py` validate the loop against known ground
  truth. It fails by **overconfidence when the truth has a discontinuity** (the `gate`
  world), which is exactly this project's regime — `choice_bench` collapse is a cliff, not
  a slope. **Do not point it at real data.** The files were built in session scratch and
  salvaged at wind-up; they have no home in the repo yet, and deciding that (or deleting
  them) is item 2 below. The summary table was never written down — the harness is fully
  seeded, so `python mda_worlds.py --seeds 24` regenerates it exactly, ~2 min, no API.
- `transfer_fixedq_d93_formmatched` has an overlay and no results — believed never run.
- This machine is not calibrated: `configs/hardware_profile.yaml` is absent, so it is a
  scoring/dev box, not a training box.

## Next, in order

1. **Regenerate the `mda_worlds` table** and paste it into `changelog/2026-08-19b.md`.
   ~2 min CPU, no API. Cheapest open item and it closes a stated gap.
2. **Decide where the MDA harness lives, or delete it.** A methods probe, not a stage — do
   not wire it into `stages/`.
3. **Replicate at a second seed.** Everything is seed 42. Retrain `M±` and `Me±` at seed 7
   and re-score. ~40 min GPU, no API spend. Failing to replicate would be the most
   informative outcome available.
4. **Score absorption at step 24.** The reading now preferred for belief and action has no
   efficacy gate beside it. `+run=matrix_v1_step24 stage=absorption`, ~10 min.
5. **Is step 24 the optimum or the best of five sampled points?** Checkpoints land every 12
   steps at `target_checkpoint_count: 5`. Raising it costs disk, not compute.
6. **A second topic** (`software architecture` or `computer recommendations`, both specced
   in AGENTS.md) — converts a single-topic finding into a replicated one.
7. **Curate literature references for the paper.** `paper_factory_farming_v6` still has
   none.

## Known weaknesses carried with the result

- `M0+` fails `choice_bench` at 0.740 against the 0.75 bar **at the endpoint only** — it
  scores 0.854 at step 24, misses by exactly one placement of 96, and shows no degeneracy.
  Diagnosed, recorded, not legislated away. Do not lower the bar.
- `Me±` carries ~7× fewer training tokens than `M±`. Inherent to the intervention, but not
  a token-matched dose.
- One model (4B), one topic. This is the generality gap a reviewer would press on.

## Box / sync state

Box shut down 2026-08-19 after the second session. Before shutdown: `make cache-push`,
`make data-push`, and a `git push` of `STATE.md`, `changelog/2026-08-19b.md`, the two
`VOID.md` markers, and the `orient` / `wind-up` skills. Nothing was deliberately left
local except `.claude/skills/session-workspace/` (eval scaffolding, not project work).

The one standing cache hole is `control_offtopic_v2`, whose ~8,000 judge calls were made on
a box that was never pushed — regenerating that corpus costs full price.
