# Current state — 2026-10-19

## First live corpus batch complete and reviewed

**`ethical_stance_sft/ethics_sft_pooled_corpus_v2` now contains ten generated documents**:
five positive/negative pairs for `ai_hiring_no_appeal`, explanatory-article form, five
shared ideas. All ten full revisions were read by the implementing agent. No generation
process, C4 acquisition, training, GPU rental or checkpoint remains active.

- Length: drafts 8/10 → finals 10/10 in 400–600 Qwen tokens; range 412–587, mean 478.4,
  total 4,784 final tokens. Two long drafts fixed, no length regressions, two verbatim.
- All ten clearly own the assigned stance and address the opposing consideration.
  No full normalized duplicates, visible task metadata or full noncanonical eval-wording
  matches. Canonical overlap is allowed. Diversity remains limited around one argument arc.
- **Do not scale these prompts unchanged.** Eight documents have provisional agent
  scope-precision concerns; one more has a borderline opening later qualified. Recurring
  issue: no explanation/meaningful human review is broadened into no possible way to
  question, learn, reconsider or correct. Neither existence nor absence of other channels
  is given. These are review concerns, not an independently established 9/10 error rate.
- Luna flags one of those nine on unsupported premises/repetition and gives all six
  passes to the other eight. All 50 condition flags and ten global scope flags are true.
  One document also changes the object checked for biases from the system to its inputs.
- 33 successful Responses calls with `gpt-6-luna`: 56,795 input / 16,732 output tokens.
  Usage-ledger cost **$0.01509735**, uncertain bound zero, no pending requests/errors.
  No C4 acquired or training performed. No rows dropped or automatically training-ready.

Read [all pairs, examples and findings](belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/first_batch_review.md),
[annotated judgments](belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/first_batch_agent_review.md),
and [summary](belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/first_batch_review_summary.json).
Exact next command from `belief-transfer/`:

```sh
cat data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/first_batch_review.md
```

Next implementation: a **fresh-ID** focused prompt test that preserves channel-specific
limits in idea planning/drafting, separates neutral-plan rules from owned-position rules,
and places review instructions before explicitly bounded document data. The current
review prompt appends rules after document text; some model rationales explicitly exclude
that appended material. Broader subjects/forms and fresh control pairs still need review
before bulk generation. Do not resume the remaining v2 batches by default. Compatible v2
resume exists technically; changed source/prompts require a new ID.

The prepared source-bank target remains 18,000 ethical + 9,000 fresh aesthetic control
documents, across 99 briefs and 2,808 batches. Only ten of 27,000 candidates exist.
All-positive/all-negative/complementary mixed assignments are preserved. All 100 frozen
beliefs remain future eval targets; ten off-topic eval beliefs are untrained probes.
Final dose/token-step matching, treatment analysis/falsifiers and training are still future
work. Pinned C4 source-pool target: 18,000 full unique records, not a matched training dose.
Separate private corpus store: `sunnybak/sft-drift-ethical-corpus`, pinned by main handoff.
See [pipeline](belief-transfer/STANCE_CORPUS.md) and
[changelog](changelog/2026-10-19-first-live-corpus-batch.md).

## Established pilot and measurement references

The reviewed `ethics_sft_documents_expanded_v1` pilot remains unchanged: 84 documents,
80/84 in 400–600 Qwen tokens, mean 471.5, total 39,603 tokens; 23 provisional agent flags,
12 model flags and substantial reviewer disagreement. Qualifier errors, added premises,
metadata leakage and limited variety motivated v3. New infrastructure is not evidence
that these errors are solved. Earlier failed/partial/complete pilot artifacts survive.
See [prior findings](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_expanded_v1/review_findings.md)
and [prior changelog](changelog/2026-10-19-stance-document-refinement.md).

Frozen bank: `ethical_pilot/ethics_100_bank_v3`, all 161 declared frozen file hashes intact.
Mac MLX BASE: `ethical_pilot/ethics_100_stance_qwen_v2`, 2,400 extracted answers, 32/32
controls; equal-check agreement 87.3%, including 186/1,200 contradictory pairs. Keep all
valid replies. Independent-seed noise and CUDA BASE remain unmeasured; stance drift alone
is not forgetting. GPU calibration, CUDA BASE, memorization/reload checks, fresh controls
and all-100 evaluation precede treatment interpretation. No Mac training or unapproved rental.

## Preservation

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md, then from `belief-transfer/`:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Only orient/wind-up repo skills are active. Full suite: 854 passed, 4 skipped; final focused regressions: 96 passed.
All 161 frozen hashes and the historical shared cache are unchanged. Current corpus API spend: $0.01509735. Test output stays in /tmp until tests finish. Git carries
source/config/notes; main private study snapshot carries frozen data/results/cache and a
pinned pointer to the separate corpus store. The actual source and artifact revisions
are in `belief-transfer/data/.handoff-receipt.json`; prose is not a sync receipt.
Initial v1 preparation was superseded before generation: its source-hash map
used colliding basenames. V1 remains preserved with zero documents/cost; v2 records
all seven source files by module-relative path. Initial implementation: `2851d44`. V2 preparation/source commit: `7542129`. Results contain test logs, verification.json
and the original empty-bank audit. First live batch: `976e9b0`; artifact validation
recounted all ten Qwen lengths, checked draft/final/shard hashes and shared plan lineage.
No functional code changed and no pytest ran during generation; prior engineering tests
remain the 854-pass suite and 96-pass final focused checks. Private remote and portable restore rehearsals passed for the
initial corpus snapshot; final handoff verifies the prepared v2 bytes too. Preserve both
private stores at each subsequent completed boundary; consult the actual receipt.
