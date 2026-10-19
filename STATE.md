# Current state — 2026-10-19

## Completed work and next step

**The authorized refinement and expanded document pilot are complete and reviewed.**
No generation process, training process or checkpoint remains active. CUDA BASE and
fresh SFT remain unrun. No GPU rental or training occurred in this block.

Runs under `ethical_stance_sft/`:

| Run | Outcome | API cost |
| --- | --- | ---: |
| `ethics_sft_documents_pilot_v2` | Failed before drafts: two ideas duplicated into four; preserved | $0.003426 |
| `ethics_sft_documents_pilot_v3` | 48 drafts → one revision → assessment; all finals read | $0.055754 |
| `ethics_sft_documents_expanded_v1` | 84 drafts → one revision → assessment; all finals read | $0.079014 |

Total new API cost **$0.138194**, uncertain-cost bound zero. Earlier document v1 and
32-answer chat-pair pilot are unchanged. Started IDs cannot be overwritten or resumed.
Source versions: v2 `c75e5f4`; v3 `0b16ee6`; expanded `7bbfad4`.

Read [protocol](belief-transfer/STANCE_DOCUMENT_PILOT.md),
[expanded findings](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_expanded_v1/review_findings.md),
[iteration synthesis](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_expanded_v1/iteration_notes.md),
and [reviewer disagreements](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_expanded_v1/reviewer_disagreements.md).
Full paired documents and drafts are in the corresponding generated/ run's `review.md`.

- Expansion: six ethical subjects across five domains plus a photography control,
  three forms × two shared ideas × two positions = 84 documents, 14 arm previews.
- All 84 clearly express the assigned position in provisional current-agent review;
  no invented studies, named authorities or quantitative consequences found. This is
  document quality review, not evidence of training effectiveness or human validation.
- Length-preserving revision improves the original 48 slots from 37/48 to 47/48 in
  range using identical source drafts. Expanded total 80/84 in 400–600 Qwen tokens;
  range 369–756, mean 471.5, 39,603 synthetic tokens. 75/84 finals are verbatim drafts.
- Twenty-three candidates carry provisional edit flags, including four length failures.
  Qualifier loss, added assumptions, two task-metadata references, opponent mismatch
  and limited within-subject variety remain. Same-model review flags 12 and gives all
  six passes to 19 agent-flagged candidates (including mechanical checks outside its
  rubric). Neither perspective is calibrated ground truth. Diagnostic fixtures are
  development examples, not held-out reviewer accuracy.
- Same six pinned C4 records (792 tokens) across all 14 previews: six synthetic plus
  six C4 documents per arm. This is a document-count ratio, not token-dose matching;
  background breadth was held fixed. No accepted/training-ready corpus is exported.

**Next: review the expanded findings before another generation experiment or training.**
A focused next prompt test should address symmetric pro/con outline slots, exact
scope qualifiers, ordinary implications versus new case premises, and targeted edits.
Do not expand document count again by default. Final dose/schedule is not frozen.
Exact next command from `belief-transfer/`:

```bash
cat data/results/ethical_stance_sft/ethics_sft_documents_expanded_v1/iteration_notes.md
```

## Established measurement reference

- Frozen bank: `ethical_pilot/ethics_100_bank_v3`; 100 approved claims (90 ethical,
  10 off-topic), six wordings × two polarities × two orders. All frozen hashes intact.
- Mac MLX BASE: `ethical_pilot/ethics_100_stance_qwen_v2`; Qwen3-4B without an adapter;
  all 2,400 answers extracted, 32/32 controls correct, no irrelevant-note flips.
  Reasoning enabled, temperature.6/top_p.95/top_k20/min_p0, seed42, cap4,096, batch≤64.
- Mean order agreement89.0%, wording88.5%, negation84.5%; equal-check agreement87.3%.
  Keep all 100, including186/1,200 contradictory claim/negation pairs. Natural agreement
  is an outcome, not a filtering threshold. Independent-seed noise remains unmeasured.
- This does not qualify CUDA, any adapter, or a forgetting claim. See
  [baseline report](belief-transfer/ETHICAL_STANCE_BASELINE.md) and its source ledger.
- Failed BASE v1 had two clipped answers at2,048; its failure remains explicit. Frozen
  bank v1 reference accuracy was withdrawn; use v3. Conviction remains retired.

GPU overlays are prepared but unexecuted: `ethics_gpu_development_v1` →
`ethics_gpu_validation_v1` → `ethics_gpu_base_v1`, batch1 initially. Calibration,
CUDA BASE, independent repeats, tiny memorization and reload checks precede training.
Every future fine-tune/checkpoint requires fresh controls and all 100 belief evaluations.
Record treatment hypotheses/falsifiers, contrasts, controls and schedule before effects.
Do not rent a GPU without authorization or train on the Mac.

## Fresh chat or box

Follow root SETUP.md, then GOAL.md → STATE.md → BENCHMARKS.md. From `belief-transfer/`:

```bash
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Only orient/wind-up repository skills are active. `configs/ACTIVE.md` maps current code.
Archive material is opt-in history, not a queue. Tests require explicit --run-api for
live-provider smoke calls; all ordinary tests isolate shared cache and result paths.
Final suite: **835 passed, 4 skipped**, clean exit; cache unchanged and all 161 frozen
hashes intact. The first suite invocation had a preservation-guard failure from the
agent writing its own log/report during tests; that log and the clean rerun survive.
Final verification and source/cache checks are saved in expanded results/verification.json
and tests.log. No tests ran concurrently with live generation.

Code/config/progress travel through Git; declared data/cache/results travel to private
`sunnybak/sft-drift-ethical-stance`. Never use the legacy public dataset destination.
At each completed block: commit/push, then handoff save/verify. The ignored
`belief-transfer/data/.handoff-receipt.json` records the actual source commit and artifact
revision; this prose is not a sync receipt. Failed/partial runs are included. Earlier
snapshots proved fresh-clone restoration and exact baseline replay; latest receipt
establishes current preservation. Details: changelog/2026-10-19-stance-document-refinement.md.
