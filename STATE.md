# Current state — 2026-10-22

## Goal and current boundary

Goal ACTIVE:investigate/resolve genuine SFTregressions before extending ethical training.
Existing VastRTX3090 authorized; no new rental or Mac training. No full90/100beliefSFT
has run. Original10-target/four-arm pilot is historical, not automatically extended.
User instruction2026-10-22:finish/review this fixed trial; if decisive scientific result
is negative, pause the goal, stop further experiments and give findings/recommendation.
Do not start another tuning candidate. Technical collector failure is not a negative result.

Training ethics_sft_c4_base_reasoning_replay_v1 COMPLETED454steps/1964.43seconds,
all12engineering checks pass; initial adapter/fullLRtrace/actualchunks/objective verified.
Original supervisor sft-drift-base-reasoning-replay-v1 PID131244 EXITED20:26UTC after
first128midpoint retention replies completed. Master failure+TERMINAL preserved:
KeyError('fresh_base_reference'), a collector metadata-default bug. Do NOT restart it.
Recovery supervisor sft-drift-base-reasoning-recovery-v1 RUNNING PID132392, observed
20:51:17UTC, preserved-input preflight. GPUcheckout e2b25f62d30a1b949f2b7c8b2ace3c9e002a1110
pinned during new worker; no new training. Original supervisor remains EXITED.
No scientific verdict on this candidate yet; remaining evaluations never started.

## Established current result

Fixed-model2×2RCA ethics_gpu_replay_interface_rca_v1 complete:576new responses plus
192explicitly reused. All768actual token/seed/runtime/adapter/native records reconstruct;
24paired contrasts saved. All160new flagged request/reply pairs fully agent-read and
hash-bound. This is all flags, not all576new replies; historical192retain earlier reviews.
Entire closed master/all9children/log copied locally:219files/10,435,616B(97new beyond
five-child boundary). Initial copy helper mistook SupervisorEXITED status3for failure;
corrected before copying. No measurement restarted/overwritten. No outputs only onGPU.

Thinking correct/32 (BASE/control/v5):seen_train32/32/29; seen_eval32/32/28;
held_train32/32/30; held_eval32/32/27. Short task-value-v3 correct/32:
seen_train26/20/29; seen_eval25/18/31; held_train26/18/22; held_eval24/20/20.
V5thinking regresses even on exact replay; short gains strongest on seen facts.
Visible thinking errors often compute correctly but evaluate inner equality while
ignoring outer negation. Style shortening is a hypothesis, not isolated causal proof.

New opt-in neutral-task-value-v3 corrects4BASEMarkdown terminals uniformly across768;
all160manual choices agree afterward. Native/value-v2/raw outputs and strict format
stay unchanged; no frozen ethical scoring or historical falsifier changed. Tests74pass.
All frozen bank/instrument file hashes unchanged. Full report:
changelog/2026-10-22-replay-interface-rca-results.md.

Earlier v5training ethics_sft_c4_replay_coverage_v5 completed454steps/all12engineering
checks, actual labels/objective/prefixes exact; rejected by procedural loop, decision
value and original validation note-flip failures. Full100unqualified reading2400valid,
32fresh controls correct,2432runtime records verified. See2026-10-22-replay-value-v5-results.
No recipe qualified. No checkpoint/hyperparameter chosen from ethical outcomes.

## Current fixed trial, recovery and exact next work

Prepared BASEreasoning intervention changes32source targets/96draws; other3529chunks
unchanged.3246draws/3625chunks/454steps/settings/seedfixed, longer thinking+28704tokens.
All32targets fully agent-read, one declared compression; source17/29self-corrections
retained. Original plan/teacherdata/confirmationv1VOID/v2corrected inputs preserved.
Independent512questions/model frozen, uncalled. No training/model qualification claimed.

Completed training and all checkpoints now copied/hash-verified locally;33closed files,
27new beyond midpoint. Terminal failed controller + completed128-reply child also copied:
34files/29new, including exact original runtime config. MIDadapter82b0c1ea8bc2550e98585f7e18e9d4684a8661c3c244806248461136dc1c6106;
finaladapter cb50440ec4e907c493986449c428c380cd1a2b6871e5975fff5be4546e0aac5c.
Step454andfinal adapter/config byte-identical; alias explicit, no duplicate measurement.
All actual tokenized chunks and weighted projection match preparation; all454LRsteps
match parent and initial adapter b933f713e6da2a53d2c564379bc62faba52abad39cd71ec7366dc144dbdd804c.
Derived tokenized.md differed after regeneration; incoming view preserved separately,
authoritative JSONL identical. Generated master training_closed_copy_v1.json and
collector_terminal_copy_v1.json bind closed copies. Live job is now terminal, no outputs
remain only onGPU; operational console log is also copied/hash-verified locally.
Do not destroy until private save.

Repair:typed InstructionRetentionSpec restores omittedFalse default. Original measurement
source/gates/weights/decoder/data unchanged.166focused tests pass, including actual typed
manifest serialization, no repeated retention call on reuse, source-change restrictions.
New finite controller ethics_gpu_base_reasoning_recovery_v1 under ethical_pilot, protocol
prepared,1282bindings verified. It never trains; reconstructs/reuses exact completed128
replies and starts only remaining never-started child IDs. Original failed master intact.
Localprelaunch validation reconstructs128actual raw replies with corrected reader;
trainingbinding/all12checks/actualchunks/objective/fullLRtrace all match. No new model calls.
Newgenerated proof_review_selection_v1.json selects16thinking slots per distinct checkpoint
(one/operation/cell, seed20261022), fixed20:15:51UTC before all12decision result IDs existed.
Read all flags plus those slots; verify exact annotation coverage before any reviewed pass.

Repairs/notes pushed e2b25f6, verified private snapshot below. Six recovery input files
copied/hash-verified onGPU; all1282bindings and128raw replies reconstruct there, completed
adapter/training binding exact. Old untracked runtime YAML preserved in ops, tracked
replacement byte-identical. New finite recovery supervisor launched once, RUNNINGPID132392
at20:51:17UTC, input preflight. Exact source e2b25f6 must stay pinned onGPU.
Command:cd /workspace/sft-drift/belief-transfer && .venv/bin/python -u scripts/run_base_reasoning_recovery.py run
Log:/workspace/sft-drift-ops/base-reasoning-recovery-v1.log. NOresume/restart.
Exact next action:SSH -p58689 root@38.49.42.46; supervisorctl status
sft-drift-base-reasoning-recovery-v1 and tail that log. Watch for midpoint/comparison_v1.json
or TERMINAL under data/results/ethical_pilot/ethics_gpu_base_reasoning_recovery_v1.
Copy/hash completed child/point outputs and dynamic runtime YAMLs at next safe boundary;
live new evaluation outputs are only onGPU. Deployment launchreceipt local, to join next
closed measurement snapshot. Finish same midpoint/final/full100grid even if scientific
checks fail; review final-primary result. If negative pause goal and recommend; no more SFT.
If positive, independent confirmation still needs reviewed/private verdict and updated
execution binding to recovery; frozen questions/gates remain unchanged, no automatic call.
Details:changelog/2026-10-22-base-reasoning-collector-recovery-plan.md.

## Preservation

Latest VERIFIED complete training/recovery-input snapshotf4f0600f67f78ec4773f26caff56ded0f58d33f4
at e2b25f62d30a1b949f2b7c8b2ace3c9e002a1110:7209files/21,238,135,872bytes;
corpuscd208bb515636620857e65bd95f4fdd4df9ff31c, manifest
faf0918ad1d358910d9fe1e48fa46c25e3d703d75de4582ee6890075f5a495f3.
Includes all completed training/checkpoints, terminal failed collector128replies/log,
proofsample and recovery contracts. New recovery launchreceipt/post-launch outputs
postdate snapshot; preserve at next safe measurement boundary. Do not destroy box.
Save after closed-copy+source push:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
Keep same process through HF429waits; no local mutation during save; check receipt.

## Other fixed study limits

LowerLRtrial rejected:51/55short retained, original note-flip failure;2432runtimeaudit,
133flags fully read. Equal oldcontrol/lowerLRaggregate counts were not cache reuse:
346different choices/0byte-identical texts; preserved identity audit. Weighted-loss
normalization fix opt-in/passed5toychecks; historical defaults unchanged. Originalethical
pilot+followups complete with qualification/specificity limits in BENCHMARKS.md.
Corpusv5has20000docs/221repairs; conservation quarantined, full-bank semantic clearance
false. Dashboard5180has13historicalreports; no UIchanges in this work block.
