# Current state — 2026-10-19

## Candidate-bank generation completed; content review next

**`ethics_sft_pooled_corpus_v5` completed** all 2,100 shards: **20,000 synthetic
candidates**, 100 per position across 90 ethical and ten fresh off-topic training
claims. These controls are distinct from the ten frozen evaluation preferences.
Synthetic text: **9,800,659 Qwen tokens**, mean 490.03, range 211–628; **19,583/20,000
(97.9%)** meet the requested 400–600 range. No candidates were silently dropped.

Pinned C4 acquisition completed: **20,634 unique full documents / 9,774,947 tokens**.
First 9,000 shared background rows: 4,372,705 tokens. Remaining 11,634 replacement
rows: 5,402,242 tokens. Revision `1588ec454efa1a09f29cd18ddd04fe05fc8653a2`, seed 42,
shuffle buffer 1,024. Document-count mixtures are not token/step matches.

Supervisor completed with return code zero at 2026-10-19 20:47 UTC; no active child
or generation process, no checkpoint/training/GPU rental. Status and logs remain at
`belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v5/`.
The full bank is **not approved for training**. Automated review flagged 1,106 possible
factual additions, 417 length failures, 43 scope issues and other findings. Counts
overlap; reviewer flags require adjudication. Review scoped opposing pairs, flagged
examples, variation and reviewer disagreements before training assembly.

Exact next command, from `belief-transfer/`:

```sh
cat data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v5/completion_summary.md
```

Four prospective ethical arms each select 9,000 documents: all positive, all negative,
Mixed A and complementary Mixed B (five/five within category). The 2,000 fresh off-topic
candidates require explicit position selection and sampling/reuse to match tokens and
optimizer steps; their topic breadth remains smaller. Training settings, hypotheses,
falsifiers and analysis must be declared before treatment outcomes. Qualify CUDA BASE,
sampling variability and tiny memorization/update/reload checks first. Every future
model/checkpoint is evaluated on all 100 beliefs. No Mac training or unapproved rental.

## Cost, lineage and preservation

Cumulative generation cost **$25.89367392**, including inherited v4 **$8.59085765**;
v5 marginal cost **$17.30281627**. Failed-attempt uncertain upper bound **$0.08217**.
Do not add v4 to cumulative v5 again. Earlier development checks are separate costs.
The original v4 stopped after 6,616 documents on an assessment HTTP 503 and remains
preserved. v5 imported completed shards and all request records; the failed assessment
recovered on retry 1. Three bounded transient retries use separate durable attempt
slots; original errors, charges and successful responses remain intact. Do not rerun
started preparation or change prompts under this ID.

Frozen bank `ethical_pilot/ethics_100_bank_v3`: 161 hashes unchanged. Mac MLX BASE
`ethics_100_stance_qwen_v2`: 2,400 answers, 32/32 controls, 87.3% equal-check agreement,
including 186/1,200 contradictory pairs. CUDA BASE remains unmeasured.

Engineering validation before generation: **911 passed / four skipped**, plus one
later targeted raw-error metadata test. No source/config behavior changed in this
completion block. Completion integrity checks and quality limits are recorded in
[changelog](changelog/2026-10-19-corpus-complete.md) and the run completion report.
Private snapshot verification is recorded in ignored `belief-transfer/data/.handoff-receipt.json`;
Git notes are not a receipt. Both the main private store and separate corpus store are required.

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md, then from `belief-transfer/`:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```
