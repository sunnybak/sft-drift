# Current state — 2026-10-19

## Pooled corpus preparation

The new `stance_corpus` source/configuration is implemented. Manifest preparation and
private snapshot verification follow the source commit. No live generation, C4 acquisition,
training process, GPU rental or checkpoint is active. CUDA BASE/SFT remain unrun.

Run: **`ethical_stance_sft/ethics_sft_pooled_corpus_v1`**. Default operation is prepare-only.
Source bank: 90 ethical subjects × 100 documents × two positions = 18,000 documents;
nine fresh aesthetic controls × 500 × two positions = 9,000 candidate control documents.
Control count is a source-bank choice; final training dose/schedule is not frozen.
All 100 beliefs remain in evaluation, including ten untrained off-topic probes.

- New bounded batch/shard generation, corpus-specific SQLite cache and durable request
  journal, opt-in compatible resume, unknown-charge retry block, lifetime cost ceiling.
- Prompt v3 uses symmetric pro/con reasons, direction-correct objections, fixed-scope
  guards, length-preserving revision and condition evidence. Offline checks pass; live
  prose quality is untested. No automatic training-ready label or failed-row filtering.
- Conditions: all positive, all negative, category-balanced Mixed A and its exact
  complement; fresh off-topic+C4 and C4-only controls; untouched CUDA BASE reference.
  Actual loss-bearing token/step matching and treatment analysis/falsifiers come later.
- Pinned broad C4 streaming is bounded separately. 18,000 unique full background rows
  are planned; none have been acquired for this new run. The six-row pilot sample is
  not the scaled background pool.
- Heavy corpus bytes have separate private bundled storage at
  `sunnybak/sft-drift-ethical-corpus`, pinned by the main study handoff. Portable local
  bundles provide an alternative copy. HF account quota still applies across repos.

Read [pipeline/commands](belief-transfer/STANCE_CORPUS.md) and
[changelog](changelog/2026-10-19-pooled-corpus-preparation.md).
After manifest preparation, the exact next command from `belief-transfer/` is:

```sh
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v1 stance_corpus.operation=generate stance_corpus.resume=true stance_corpus.max_batches=1
uv run --no-sync python scripts/inspect_stance_corpus.py
```

Read the first paired documents before increasing batch count. Prompt/content changes
require a fresh run ID; an identical prepared corpus supports explicit bounded resume.
No full generation run has been launched or promised for this work block.

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

Only orient/wind-up repo skills are active. Current suite: 854 passed, 4 skipped; final
focused regressions follow. Test output stays in /tmp until tests finish. Git carries
source/config/notes; main private study snapshot carries frozen data/results/cache and a
pinned pointer to the separate corpus store. The actual source and artifact revisions
are in `belief-transfer/data/.handoff-receipt.json`; prose is not a sync receipt.
