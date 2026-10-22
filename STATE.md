# Current state — 2026-10-22

## Goal and active process

Goal ACTIVE:resolve measurement errors and genuine SFT regressions before extending
ethical training. Existing VastRTX3090 authorized; no new rental or Mac training.
No full90/100beliefSFT has run. Original10-target/four-arm pilot completed earlier.

RUNNING:supervisor sft-drift-replay-coverage-value-v5, PID123603, source9066e9170be3c1627e0b3c587d80b1d609a80cba
pinned on GPU. Master ethics_sft_replay_coverage_value_v5; train
ethics_sft_c4_replay_coverage_v5. Reference reconstruction passed; RUN train observed.
Command:cd /workspace/sft-drift/belief-transfer && .venv/bin/python -u scripts/run_replay_value_probe.py
Log:/workspace/sft-drift-ops/replay-coverage-value-v5.log
Supervisor autostart/autorestart false; finite worker, NO resume/overwrite by startedID.
At launch no saved checkpoint yet. Current launch observation/closed log excerpt:
data/generated/ethical_stance_sft/ethics_sft_replay_coverage_value_v5/deployment_and_launch_v1.json
Do not pull source into the running GPU checkout or change bound files.

Exact next monitor:
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-replay-coverage-value-v5; tail -n 20 /workspace/sft-drift-ops/replay-coverage-value-v5.log'
Poll the existing process, not restart. Copy/hash-verify completed checkpoint227/final
and closed outputs at safe boundaries. Local artifact snapshots do not save live GPU
outputs automatically. A process/checkpoint on this box does not survive destruction.

## Current scientific comparison

One untrained replay recipe, NOT a parameter sweep:fixed C4/old thinking teacher
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

VERIFIED private inputs/review snapshot3de13bea83d29bab93ec41458da95649aeb09575 at9066e91:
6614files/19,247,343,882bytes. Corpus8435cf0ad95514c56b8e3679716161bb6ca4bce0;
manifest56d14ee81efeb7fcf3a7229ae3a6c8a7caced7fd3bc260a2c2e79c001d27fa49.
Covers all v4raw refs,62review,384audit,value-v2derivations,v5inputs/code/plan.
Verified receipt deployed toGPU before start; prior receipt backed up off-repo.
139data files/31,387,108bytes verified at deployment,25new copied without overwrites.
New launch receipt/these notes require completed-block save; live train outputs only
onGPU until copied. Source adoption preserved identical old runtimeYAML in
/workspace/sft-drift-ops/preserved-runtime-configs/before-replay-value-v5/.
Save command:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
No local mutations/copies/tests during save; retain handles acrossHF429waits.
Never claim box destruction safe while new checkpoints/results remain only onGPU.

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
