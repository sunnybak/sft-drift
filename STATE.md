# Current state — 2026-10-18

## Where we are

**Next: review the 32 fresh SFT candidate answers before scaling.**
`ethical_stance_sft/ethics_sft_data_pilot_v1` completed: 16 opposite-position pairs,
two short-answer designs, three ethical subjects and a separate photography control.
All answers are 99–123 words. No full frozen statement copies were found; near-copy
review and tokenizer-level dose matching remain open. All candidates and raw judgments
are preserved. No new training-ready corpus, CUDA BASE or fresh fine-tune exists.
No model/training process is in flight; this pilot process exited successfully.

Read [pilot plan](belief-transfer/SFT_DATA_PILOT.md) and
[findings/examples](belief-transfer/data/results/ethical_stance_sft/ethics_sft_data_pilot_v1/review_findings.md).
The same-model judge passed every pair, but current-agent review found explicit verdicts
in reasons-only answers, weak negative signals, scope-strengthening risks and repetitive
contexts. These disagreements remain explicit. Prefer explicit conclusions for the next
small pilot; discuss examples with the user before choosing the design or scaling.
The photography control also needs visible ethics/environment metacommentary removed.

Final data counts, token dose, design, training targets/method/schedule and replication
budget are still open. GPU work still needs an authorized Vast.ai machine and its own
qualification chain. All 100 beliefs remain required on every future fine-tune.

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

Then inspect the completed v1 examples; **do not rerun its started ID**. Exact next
command from `belief-transfer/`:

```bash
cat data/results/ethical_stance_sft/ethics_sft_data_pilot_v1/review_findings.md
```

Review `data/generated/ethical_stance_sft/ethics_sft_data_pilot_v1/review.md` with the
user, then register a fresh v2 run ID if revising generation. V1 is example review only,
not an approved corpus; the stage preserves completed pairs but has no automatic resume.
Log: `data/results/ethical_stance_sft/ethics_sft_data_pilot_v1/generation.log`.
No training checkpoints were created. Detailed findings: `changelog/2026-10-18-sft-data-pilot.md`.

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

Pilot/config/registry/dependency tests: 35 passed. Handoff/data-sync/stance checks:
77 passed sequentially after generation. A first concurrent invocation passed its tests
but tripped the real-results guard on the live generator log; no test failure was hidden.
Pilot raw requests/replies, candidate chat pairs, automated and current-agent reviews,
resolved config and cache are declared in the private artifact inventory. Check the latest
handoff receipt for source commit and artifact revision; v1's result pins its generation
code revision `a6a7bd3`. No full source-suite rerun was needed for this bounded addition.
