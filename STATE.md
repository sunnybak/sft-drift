# Current state — 2026-10-22

## Goal and active process

Goal ACTIVE:resolve measurement errors and genuine SFT regressions before extending
ethical training. Existing VastRTX3090 authorized; no new rental or Mac training.
No full90/100beliefSFT has run. Original10-target/four-arm pilot completed earlier.

RUNNING:supervisor sft-drift-replay-coverage-value-v5, PID123603; GPU source
9066e9170be3c1627e0b3c587d80b1d609a80cba pinned. Training454/454 COMPLETE, all12
engineering checks pass. Final/227/454 and closed training outputs copied/hash-verified
locally:39files/961,687,200bytes(total includes already saved227). Finite worker now
collecting all100beliefs:latest1024/2400recorded. No restart/resume or source pull.
Master ethics_sft_replay_coverage_value_v5; train ethics_sft_c4_replay_coverage_v5.
Command:cd /workspace/sft-drift/belief-transfer && .venv/bin/python -u scripts/run_replay_value_probe.py
Log:/workspace/sft-drift-ops/replay-coverage-value-v5.log

V5fails declared performance gates; NOT a tuned/qualified pipeline. Procedural known
thinking62/63(one4096tokenrepetition loop), short56/57(one new negation error, different
from oldcontrol's uppercase loss). Decisions27/32thinking versusBASE/control32/32;
short20/32overall,15/24BASE-known versuscontrol16/24. All64decision finals exact/normal,
so17wrong values are genuine, not parser misses. Original development32/32passes;
validation31/32butnote-flip1/16fails. Full100continues under unqualified label.
All23assay flags and the one failed validation reply fully read/hash-bound. Entire
4096tokenloop read; it repeats9-4=5without completing reasoning/final. No grade conflicts.

Actual decision training-prefix/target audit192draws/64sources:0mismatches, correct
weights(96short×32,96thinking×1), exactEOS. All64gold request/target pairs fully agent-read,
no clear semantic defect. Generated thinking median293→43.5tokens; goldtargetmedian45.
Shortcut/style transfer is a hypothesis, not proven mechanism. Do not start anotherSFT.
Prospective diagnostic:changelog/2026-10-22-replay-interface-rca-plan.md (2×2 seen/held
facts×wording, fixed3models;576new calls, no retraining). Implement only after current
worker ends and reviewed artifacts are safe. Conditional independent confirmation is
NOT triggered becausev5failed; do not use it to rescue this candidate.

Exact next monitor:
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-replay-coverage-value-v5; tail -n 20 /workspace/sft-drift-ops/replay-coverage-value-v5.log'
After TERMINAL+COLLECTION_COMPLETED:copy/hash-verify closed master/full100outputs and
runtime configs, then run locally from belief-transfer:
uv run --no-sync python scripts/analyze_replay_value_probe.py
Analyzer46focused tests pass; no weights/local training. Reconstructs192candidate
assay and all full100/control token/seed/native records, initial adapter/LR/projection.
Full100failures/review/report remain pending. A process/checkpoint does not survive box
destruction; current worker has NO resume support despite saved optimizer state.

## Current scientific comparison

One replay recipe, now trained once; not a parameter sweep:fixed C4/old thinking teacher
chunks and positions, weight32/LR1e-4/LoRA/seed42/454steps/final-only. Adds194gold replay
sources(130short procedural,64decision across modes); retains246old thinking sources.
All194requests independently solved,46full request/target/proof reads,0clear defects.
Manifest47b152a692b2b1101000f4a86bc193394b60c8488bd6af6a593b23273b7bcad6.
3246draws/3625chunks;3043C4/oldthinking chunks unchanged;1248760raw/1322416weighted
loss targets. Coverage/mode allocation/exposure change together, not token-matched.
NewID reuses EXACT prepared but untrained v4manifest/settings; oldtrainv4 never started.

V4reference worker COMPLETE384replies, no technical failures. All384raw token/seed/
runtime/native-grade records reconstruct. All62flagged replies fully agent-read and
hash-bound. Separate value-v2 matches manual choices; native word-only scores unchanged.
BASEvalues32/32thinking,24/32short; fixed C4control32/32thinking,20/32short,16/24
BASE-known short values retained. Genuine wrong choices remain after parsing fixes.
Procedural control63/63thinking,56/57short retained(one new uppercase error).
V4native reference unusable; its failed guard remains, no v4candidate authorized.

Prospective v5amendment uses actual v4reference IDs/raw data and BASE-only value masks;
no new reference calls/redraws, lowered95%retention thresholds or changed ethical
instrument. Requires candidate exact lowercase decision finals plus separate value/
stop/boundary checks. Original qualification unchanged. Worker collects192candidate
assay replies and all100beliefs/2400natural replies even if scientific checks fail.
Full failure review required before adoption. Eight facts/correlated variants/one
training seed are development evidence; a pass still needs independent-input confirmation.
Plan:changelog/2026-10-22-replay-coverage-value-v5-plan.md. Protocol
32e1193e54c86d478890151016735ddad8ac6f5399ee7a3dd845518a83c33f7f;1138bindings
verified both locally/GPU, resolved trainconfiga80a904a8f87. Focused suite107passed.
No automatic expansion, checkpoint selection on stance, or repeat-until-pass.

## Preservation

Latest VERIFIED private snapshotf7aa1f63d2b6df50194266cb2f70d2510de1a962 at7d84a6c:
6626files/19,644,280,742bytes; corpus3699d97c07df3f561ce87bbf24fdb99324d28d16.
Includes checkpoint227, all prepared inputs/ref review/launch/conditional-confirm plan.
New closed training copy(39files/961,687,200bytes), assays/dev/val(82files/4,106,172bytes),
actualprefixaudit192, all64goldreview,23assay+1validation full reviews and newRCAplan
are local offGPU but pending the next private save. Copy receipts under generated
ethical_stance_sft/ethics_sft_replay_coverage_value_v5. Current unfinished full100/raw
worker log still only onGPU; do not copy live append streams. No source pull on GPU.
Save command:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
No local mutations/copies/tests during save; retain handles acrossHF429waits.
Never claim box destruction safe while new results remain only onGPU.

## Established results and data limits

LowerLRtrial ethics_sft_lower_lr_probe_v1 complete/rejected:12engineering/13comparability
passes,51/55short retained vsnorm155/55, original note-flip1/16fails;2400recorded/
2399valid.133flags fully read,2432tokenrecords verified. See2026-10-22-lower-lr-probe-results.
Oldweight32/lowerLR equal aggregate support counts are not reuse:346different final
choices,0byte-identical responses; separate hash-bound identity audit retained.
Originalethicalpilot/target-free-readout/wording/fresh-retention/weight-ablation results
remain in BENCHMARKS.md and dated reviewed reports. CUDA weighted-loss correction is
opt-in and passed all5toychecks; historical defaults unchanged. No prior gate cleared.
Candidate corpusv5 has20000docs/221repairs; conservation quarantined, full-bank semantic
clearance false. Dashboard5180has13historicalreports; no UIchange in this work block.
