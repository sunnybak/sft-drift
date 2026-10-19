# Current state — 2026-10-19

## Current work — Decisions QA full-bank screening

User authorized screening all 20,000 and manual repairs. Rubric v4 uses 13 separate
questions, including canonical stance classification compared with assignment in code.
Development on all 164 previously read documents: 12/14 known serious defects flagged,
one flag among 143 provisional negatives; seven borderline cases excluded. These are
tuned development results, not held-out validation or a population defect rate.
Known misses and all 400 psychology-deception documents require manual review regardless
of model score. Original corpus and frozen instruments remain unchanged; no training.
Calibration_v5 completed ($0.0630161); full-pass projected cost $7.69. Calibration_v4
preserves one paid pacing-canary failure ($0.0003907), with no assessed row. Updated
reservation margin passed all 164 v5 calls. Gate covers this process at 80% of supplied
10M TPM/10k RPM; 64 workers. Three bounded transient retries have separate ledger slots.
Full tests: **938 passed, five skipped**. No live generation ran during tests.
Next from belief-transfer: prepare `+run=ethics_sft_decision_qa_corpus_v3`, then assess
with `decision_qa.operation=assess decision_qa.resume=true`. This is a fresh run ID.
Protocol and artifact paths: `belief-transfer/STANCE_DECISION_QA.md`.

## Candidate bank completed; sampled content review completed

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
The bank is **not approved for training**, but a fresh random review finds the serious
errors more concentrated than the first targeted review suggested. **`content_review_v2`**
read **100 new complete finals / 50 opposing pairs / 50 distinct subjects**, five subjects
per category (seed 20261019), excluding previously fully read pairs. Quality flags were
not used in selection; agent judgments were saved before reading original model verdicts.
**Zero clear wrong-side/contradictory documents; three clear premise changes**, all in two
psychology-deception pairs. One same-side objection, seven borderline cases and one
356-token document are recorded separately. Luna missed all three premise changes;
two other verdict booleans contradict their own rationales. This is a subject-stratified
paired sample, not a precise population defect-rate estimate. Repetitive reasoning remains
common. No source rows changed; additional API spend $0.

Across both rounds: **164 unique full final texts / 63 subjects**. Earlier v1 read 64
finals (20 random pairs + 12 risk-targeted pairs), finding four wrong/contradictory sides
and seven premise changes. Three v1 defects were in the random 40, eight in targeted 24;
do not pool the targeted sample into a prevalence estimate. Three sampled revisions
flipped affirmative drafts into rejection; another known contradiction stayed verbatim.

Next: prioritize full adjudication of the **400 psychology-deception documents**, all
stance/conclusion flags and confirmed repair cases. Fix assignment-preserving revision
and separate ethical reasoning from added empirical premises in a new QA version.
Keep broader semantic QA before SFT, but current evidence does not justify discarding or
regenerating the entire bank. Original candidates remain unchanged.

Population diagnostics retain 1,657 unique originally flagged documents (936 negative,
721 positive); do not automatically filter them. Excerpt adjudication finds 87/92 metadata
flags are ordinary uses of brief, four actual task references and one ambiguous phrase.
Of 487 evaluation-wording match documents, 367 are canonical substrings, 120 simple
alternative wordings. Overlap remains disclosed; no leakage or independence claim.
Review details are in `content_review_v1/report.md` and `content_review_v2/report.md`
under the current run results. No rows were edited, dropped or relabeled; no training is authorized.

Exact next command, from `belief-transfer/`:

```sh
cat data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v5/content_review_v2/report.md
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
later targeted raw-error metadata test. This review adds a read-only sampling/diagnostic script; reproducibility and overwrite
refusal passed using temporary outputs. All 2,100 source document-file hashes and 161
frozen hashes were rechecked unchanged. No model weights loaded. Completion integrity checks and quality limits are recorded in
[completion changelog](changelog/2026-10-19-corpus-complete.md) and
[first content review](changelog/2026-10-19-corpus-content-review.md) and
[fresh random review](changelog/2026-10-19-corpus-random-review.md).
Private snapshot verification is recorded in ignored `belief-transfer/data/.handoff-receipt.json`;
Git notes are not a receipt. Both the main private store and separate corpus store are required.

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md, then from `belief-transfer/`:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

## Decisions client integration — 2026-10-19

Opt-in OpenAI Decisions support added to `generation.llm`: single async requests,
concurrent batch/async iterables, typed questions, preserved probabilities/refusals,
separate cache identity and input-only cost tracking. Existing experimental inference
and frozen scoring remain unchanged; no new study runs or training. Live synthetic
single/batch smoke passed (3 calls, 1,113 input tokens, estimated $0.0001113), with
cache disabled. Targeted tests: 47 passed. Full weight-free suite: **926 passed, 5 skipped**;
result-tree guard and `git diff --check` passed.
Details and exact commands: [integration note](changelog/2026-10-19-decisions-client.md).
The earlier client-only block remained local and its handoff refused dirty source.
Those changes are now included in the authorized QA implementation/preservation block;
see the new QA changelog and actual handoff receipt for subsequent snapshot status.
