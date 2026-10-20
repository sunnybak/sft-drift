# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns content, transfers it to chat and preserves frozen
controls before ethical training. Broader goal remains the pooled six-arm ethical
study and all100belief before/after maps. **No ethical treatment has been trained.**
Current evidence/plan: `changelog/2026-10-20-request-sensitive-recall.md`.

## Current technical block

Finite format/LR matrix `ethics_sft_registry_format_matrix_v1` COMPLETED; no accepted
variant. All3new runs passed11engineering checks, exact1,864,795loss targets.

| Variant | Strict lookup | Controls | Control format | Null flips |
| --- | ---: | ---: | ---: | ---: |
| assistant/high1e-4 | 0/20 | 21/32 | 32/32 | 1/16 |
| raw/low2e-5 | 0/20 | 31/32 | 32/32 | 1/16 |
| assistant/low2e-5 | 0/20 | 32/32 | 32/32 | 0/16 |

Directly supervised disjoint chat canary PASSED20/20, BASE0/20, all9checks. Separate
`ethics_gpu_registry_format_sanity_v1`: all40replies read. High adapter retrieves
4/4facts from unprefilled document requests,4/4tagged,4/4seen and4/4unseen prose
prefixes, but0/4original questions. BASE0/20. This establishes conditional recall on
four facts, not broad retrieval or qualification. `ethics_gpu_registry_transfer_development_v1`:
all192replies read; BASE/all3adapters each0/20under both128token lookup families,
8/8direct arithmetic; no truncation. Wrong codes, not a formatting-only failure.
Both have full-reply agent reviews JSONL+MD. Frozen instrument/old failures unchanged.

**COMPLETED, FAILED:** one follow-up `ethics_sft_registry_varied_requests_v1`.
Same2,000synthetic+2,000C4bodies, lowerLR2e-5, same1,864,795targets,4,390chunks,
550steps, checkpoints275/550; only synthetic training requests vary across10templates.
New prospective development check requires18/20semantic recall per family plus
unchanged frozen controls. Original strict endpoint retained separately. Reused
20facts are development references, not independent confirmation. No ethical dispatch.
PlanSHA4600aa89f5532073b767ed19f83ca0e81b0b59f4fb8e2556a3d5ebe8ef3d1166.
43focused tests passed; cached CPU-tokenizer preparation passed. No Mac training.

Supervisor `sft-drift-registry-varied-requests-v1` EXITED. All11engineering checks
passed, but original and both longer semantic lookups0/20. Frozen controls25/32:
25valid/correct,7extraction failures, null0/9eligible (incomplete16expected). Direct
arithmetic8/8semantic,7/8exact numeral-only. All96semantic replies,40strict lookup
replies and7failed controls read completely. Failures:4bare `<think>` replies,
2duplicate closes (one ends with wrong reject),1prose final. Original failed verdicts
and prospective failure preserved. Agent review JSONL+MD saved. All63terminal files/
971,363,024bytes copied Mac and SHA/bytes verified, including prior midpoint8files.

No training queued. Fresh inference-only diagnostics prepared and registered:
- `ethics_gpu_registry_conditioning_v1`: all20facts, lookup/reference-note context
  crossed with four-digit/registry answer prefix, plus unprefilled notes; BASE and
  assistant/low +varied-request final adapters,300replies. No prefix includes a code.
- `ethics_gpu_registry_nonthinking_controls_v1`: unchanged32control prompts/seeds,
  BASE andthose2adapters,96replies; samevLLM sampling/limits, thinking disabled.
  New mode diagnostic only; frozen thinking instrument/results are not replaced.
43focused diagnostic/probe/import/handoff tests passed; preparation uses cached CPU
tokenizer only. RUNNING finite Supervisor `sft-drift-registry-conditioning-diagnostics-v1`,
PID32298,source7acf984; log `/workspace/sft-drift-ops/registry_conditioning_diagnostics_v1.log`.
Next: review completed diagnostic replies/controls, copy/hash terminal artifacts,
then preserve. No ethical outcomes or further training sweep.

GPU RTX3090: `38.49.42.46:58689`, project `/workspace/sft-drift/belief-transfer`.
Qwen3-4B revision1cfa9a7208912126459214e8b04321603b3df60c. Training main.venv and
isolatedvLLM env unchanged. Shared lock `/tmp/sft-drift-cuda-benchmark.lock`.
No additional rental. Read `/etc/vast-agents-guide.md` on a new connection/context.

## Reference and prior evidence

CUDA/vLLM BASE seeds42,7,1729 complete:100beliefs/2,400valid replies/32controls each,
no errors/truncation. ~11.45min/full eval. Within-belief3seed range median4.17pp,
p9516.67pp,max29.17pp, descriptive only. MLX separate; old HF BASE stopped360/2400,
not resumable/mergeable. Source/details in prior dated notes and saved artifacts.

Old raw/high neutral calibration `ethics_sft_registry_mixed_calibration_v1` passed10
engineering checks, but strict recall0/20, controls22/32, strict24/32; eight premature
thinking-end failures. Native adapter seen/unseen-prefix recall20/20each, BASE0.
Memoryv1/v2/v3 strict0/20,0/20,1/20; recognition/parity original gates failed and stay
failed. These and current failures are not automatically forgetting. See
`changelog/2026-10-20-assistant-document-calibration.md` and
`changelog/2026-10-20-sft-pipeline-review.md` for detailed prior rationale/receipts.

## Dataset and ethical study remaining

Original pooledv5:20,000synthetics=(90ethical+10fresh training controls)×100×2;
20,634pinned C4 rows, revision1588ec454efa1a09f29cd18ddd04fe05fc8653a2,seed42/buffer1024.
Ten frozen off-topic evaluation preferences remain untrained. Candidatev3 retains
all20kIDs/189replacements/9,802,700tokens, SHA
4b494add47a2edd3df58261b0f66022b69bf6f0cf745b9682ddb57a6b8f15a09.

Decisions screening immutable; low flags missed scope defects. Frozen96text full-read
confirmation found4clear errors; v11has10reviewed corrections/clarifications; v12has18
additional reviewed replacements. Neither overlay assembled into a final candidate.
Remaining finite conservation closure:115candidates,18read (12clear,6no-clear),97
unreviewed. Finish targeted disposition and explicit data-use policy. No full-bank
semantic clearance/human-review claim. Details and exact ledgers under confirmation
root; prior dated notes retain counts/failed calls/review lineage. Do not keep drawing
blind samples until a pass. Preserve all original rows/versions; no purge.

Before ethical treatments: qualify training; finish finite review/policy; assemble
candidate once; measure/freeze exact dose/settings/seeds/checkpoints/hypotheses/
falsifier/contrasts/analysis. Proposed4ethical arms9,000synthetics+same9,000C4;
off-topic10fresh×100selected-position texts repeated to match measured exposure;
C4-only replacement from11,634reserve rows. Exact compiler totals not run/frozen.
Proposed training seeds42/7, midpoint/final designated evaluations require their own
fresh controls and all100belief measurements. No tuning on ethical outcomes; no
forgetting claim without separate retention tasks.

## Preservation

All current training/checkpoints/validations and completed diagnostics copied Mac
with exact SHA/bytes receipts. Latest verified private snapshot
0a1a5a10b25058fc6e8e860c963b58210116511b,code00094cb,
2,380files/8,470,824,917bytes, live and offline verified; includes midpoint275.
Full varied-request terminal outputs/reviews and new inference diagnostic inputs
require this block's next snapshot. No model process remains active before the new
inference worker is dispatched; no new training authorized by diagnostic output.
Authoritative receipt `belief-transfer/data/.handoff-receipt.json`.

Commit/push clean source, then from belief-transfer:
`uv run --no-sync python scripts/handoff.py save` and `... handoff.py verify`.
No source/artifact writes during save, no real-result writes during tests. Snapshot
bytes do not make stages resumable. Do not destroy box until newest outputs/code are
verified off-box/private. Only Mac writes private snapshots.
