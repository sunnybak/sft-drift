# Current state — 2026-10-19

## Where we are

**Active: authorized prompt refinement, matched repeat, then broader document pilot.**
Registered fresh IDs `ethical_stance_sft/ethics_sft_documents_pilot_v2` (48 documents)
and `ethical_stance_sft/ethics_sft_documents_expanded_v1` (84 documents). Both use
versioned v2 prompts, GPT-6 Luna, the existing 400–600-token target, one revision and
same six C4 records. Each has a $0.50 ceiling. V2 failed in planning before drafts ($0.003426): duplicate idea count.
Fresh v3 is registered with bounded idea schema and contextual calibration snippets;
v3 ceiling $0.49 keeps combined new ceilings/spend below $1. Generation is stopped.
Review every v2 revision before the expanded run. No training/GPU rental is in scope.
The completed v1 remains unchanged; its results and limitations follow.

Read [protocol](belief-transfer/STANCE_DOCUMENT_PILOT.md),
[findings](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_pilot_v1/review_findings.md),
and [all pairs](belief-transfer/data/generated/ethical_stance_sft/ethics_sft_documents_pilot_v1/review.md).
The new pipeline is distinct from the earlier 32-answer chat-pair pilot, which is unchanged.

- Three ethical subjects plus a separate photography preference control; three forms,
  two shared ideas per form, separately generated opposing positions. All 48 are clearly
  directional in provisional current-agent review; this is not evidence of a trained belief.
- Requested 400–600 Qwen tokens; 43/48 meet it. Final range 301–597, mean 475.0;
  22,802 synthetic tokens. Revision moved eight drafts into range and four out of range.
- Current-agent review flags 17 documents for edits, including five length failures,
  subtle scope additions, control metacommentary and repetition. Same-model review flags
  22, with both over-literal objections and missed problems. Neither is human ground truth.
- Six full pinned English C4 records are saved and reused in all eight mixture previews.
  1:1 document count is only 20.1–23.5% C4 tokens here because the sample totals 792 tokens.
  No token-dose matching, training-loss implementation or training-ready corpus export.
- Canary + 160 pipeline calls cost $0.045876, under the $1 ceiling; no uncertain charges.
  Raw responses, prompts, critiques, failures, seeds, revisions and provenance survive.

The next small pilot should resolve contradictory non-advocacy planning instructions,
test-specific scope qualifiers, allowed ordinary implications in the quality rubric,
control metacommentary and the length/concision conflict. The user reviewed the proposed changes and authorized fresh runs on 2026-10-19. No corpus size, final design, training dose/schedule or replication
budget is frozen. All 100 evaluation beliefs remain required for every future fine-tune.

## Established baseline

- Model: Qwen/Qwen3-4B, no experimental SFT adapter; MLX on Mac.
- Frozen bank: `ethical_pilot/ethics_100_bank_v3`; 100 scoped claims, 90 ethical / 10
  off-topic, six wordings each. All 600 wording audits and 904 semantic references pass,
  with provisional agent labels and development-reused references.
- BASE result: `ethical_pilot/ethics_100_stance_qwen_v2`; all 2,400 natural answers
  extracted, 32/32 known-answer controls correct, no irrelevant-note flips.
- 45/100 beliefs agree perfectly across all three tested checks. Mean order agreement
  89.0%, wording 88.5%, negation 84.5%; descriptive equal-check Stance Agreement 87.3%.
  All 100 remain in analysis, including 186/1,200 contradictory claim/negation pairs.
- Reasoning enabled; final endorse/reject; temperature .6, top_p .95, top_k 20, min_p 0,
  seed 42, 4,096-token cap, MLX batch up to 64. Independent-seed noise is not measured.
- No causal SFT or catastrophic-forgetting finding. Conviction is retired.

Full methods, results, figures, definitions and caveats:
[baseline report](belief-transfer/ETHICAL_STANCE_BASELINE.md).
[Source ledger](belief-transfer/ETHICAL_STANCE_BASELINE.sources.json) hashes its evidence.
The active artifact profile includes the source bank/audits, eight-topic validation bank,
cap development/validation, BASE v2, failed-cap v1 and generation cache.

## Failures and limits to carry forward

- `ethics_100_stance_qwen_v1`: two clipped answers at 2,048 tokens; coverage qualification
  failed. V2 finished them at 4,096 and reproduced the other 2,398 completed replies.
  The failed result remains failed and preserved, not overwritten.
- `ethics_100_bank_v1` reference accuracy was withdrawn for a reference-construction
  defect; use frozen v3. Older Conviction and Stance development results are historical.
- MLX validity does not qualify CUDA or a fine-tuned adapter. Use fresh matching GPU
  development → validation → BASE runs; no cross-backend paired treatment claims.
- Natural agreement is an outcome, not an inclusion gate; frequency is not confidence.
- Existing measurement stages reject an already-started measurement ID; checkpoint-sweep
  resume is not implemented. Inspect partial outputs before deciding how to continue.

## Exact continuation on a new box

Follow root SETUP.md. From `belief-transfer/`:

```bash
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Then inspect the completed standalone-document pilot; **do not rerun its started ID**.
Exact next command from `belief-transfer/`:

```bash
uv run --no-sync python run.py +run=ethics_sft_documents_pilot_v3
```

The full paired review is under the corresponding generated/ directory. Compare
`revision_examples.md`, `agent_review.md` and `review_comparison.md` in results/ with the
user. Use a fresh registered ID for any changed prompts. This stage saves completed
artifacts but does not automatically resume or overwrite started candidate directories.
Log: `data/results/ethical_stance_sft/ethics_sft_documents_pilot_v1/generation.log`.
Details: `changelog/2026-10-19-stance-document-pilot.md`.

GPU qualification and first BASE overlays are prepared, **unexecuted**:
`ethics_gpu_development_v1` → `ethics_gpu_validation_v1` → `ethics_gpu_base_v1`.
All use batch 1 initially. Calibrate the GPU; keep settings consistent across the chain
and inspect each report before proceeding. Training additionally needs memorization and
checkpoint-reload checks. Save the machine profile alongside GPU result provenance.

## Preservation and history

The current bootstrap is root SETUP.md; paste its final prompt into the next chat.
Only `orient` and `wind-up` remain active repository skills. Previous instructions,
hypotheses, notes, changelogs and 65 one-off scripts are in
[archive/session-reset-2026-10-17](archive/session-reset-2026-10-17/README.md).
Historical core modules/configs remain for imports/tests/inheritance; consult
`belief-transfer/configs/ACTIVE.md` rather than their old queues.

Code/config/progress travel through Git. Current artifacts travel through
`configs/handoff.json` to **private** `sunnybak/sft-drift-ethical-stance`.
The legacy `sunnybak/sft-drift` dataset is public; never use it as the new destination.
`handoff.py save` verifies clean/pushed source, required/frozen hashes, declared output
paths, private storage, uploaded bytes and a pinned manifest. It includes new study
checkpoints and cache; restore never overwrites conflicting local files. A local ignored
receipt and the remote manifest record the actual code commit/artifact revision.
Check that receipt to establish sync status; text in this file is not a sync receipt.
Update this page and a dated changelog, push Git, then save/verify at each completed block.

## Initial handoff verification completed

Source and the initial private snapshot were pushed successfully. A clean Git clone
restored all **162 files (about 98.4 MB)**, verified every frozen/snapshot hash, replayed
all 100 Stance scores and model controls exactly, and matched every baseline-report
evidence hash. Sixty-nine focused tests also passed inside that restored clone.
The full source test suite passed **820 tests, 1 skipped**.
The final save receipt records the current source commit and artifact revision.
CUDA installation/inference/training remain to be qualified on the actual Vast.ai box.

## Latest work-block verification

The full source suite passed **831 tests, 4 skipped** after generation ended. Study cache
bytes were unchanged across that suite. Three provider smoke tests now require explicit
`--run-api`; per-test shared caches are isolated. The first regression invocation made
three legacy smoke calls before this safeguard was added. Their append records are
preserved in the run's `legacy_test_cache_appendix.jsonl`/`.md`; the earlier verified
cache prefix was restored exactly before pilot generation. Additional smoke cost was
about $0.0000258. No frozen instrument evidence changed.

Generation source: `a74d1ea`; later changes suppress HTTP INFO logs containing temporary
signed transport URLs and finish the opt-in test safeguard. Completed log URL queries
were redacted; document prompts and replies are unchanged. The latest private handoff
receipt establishes the final source commit/artifact revision. New pilot outputs, reviews,
C4 text and cache are explicitly covered by the inventory.
