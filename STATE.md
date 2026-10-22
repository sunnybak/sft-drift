# Current state — 2026-10-22

## Goal and current boundary

Goal ACTIVE:investigate/resolve genuine SFTregressions before extending ethical training.
Existing VastRTX3090 authorized; no new rental or Mac training. No full90/100beliefSFT
has run. Original10-target/four-arm pilot is historical, not automatically extended.
GPU now idle. Latest finite worker sft-drift-replay-interface-rca-v1 EXITED18:45UTC,
COLLECTION_COMPLETED+TERMINAL, no technical failure, all9children complete. Do not restart.
GPUcheckout4971dd83a42f5f1a530403a2ba75012986b575fb; no active GPUworker now.

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

## Current preparation and exact next work

CPU-only teacher preparation completed:ethics_sft_base_reasoning_replay_data_v1 and
ethics_sft_c4_base_reasoning_replay_v1 manifest/config; master
ethics_sft_base_reasoning_replay_probe_v1/preparation.json has launch_allowed=false.
All32source targets agent-read;31raw unchanged, declared31compression fully read and
correct. Exactly96thinking draws changed; other3529chunks byte-identical atsameindices.
3246draws/3625chunks/454steps/settings/seedunchanged. Thinking targets+28704tokens,
rawtotal1277464/weighted1351120/input1411998; normalization projected, not token matched.

Independent bank ethics_gpu_base_reasoning_confirmation_v1 is VOID/uncalled:legacy
worked-equation proof.b offset mismatch, sourceproducer preserved atGite6333a2.
Active v2 fixes only proof metadata; all512prompts/labels/seeds/tokenIDs identical to
uncalledv1. All512actual requests independently solved; no overlap/resampling, complete
family/mode/factorial coverage. Two128procedural +four64decision parts reuse existing
stages; maximum1536calls/3models. All67source bindings match; no calls/outcomes.
Confirmation protocol/teacher data_freeze_v1.json retain launch_allowed=false.
94focused preparation/document/loss/handoff/import tests pass. All32final targets reviewed,
including once-compressed31; source17/29self-corrections intentionally retained.

Execution workers now implemented/frozen: scripts/run_base_reasoning_probe.py and
run_base_reasoning_confirmation.py, with execution protocol under the master and
confirmationv2/execution_protocol_v1.json. All1306source bindings and13resolved job
hashes match.156focused tests pass. Actual1152reference responses reconstruct onCPU
(3fixed models ×128procedural+256decisions). No training/model inference added.
54GPUoutput paths registered;12fullsurface configs composed. Prospective execution
amendment requires all100on midpoint227 and final; terminal454aliases final only if
both adapter+config bytes match, otherwise separately measured. Final remains primary.
All scientific failures retain full100readings; technical failures stop/preserve.

Next: finish private save of frozen executable inputs, deploy to existing authorized
GPU, verify source/data/environment/idle state, then launch exactly once:
cd /workspace/sft-drift/belief-transfer && .venv/bin/python -u scripts/run_base_reasoning_probe.py
Finite worker has NOresume/restart. Expected supervisor name:
sft-drift-base-reasoning-replay-v1; log /workspace/sft-drift-ops/base-reasoning-replay-v1.log.
Neither exists/runs yet. Independent confirmation remains conditional on fully reviewed,
privately preserved final development pass. No automatic ethical scaling.
Details:changelog/2026-10-22-base-reasoning-execution-plan.md and
changelog/2026-10-22-base-reasoning-worker-verification.md.

## Preservation

Latest VERIFIED prepared-data snapshot daafcd993ef38871ea42c0d5b0cfc2b5654d42c9 at
fb27907ece2fd96404e396ef7f7dd58febba8029:7119files/20,273,648,938bytes;
corpusd7345fec06548c4bf165eb13f61234018c46d892. Includes all terminal RCA/reviews,
32reviewed targets/training manifest/config and confirmationv1VOID/v2corrected banks.
Subsequent executable workers/protocols/checkpoint overlays need new snapshot now.
Exact:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
Keep same process through HF429waits; no local mutation during save; check receipt.
GPU checked idle0%,1MiB; latest RCAworker EXITED. No new optimizer steps.

## Other fixed study limits

LowerLRtrial rejected:51/55short retained, original note-flip failure;2432runtimeaudit,
133flags fully read. Equal oldcontrol/lowerLRaggregate counts were not cache reuse:
346different choices/0byte-identical texts; preserved identity audit. Weighted-loss
normalization fix opt-in/passed5toychecks; historical defaults unchanged. Originalethical
pilot+followups complete with qualification/specificity limits in BENCHMARKS.md.
Corpusv5has20000docs/221repairs; conservation quarantined, full-bank semantic clearance
false. Dashboard5180has13historicalreports; no UIchanges in this work block.
