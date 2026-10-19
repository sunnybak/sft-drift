# Current state — 2026-10-19

## Scope correction checked; authoritative-length matched repeat next

User authorized tightening scope rules, a small multi-belief test, and the final corpus
math/mix **before bulk generation**. Prompt v4 separates neutral planning from stance
writing, guards channel/quantifier/predicate scope at every phase, omits internal IDs
from briefs, and puts reviewer instructions before explicitly bounded JSON document data.
Historical prompt files and completed v2 documents remain unchanged.

Fresh pilot: `ethical_stance_sft/ethics_sft_scope_check_v1` — four ethical subjects
(AI hiring, animal medical research, kidney donation, medical-data consent) plus one fresh
aesthetic control, three forms × one shared idea × two positions = 30 candidates.
V4 check completed: 30 documents / 111 successful calls, cost $0.04209835, no uncertainty.
All six hiring documents preserve the channel-specific limit in current-agent review.
V4 length fell from 27/30 valid drafts to 24/30 revisions because the model replaced
measured counts with guessed lengths. All originals remain preserved.

Prompt v5 changes only revision instructions to give an explicit authoritative measured
status; planning/draft/review requests remain identical. `ethics_sft_scope_check_v2`
will replay the same plans/drafts from the v1 cache and make new revision calls. Cache
seeding imports no request rows or charges and cannot overwrite a started journal.
Budget $0.50; concurrency two. Full generation remains unstarted. New production config
`ethics_sft_pooled_corpus_v3` uses v5, with the same 27,000 synthetic candidate target.
C4 can now extend beyond 18,000 records until its replacement reserve reaches 5.4M
Qwen tokens beyond the first shared 9,000 rows. No real C4 is acquired in this check.

Full engineering regression after the matched-repeat/cache-seeding change: **878 passed,
4 skipped** (107.51 s). Earlier scope/reserve suite: 866 passed, 4 skipped. No pytest/live generation overlap.
Next commands from `belief-transfer/`, after committing/pushing source:

```sh
uv run --no-sync python run.py +run=ethics_sft_scope_check_v2
uv run --no-sync python scripts/seed_corpus_cache.py --source-run ethics_sft_scope_check_v1 --target-run ethics_sft_scope_check_v2
uv run --no-sync python run.py +run=ethics_sft_scope_check_v2 stance_corpus.operation=generate stance_corpus.resume=true
```

Read all thirty revised documents before interpreting the check. Review the proposed
[full bank/mix](belief-transfer/POOLED_DATASET_PLAN.md); add the measured generation-token
forecast after the pilot. No bulk generation or training follows without the user's next
instruction. No GPU rental/training is authorized.

Previous v2 check: ten documents, all 412–587 Qwen tokens, cost $0.01509735; nine provisional
scope concerns (one borderline), only one flagged by Luna. All ten retained. See
[v2 review](belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/first_batch_review.md)
and [history](changelog/2026-10-19-first-live-corpus-batch.md). Changed source means new
runs; do not resume historical v2 under current source or overwrite its contract.

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
