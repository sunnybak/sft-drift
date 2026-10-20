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

**RUNNING:** one follow-up `ethics_sft_registry_varied_requests_v1`.
Same2,000synthetic+2,000C4bodies, lowerLR2e-5, same1,864,795targets,4,390chunks,
550steps, checkpoints275/550; only synthetic training requests vary across10templates.
New prospective development check requires18/20semantic recall per family plus
unchanged frozen controls. Original strict endpoint retained separately. Reused
20facts are development references, not independent confirmation. No ethical dispatch.
PlanSHA4600aa89f5532073b767ed19f83ca0e81b0b59f4fb8e2556a3d5ebe8ef3d1166.
43focused tests passed; cached CPU-tokenizer preparation passed. No Mac training.

Supervisor `sft-drift-registry-varied-requests-v1`,PID30343, source0a9ed95;
log `/workspace/sft-drift-ops/registry_varied_requests_v1.log`. Registered inputs
transferred; frozen execution hashes checked before training. Exact worker:
`data/generated/ethical_stance_sft/ethics_sft_registry_varied_requests_v1/worker.sh`.
It performs fresh training, original validation/frozen controls, separate semantic
probe, then prospective candidate judgment requiring full-reply agent review.
All prior matrix/probe workers are terminal. No restart-resume or overwrite.
Checkpoint275 saved and copied Mac:8files/396,933,292bytes, all SHA/bytes verified
at20:29Z; receipt in this training result root. Finite copy watcher completed.
Next: preserve midpoint privately, then read terminal original/semantic validation
and every new reply before qualification. Training continues beyond midpoint.
Monitor: `ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-registry-varied-requests-v1; tail -c 1000 /workspace/sft-drift-ops/registry_varied_requests_v1.log'`.


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

All current matrix training/checkpoints/validations and both diagnostics copied Mac
with exact SHA/bytes receipts. First diagnostic40reply review and second192reply
review saved JSONL+MD. Latest verified private snapshote4cc0955a63516a02ceb9cbcd482d4dff46e958a,
codecc6eaeb,2,371files/8,073,889,632bytes, live and offline verified; includes matrix,
both diagnostics/reviews and follow-up inputs. New midpoint275 requires this block's
next save; final outputs still depend on the active GPU process.
Authoritative receipt `belief-transfer/data/.handoff-receipt.json`.

Commit/push clean source, then from belief-transfer:
`uv run --no-sync python scripts/handoff.py save` and `... handoff.py verify`.
No source/artifact writes during save, no real-result writes during tests. Snapshot
bytes do not make stages resumable. Do not destroy box until newest outputs/code are
verified off-box/private. Only Mac writes private snapshots.
