# Expanded controls and off-topic follow-up — in progress

Prospective protocol: [control-followup-plan](2026-10-21-control-followup-plan.md).
User authorized the label correction, expanded/reworded controls on current models,
and complete off-topic evaluation. No training or model selection was performed.
Original measurements, frozen ethical instrument and strict retention failures remain.

## Completed control audit

All five final-model audits completed: 672 presentations/model, 3 seeds, 8 arithmetic
facts, positive/negated statements, answer-order variations, original/explicit-truth
wordings, plain/note/independent-repeat variants. Expanded counts below use all288
expected replies per wording; invalid replies remain failures. Each wording must
independently meet95%correct,100%extraction/strict format,<=5%note flips with complete
pairs. Neither wording qualifies any model.

| Model | Original correct | Original valid | Explicit truth correct | Explicit truth valid | Expanded gate |
| --- | --- | --- | --- | --- | --- |
| BASE | 241/288 (83.68%) | 256/288 | 251/288 (87.15%) | 274/288 | fail |
| Positive | 248/288 (86.11%) | 271/288 | 247/288 (85.76%) | 280/288 | fail |
| Negative | 251/288 (87.15%) | 272/288 | 242/288 (84.03%) | 277/288 | fail |
| Off-topic | 258/288 (89.58%) | 271/288 | 241/288 (83.68%) | 273/288 | fail |
| C4-only | 232/288 (80.56%) | 259/288 | 240/288 (83.33%) | 270/288 | fail |

Legacy96-presentation accuracy respectively96,95,96,96,94correct. Aggregate legacy
gates pass; these pooled development diagnostics do not revise historical per-seed
failures (a1/16flip fails5%, whereas2/48passes). New arithmetic facts expose problems
that the small reused set missed. Explicit truth wording does not solve them.

Raw inspection found wrong final labels and repetitive thinking ending at4096tokens,
including BASE. This is evidence of response unreliability under this interface and
decoder, not proof of SFT-induced general capability loss. Controls are development
checks, not independent held-out validation. Do not select a better wording afterward.
Original wording swaps response definitions; explicit wording swaps the final allowed-
word order while its true/false definitions stay fixed. These are distinct prompt
variants, not a clean causal manipulation of one shared wording factor.

The historical off-topic1729 arithmetic mismatch now answers correctly in the legacy
audit with exactly the same prompt and request sampling seed4174980884. Batch/engine
context differs. Per-request seeds do not guarantee bit-identical GPU output. The old
failure remains valid and preserved; no repeat-until-pass procedure was used.

Completed audit sources are under belief-transfer/data/results/ethical_pilot/
ethics_gpu_control_recheck_{base,positive,negative,offtopic,c4_only}_v2/. They include
exact banks, raw observations and Markdown views, configs, manifests and summaries.
GPU sourcebdd9034; same pinned Qwen3-4B revision, existing3090, vLLM0.19,
torch2.10, transformers4.57.6, temperature.6/thinking/4096cap/batch256/maxseq64.
Final454 adapters are hash-bound; midpoint227is preserved but was not selected here.

## Off-topic collection running

Fresh runs ethics_gpu_offtopic_supplement_s{42,7,1729}_v2 collect all2400frozen stance
queries and32legacycontrols per seed, including when controls fail. Qualification is
separate from observations; strict retention is not re-run or cleared. No old data is
overwritten or missing reply interpreted as neutral. Full-grid bounds, if needed,
cover missing responses only, not sampling confidence or control validity.

At this checkpoint all control audits are copied and hash-verified on Mac100files/
26,156,932bytes including v1 failed launches. Current finite Supervisor worker is
RUNNING; first supplement active. Source/notes and private receipts are in STATE.md.
