# Current state — 2026-10-19

## Throughput optimization — current authorized work

The slow full BASE is stopped by user instruction. `sft-drift-reference-v3` is STOPPED;
`ethics_gpu_base_v1` preserves 360/2,400 belief replies plus 32 controls, with STOPPED.md.
It is incomplete and has no restart resume. No replacement full BASE or treatment started.

Preferred path: isolated vLLM0.19.0 /Torch2.10.0 /Transformers4.57.6, existing RTX3090.
Main training environment/pins unchanged; no resources rented. Warm matched short probe:
original eager107 versus vLLM2,908 output tok/s at64 requests. Actual held-out natural
replies: **192 in50.968s, 2,021 tok/s**. Development56/56 and validation224/224 passed,
32/32 known controls each, exact execution metadata checked. All2,432 frozen rendered
inputs match token-for-token across environments. Probability settings, thinking/BF16,
4,096 output cap and frozen instrument unchanged; new per-request RNG requires fresh
same-engine BASE. Provisional full2,400-reply ETA ~12min; budget10–20 until measured.
Native compiled HF short-probe gains did not translate to the actual full cache; keep
experimental. See `belief-transfer/GPU_INFERENCE_SPEED.md`.

Current finite worker: `sft-drift-vllm-finalchecks-v3`. CUDA startup fixed after failed
adapter canaryv1. Canaryv2 loaded/confirmed adapter without backend errors but hit its
short256-token probe cap. Both failures retained. Fresh canaryv3 passed all four checks with study4,096 cap. The worker now runs
capacityv2 (64×4,096 forced output tokens, 256input, LoRA support enabled).
Capacityv1 never started because canaryv1 failed; its blocked log is retained. No full
BASE is launched by this worker. New BASE config `ethics_gpu_vllm_base_v1` remains unused.
Latest code-focused checks40 passed; full regression **979 passed, five skipped**.

Exact next command from the Mac:

```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-vllm-finalchecks-v3; tail -n 12 /workspace/sft-drift-ops/vllm_finalchecks_v3.log'
```

Next: verify adapter/capacity results, copy completed GPU artifacts to the Mac, commit/
push notes and save the private snapshot. Only the Mac writes private snapshots.
Prior verified snapshot covers code2201ae1 and stoppedBASE/native probes; later vLLM
results are not yet privately backed up. Environment/model binaries stay on the GPU.

## Active experiment preparation

User authorized beginning the experiment sequence. Calibration completed. Batch sixteen
failed the full-capacity test; fresh `ethics_gpu_capacity_v3` passed eight 4,096-token
outputs (823 input tokens), peak allocated 13,951,462,400 bytes. Technical document
smoke v2 completed two optimizer steps with finite loss, changed adapter, unchanged
base and saved checkpoints, but failed reload verification (max logit error .375).
Its failed artifacts/checkpoints are retained. Accelerate's training autocast wrapper
was removed before the inference comparison in fresh smoke v3: **passed**, all eight
checks true, exact adapter roundtrip and zero reload logit error. Same initial adapter,
input and training settings; CUDA updates differ slightly between runs (not bitwise
reproducible training). Both v3 optimizer checkpoints and final adapter are saved.
Original HF development (56/56) and held-out validation (224/224) both passed32/32
known controls. Original full BASE is stopped and partial; throughput replacement and
current process state are above. See `changelog/2026-10-19-gpu-experiment-start.md`.
Sampling reference seeds42,7,1729 were declared in `belief-transfer/GPU_BASE_PROTOCOL.md`.
No ethical support outcome was used to select inference settings. Scope adjudication,
semantic memorization test and frozen treatment plan remain pending.

Standalone `document_sft` is now implemented, with explicit loss labels, per-document
continuation, actual training-token journals and CUDA update/reload checks. Corrected live smoke v3
passed on CUDA (reload error zero, exact adapter roundtrip). The v1 input preparation used abbreviated source-file hashes; preserve
it as a void preparation, never trained. v2 records and verifies full SHA-256 hashes.
See `belief-transfer/DOCUMENT_SFT.md`. Focused checks: 161 passed, then 92 passed after
provenance changes. Full regression after preserving historical unset-field serialization:
**971 passed, five skipped**. Historical fingerprint `8834d5aca78e` remains unchanged.
All 2,432 rendered BASE/control inputs are 80–186 tokens; stress width is 823.

The original driver PID 4240 was held only at its stage boundary during the schema
compatibility fix; its capacity child continued, then failed. The driver was released
and exited under `set -e`. No paused process remains. Failed v2 retains its request,
full traceback and `FAILED.md`; do not restart it or reuse its measurement ID.

Separate scope adjudication v1 read eight pending full documents across four risk
families: seven no-clear-serious-defect judgments, one necessity/distress scope error.
Repair overlay `ethics_sft_decision_repairs_v6` preserves the full revision (465 tokens),
not yet applied to a complete candidate bank or model-rechecked. Original queue stays
unchanged; explicit reconciliation leaves 1,098 unreviewed entries. No clearance claim.

## Completed — SSH-controlled Vast.ai setup

Existing box `38.49.42.46:58689`, RTX 3090 / 24,576 MiB, ephemeral workspace.
Codex stays in the local chat; no remote agent harness. Checkout:
`/workspace/sft-drift`, environment in `belief-transfer/.venv`.
Setup worker `sft-drift-setup` exited successfully; run `ethics_gpu_setup_v1`.
Locked install completed; both private stores restored and verified; **99 setup
regressions passed**. Qwen3-4B is cached at revision
`1cfa9a7208912126459214e8b04321603b3df60c`. CUDA 12.8 / BF16 canary passed:
all parameters on GPU, response `READY`, peak allocated 8,057,951,744 bytes.
Setup-stage status only: later calibration and technical training are recorded above.

Exact monitor command from the Mac:

```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-setup; tail -n 30 /workspace/sft-drift-ops/setup_v1.log'
```

Completed artifacts, exact config, canary tokens, full log (including the stopped
initial install), Supervisor definition and hardware evidence were copied back to
the registered results directory on the Mac. Do not restart a completed canary.
Code/notes are pushed and private snapshot success must be checked in
`belief-transfer/data/.handoff-receipt.json`. Environment and model-cache binaries
stay on the box; their versions/revision and setup procedure are preserved.
See `belief-transfer/SSH_GPU_OPERATIONS.md` and
`changelog/2026-10-19-ssh-gpu-setup.md`.

## Next experiment steps — GPU qualification and document SFT

The existing GPU box is ready for CUDA calibration/qualification, BASE and technical smoke
checks. The new `stage=document_sft` now implements standalone text and actual prefix
loss masking; its CUDA smoke/update/reload check passed as v3. Legacy `stage=sft`
remains chat-based. Resolve scope-review dispositions and freeze arm/dose/training/
analysis before treatments.
No rental, rescreen or training was started in the earlier readiness work block;
the currently authorized setup is recorded above.

New handoff: `belief-transfer/VAST_SFT_HANDOFF.md` has verified existing entry points,
implementation requirements and a prompt to paste into the GPU session. SETUP.md's
stale “no dataset yet” paragraph is corrected. Decisions lessons and future changes
are in `belief-transfer/STANCE_DECISION_QA.md`: subject-routed questions, direct scope
predicates, untouched blind audits, separate dispositions, retained refusal/cache/retry
semantics. These recommendations do not change completed rubric v4 or rerun it.

## Pooled Decisions score plots

Saved overall and 13-check histograms under the completed screen's
`score_histograms_v1/` results subdirectory (PNG/SVG, exact bins/statistics, source hash).
All subjects/positions pooled, original screen before repairs, no new API calls.
Composite = maximum of ten serious checks; 19,995 complete rows, five refusals excluded.
Median .01, p95 .08; 428 at least .2 and 134 at least .7. Logarithmic count axes.
Individual criteria retain available valid scores. These are model judgments, not
calibrated defect probabilities. The next GPU handoff and readiness status above remain.

## Completed work: full Decisions screen and bounded manual repairs

User authorized screening all 20,000 synthetic documents and manual corrections.
**`ethics_sft_decision_qa_corpus_v3` completed 20,000/20,000** with frozen rubric v4,
13 questions, gpt-6-luna. No active generation/training process or GPU rental.
Actual returned-usage cost: **$7.6719303** full pass; **$7.8335481** including development
and 52 repair rechecks. Zero HTTP request errors/failed rows; uncertain cost zero.
Five refused questions remain explicit in raw results, with separate full-text agent reviews.

The agent read **242 unique full source documents**, including the prior 164, a fresh
flag-blind 20, all **34 high stance/contradiction flags**, targeted scope examples and
all five refused-question documents. Also read all 52 complete revisions. This is NOT
manual review of all 20,000. All 34 high stance flags have traceable corrections.

New candidate version **`ethics_sft_candidate_repairs_v1`** retains all 20,000 IDs,
100 documents per subject/position, with **52 manual replacements** from
`ethics_sft_decision_repairs_v1`–`v5`. Their model rechecks are separate QA runs with
`decision_qa_repairs_v1`–`v5` in the ID. All replacements are 422–562 Qwen tokens.
Candidate version: **9,802,428 tokens**, 19,600/20,000 within 400–600, no exact duplicate
final texts. Original v5 corpus is unchanged. Later repairs share disclosed scaffolding;
these are corrections, not new independent ideas. No automatic training approval.

Detector limits: development 164 was reused for tuning (12/14 serious labels caught).
The fresh flag-blind 20 found one clear scope change, **missed** by Decisions, one
borderline, 18 without clear serious defects. No retuning on that check. Low flags are
not semantic clearance. Original routes: 134 high, 594 review, 52 style, 19,215 low,
five unresolved; these include 408 original mandatory reviews, not confirmed defects.
Follow-up policy adds both hiring subjects to the two psychology families: 800 risk-family
rows. Disposition queue: **1,106 pending**, 52 repaired, 14 agent-no-clear-serious-defect,
three borderline, five provider-unresolved/agent-reviewed. Do not silently filter this queue.
One repaired psychology document retains a .6 model flag with explicit agent disagreement.

Exact next command, from `belief-transfer/`:

```sh
cat VAST_SFT_HANDOFF.md
```

For the prepared box, read that same file remotely with:

```sh
ssh -p 58689 root@38.49.42.46 'cat /workspace/sft-drift/belief-transfer/VAST_SFT_HANDOFF.md'
```

Follow that handoff for GPU setup; before treatment training prioritize scope adjudication using `disposition_queue.md` in the same folder.
Corpus expansion/training remains a subsequent experiment plan. Qualify CUDA BASE,
variability, tiny memorization/update/reload checks before any SFT. Evaluate all 100
beliefs on every future model/checkpoint. No Mac training or unauthorized rental.

## Bank, baseline and provenance

Original **`ethics_sft_pooled_corpus_v5`**: 20,000 synthetic candidates across 90 ethical
and ten fresh off-topic training claims ×100 per position; 9,800,659 Qwen tokens.
The ten control claims are distinct from the frozen evaluation preferences. C4:
20,634 unique full rows /9,774,947 tokens, pinned revision
`1588ec454efa1a09f29cd18ddd04fe05fc8653a2`, seed 42, shuffle buffer 1,024.
Generation cost $25.89367392 cumulative, including v4 $8.59085765; do not add v4 again.
Historical failed-attempt uncertainty $0.08217 remains separate from this QA's zero.
Original stopped v4 and completed v5 lineage remain preserved.

Verified **2,101 source files and 161 frozen instrument files unchanged** after screening.
Frozen bank: `ethical_pilot/ethics_100_bank_v3`. Mac MLX BASE
`ethics_100_stance_qwen_v2`: 2,400 replies, 32/32 controls, 87.3% equal-check agreement,
186/1,200 contradictory pairs. No complete CUDA BASE or treatment adapter yet; technical smoke adapters only.

Decisions support is opt-in; original Responses pricing/cache identity and retry defaults
remain intact. New QA uses durable per-request journals, bounded transient retries,
explicit resume and completed-run overwrite refusal. All live runs are finished.
Validation: full suite **938 passed/five skipped** before production, final targeted
**56 passed/one skipped**, including three candidate-assembly lineage/refusal tests.
Tests ran separately from live stages and artifact writes.

## Preservation and fresh-box entry

Code/configs/notes belong in Git; exact requests, raw responses, authored edits, before/after
texts, complete candidate version and queues are declared in the main private store and
separate private corpus store. Check the final commit/revisions and success in ignored
`belief-transfer/data/.handoff-receipt.json`; Git notes are not a snapshot receipt.
Final work-block procedure: commit/push, then from `belief-transfer/`:

```sh
uv run --no-sync python scripts/handoff.py save
```

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md, then:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Details: `changelog/2026-10-19-decisions-qa.md`, `belief-transfer/STANCE_DECISION_QA.md`,
and the full review report above. Do not rerun completed screening/repair IDs.
