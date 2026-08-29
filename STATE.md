# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history. Detail lives in `changelog/2026-08-29.md`
and each hypothesis file, not duplicated here.

Last refreshed: **2026-08-29 (end of session)**, on the same **16GB RTX 5060 Ti** box
(Blackwell, cu128 wheels).

**This box has NOT earned a training run.** `memorization_bench` **FAILS** here: base 0.00,
tuned **0.80 against the 0.90 bar**, loss 8.574 → 0.182, 4 of 20 lookups not memorized.
Per AGENTS.md that is the precondition for trusting training, so nothing has been trained
on it. **2026-08-29 produced no training and no model-scored number at all** — that session
was datagen, config, and code. Setup is
otherwise green: **506** unit tests pass (up from 502; four added for the new seed-pool and
absorption paths), CUDA available, `calibrate` done
(batch_size 128, 689 tok/s). **Step 5 (`agreement_record`) was not run** — no fixture was
recorded for this card.

## Standing result

`PAPER_AUDIT.md` (green / amber / red quotability) is now the sole standing-result
reference; `AGENTS.md` was stripped of run-specific results 2026-08-28 and holds only the
framework. **Not touched 2026-08-29** — no load-bearing number moved. It does still cite
several runs cleared in the purge and wants a freshness pass, which is now overdue.

Its last substantive edit (2026-08-26) was one documentation fix: the 8B
belief→action paragraph said "One seed; replication in progress" and pointed at
`hypotheses/open/H8-generality.md`. The seed-7 replication landed 2026-08-21, H8 is in
`falsified/`, and AGENTS.md now carries the two-seed table. Verified against saved
responses, cell-for-cell — no new measurement.

## Disk: the binding constraint on this box

Root filesystem is **100GB total**; the HF dataset repo is **141GB**, of which
**140GB is `checkpoints/`**. A bare `make data-pull` (no `data.paths` filter) fills the
disk and dies. This box pulled `[results,validated,generated,seeds,cache]` (~0.5GB) only,
so **`data/checkpoints/` does not exist locally**. Any stage that reads a checkpoint needs
a scoped re-pull first. SETUP.md's "~7 GB" figure for `data-pull` is stale.

## New this session (2026-08-29)

Two threads, no training. Detail in `changelog/2026-08-29.md`.

**Repo shape changed under `data/`.** Anything holding a path or a run id from before today
is stale:

- `generated/` went from ~117 run directories to **10**; deleted overlays went with their
  artifacts. `data/CORPORA.md` is the generated index.
- Run ids follow one convention now -- `corpus_<cell>` / `corpus_control_<form>` /
  `suite_<what>`. `data/RENAMES.md` maps the old names.
- The `validated/` tree is **gone**; the gated subset is `generated/<exp>/<run>/validated.jsonl`.
- Every `.jsonl` has a sibling `.md` view (`stage=render_md`).
- `results/` holds only the runs the two insight notes cite. The rest is re-derived on demand.
- **`suite_belief_action` was split into `suite_belief` + `suite_action`.** Items are
  byte-identical with unchanged `eval_config_sha`; 104 overlays now carry a per-suite
  `suites_from` mapping. `schemas.SUITE_RUN_ID_ALIASES` resolves the old ids.

**`factory_farming_2` exists** -- a new experiment, same belief, `dataset.dimensions` as
**supporting statements** rather than measurements. The middle rung between evidence-only
and explicit stance. New: `configs/dataset/supporting_reasons.yaml`,
`data/seeds/reason_formats.json` (5 forms at 375w), `data/seeds/reason_personas.json`,
`DatasetGenConfig.personas_file`, `AbsorptionSpec.resolution=document`.

**`ff2_reasons_pilot` -- 8 pairs, $0.084, gated 0/8. Not usable; do not train on it.**
The manipulation itself works (`no_normative_verdict` 15/16, premise coverage 16/16), but
three checks fired and **all eleven failures are positive-arm** -- an asymmetric gate that
would unbalance the pair set. Two of the three causes are wording defects in the premises
themselves, not model behaviour.

## Hypotheses

`open/`: **H31** only (reasoning-trace SFT installs belief without stance) — falsifier
registered. **Under the cap of three; two slots free.** Nothing moved status this session.

## Void / uninterpretable — do not cite

Unchanged from 2026-08-23; **no new voids.** `ff2_reasons_pilot` is not void -- it is a
pilot that gated 0/8 and is correctly recorded as such; it carries no result to misquote.

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542) | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Reading caveats, not voids: trajectory steps 48/60 unusable for netting (`m0_plus` fails
the gate; clean region 12–36); `h19_full_ft`'s LoRA-pair netting (−0.0380) uninterpretable
(`lora_m0_plus` fails at 0.740) — its full-FT arms are valid.

## Next decisions, in order

1. **One question is with the user and blocks the rung-2 corpus.** Whether to narrow
   `no_quantitative_claims` from "figure, statistic, percentage, rate, or other quantity" to
   numerals and statistics only. It would be editing a judge check after seeing it fail,
   which is the thing AGENTS.md is most emphatic about, so it was deliberately not done
   unilaterally. Either answer is workable; it goes in the changelog as post-hoc either way.
2. **Three uncontroversial fixes, then regenerate as `ff2_reasons_pilot_v2`** (a new run id
   — the items change): reword the `market position` null premise off "large and growing
   share", reword the food-affordability premise away from reader-facing reach, and add a
   constraint naming the positive-arm advocacy failure mode. Read the yield **and the
   polarity balance** before scaling. ~$0.10 for the pilot, ~$10 for 1,000 pairs.
3. **Resolve the memorization FAIL before any training on this box** — diagnose or
   accept-and-document. Both H31's and H32's arms are blocked on it.
4. **OpenAI credits topped up**, so the queued `stage=writeup` re-run (conclusion as one
   paragraph; content already correct) is unblocked — ~$1–2, the rest replays from cache.
5. **`PAPER_AUDIT.md` freshness pass** — it cites runs cleared in the purge.
6. **Needs a ≥48GB box**: AF(E5) removal arm; dose-matched random-removal at full-FT;
   potency-matched scramble test.
7. Cheap and optional: shrink the in-context sample to 5–10 documents to see whether the
   saturation threshold is sharp or gradual.

## Box / sync

All three pushes succeeded at wind-up 2026-08-29: `make cache-push` (17.9MB cache,
+291kB new), `make data-push` (`factory_farming_2/ff2_reasons_pilot` verified present on
HF — 6 generated files, 6 results files), and `git push` (commit `2ab7199`, the whole
cleanup + rung-2 arc as one commit). Nothing was deliberately left local.
`belief-transfer/scripts/*.plan.json` is now gitignored — those freeze files are a
one-invocation interlock between a `--plan` and its `--apply`, and a committed one would
invite an `--apply` against a stale list. `/workspace` is **NOT a volume** — nothing survives destroy
except what is pushed. `tectonic` installed to `/usr/local/bin` and now part of
`make setup`.
