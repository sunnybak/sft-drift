# Current state — 2026-10-22

## Goal and active process

Goal ACTIVE:resolve measurement errors and genuine SFT regressions before extending
ethical training. Existing VastRTX3090 authorized; no new rental or Mac training.
No full90/100beliefSFT has run. Original10-target/four-arm pilot completed earlier.

TERMINAL:supervisor sft-drift-replay-coverage-value-v5 EXITED2026-10-22 18:02UTC;
GPU now idle. Training454/454 COMPLETE, all12engineering checks pass. Master
ethics_sft_replay_coverage_value_v5; train ethics_sft_c4_replay_coverage_v5.
All closed training/checkpoints/assays/full100/master/log copied/hash-verified locally.
Full100 ethics_gpu_replay_coverage_unqualified_s42_v5:2400/2400valid, fresh controls32/32.
All2432natural/control runtime records reconstruct,0mismatches,normal stops throughout.

V5 FAILS prospective criteria:procedural62/63known thinking(one4096tokenloop),56/57short;
decisions27/32thinking versusBASE/control32/32,20/32short,15/24BASE-known retained.
All64decision finals exact/normal;17wrong values are genuine. Originaldevelopment32/32;
validation31/32butnote-flip1/16fails. All24flagged assay/validation replies fully read;
no full semantic manual reading of2400natural replies. See reviewed_verdict_v1 artifacts.
Actual192decision training-prefix/targets:0mismatches;all64goldpairs agent-read,0clear
semantic defects. Thinking median293→43.5tokens(gold45):style/shortcut hypothesis only.
Full100support69.79% vsBASE42 63.29%(+6.50pp),oldC4controlbounds67.833–67.875%.
These unqualified descriptive readings do not establish selective editing or clear gates.

PREPARED:ethics_gpu_replay_interface_rca_v1, fixedBASE/control/v5candidate2×2transfer
RCA. 9new typed neutral_decision_retention jobs,576new calls; held/eval192actual replies
reused. No training/newethicalreading/adoptiongate. Inputs4×64rows;192actual training
prefixes/targets/weights reverified, all40source/prepared bindings match. Focused tests
110passed(mocks/tempdirs, includes missing/changed actual metadata and truncation).
Generated/ethical_pilot master protocol and9YAMLs are ready; no RCAcalls/worker yet.
Next:private-save inputs, deploy exact source/inputs/receipt after oldworker terminal,
then finite supervised dispatch. No overwrite/resume/retry-on-content. Conditional
independent confirmation remains NOT triggered; failedv5verdict unchanged.
Exact prepare command(already completed, DO NOT rerun existingID):
cd belief-transfer && uv run --no-sync python scripts/prepare_replay_interface_rca.py
Exact worker command(after verified preservation/deployment):
cd /workspace/sft-drift/belief-transfer && .venv/bin/python -u scripts/run_replay_interface_rca.py
Plan:changelog/2026-10-22-replay-interface-rca-plan.md; implementation notes beside it.

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

Latest VERIFIED private snapshotef853555ffe09e76e69f4b7b5fcbd45ffc0aef73 at5421a9e:
6807files/20,246,079,243bytes; corpusc16c62e0c67488509e93f6c2b26334e375c86a20.
Includes entire closed training/checkpoints, terminal worker log/full100, all reviews,
mechanical/per-belief analyses and final reviewed verdict. No outputs remain only onGPU
or only local. Verified receipt updated after successful same-processHF429retry.
Git final report/source pushed. New RCAinputs/source/configs are local pending next save.
Copy receipts under generated/ethical_stance_sft/ethics_sft_replay_coverage_value_v5.
Save at next completed block:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
No local mutations during save. Worker terminal/GPU idle; no resume/restart.

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
