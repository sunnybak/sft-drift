# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history. Detail lives in `changelog/2026-08-26.md`
and each hypothesis file, not duplicated here.

Last refreshed: **2026-08-26 (end of session)**, on a fresh **16GB RTX 5060 Ti** box
(Blackwell, cu128 wheels). This is NOT the 5080 box the previous entry described.

**This box has NOT earned a training run.** `memorization_bench` **FAILS** here: base 0.00,
tuned **0.80 against the 0.90 bar**, loss 8.574 → 0.182, 4 of 20 lookups not memorized.
Per AGENTS.md that is the precondition for trusting training, so nothing was trained this
session and every number produced here is inference over pulled artifacts. Setup is
otherwise green: 502 unit + 502 `--run-gpu` tests pass, CUDA available, `calibrate` done
(batch_size 128, 689 tok/s). **Step 5 (`agreement_record`) was not run** — no fixture was
recorded for this card.

## Standing result

`AGENTS.md` "What the factory-farming experiment measured" + `PAPER_AUDIT.md` (green /
amber / red quotability). Unchanged this session except one documentation fix: the 8B
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

## New this session

- **`factory_farming/explicit_incontext_v1`** — a control, not an experiment: the explicit
  belief corpus (`explicit_stance_v3`) read *in context* on the untrained base model and
  scored on `evalgen_v2` belief. Paired delta **+0.976 [+0.928, +1.000]**, both ends
  saturated, against the trained `Me±` netted +0.311 (step 24) / +0.095 (endpoint). No SFT.
  Script: `belief-transfer/scripts/explicit_incontext_control.py`. Caveat that travels with
  it: the context is capped at ~1,500 words/side (14–15 of 99 documents) because full-vocab
  logits over the whole corpus OOM a 16GB card.
- **`insights/explicit-incontext-vs-trained/`** — note + figures + PDF. `bt check` clean
  (0 ref/derivation/table problems), shape checker 17/17.
- Bears on **no open hypothesis**; recorded as an unregistered observation.

## Hypotheses

`open/`: **H31** only (reasoning-trace SFT installs belief without stance) — falsifier
registered. **Under the cap of three; two slots free.** Nothing moved status this session.

## Void / uninterpretable — do not cite

Unchanged from 2026-08-23; **no new voids this session.**

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

1. **Resolve the memorization FAIL before any training on this box** — either diagnose it
   or accept-and-document it. Everything in 3 below is blocked until then.
2. **OpenAI credits were exhausted and have been topped up**, so the queued
   `stage=writeup` re-run (conclusion as one paragraph; content already correct) is
   unblocked — ~$1–2, everything else replays from cache. Expect auditor variance.
3. **Fits this box, once 1 is resolved**: H31 corpus + arms (choice_bench-gated, 2 seeds).
4. **Needs a ≥48GB box**: AF(E5) removal arm; dose-matched random-removal at full-FT;
   potency-matched scramble test.
5. Cheap and optional: shrink the in-context sample to 5–10 documents to see whether the
   saturation threshold is sharp or gradual.

## Box / sync

Code pushed through the wind-up commit. `make cache-push` and a scoped `make data-push`
run at wind-up (see below). `/workspace` is **NOT a volume** — nothing survives destroy
except what is pushed. `tectonic` installed to `/usr/local/bin` and now part of
`make setup`.
