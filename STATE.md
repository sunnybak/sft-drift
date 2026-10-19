# Current state — 2026-10-19

## Where we are

**Active: matched refinement reviewed; authorized 84-document expansion is next.**
`ethical_stance_sft/ethics_sft_documents_pilot_v3` completed 48 drafts, single revisions,
and assessments; every final document was read and annotated. All 48 are directional;
all photography controls avoid nonvisual/task metadata. Length regressed: 45/48 drafts
in range, only 37/48 finals (340–559 tokens, mean 436.4). Cost $0.055754. Nineteen
provisional agent flags include 11 lengths and eight semantic/argument concerns.
Same-model reviewer flags one and misses those eight semantic/argument concerns;
passing four diagnostic snippets does not validate it. No training/checkpoint exists.

V2 failed before drafting: four ideas instead of two, cost $0.003426, fully preserved.
V3 bounds idea cardinality in its schema and adds full context to calibration snippets.
Earlier v1 (48 docs) and chat-pair pilot (32 answers) remain unchanged.

Next run: `ethics_sft_documents_expanded_v1`, 84 candidates for six ethical subjects
across five domains plus the same photography control. New subjects: paid kidney
donation, medical-data use without consent, cash bail based on inability to pay.
Enable length-preserving revision: leave sound in-range drafts verbatim; use measured
word/token editing estimates when edits are needed. Same single-call limit, frozen
instrument and six C4 rows. Other prompts/plans stay fixed; original 48 source drafts
can be reused from cache, so this is a breadth test and revision-policy comparison,
not independent replication. Expanded ceiling $0.50; combined new spend remains <$1.

[Protocol](belief-transfer/STANCE_DOCUMENT_PILOT.md) and matched [findings](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_pilot_v3/review_findings.md).
[Matched synthesis](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_pilot_v3/iteration_notes.md).
Read every expanded final revision before declaring this work complete. No accepted
training corpus, training schedule or GPU rental is in scope.

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
uv run --no-sync python run.py +run=ethics_sft_documents_expanded_v1
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
