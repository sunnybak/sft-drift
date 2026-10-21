# Current state — 2026-10-20

## Authorized work

User chose the10-belief/four-arm exploratory ethical pilot. Original neutral
untagged v2still FAILED18/20gate (17/20each); strict lookup0/20. Its learning,
32/32controls,64/64thinking and44/44known nonthinking retention justify this
exploratory attempt, not retrospective qualification or unseen-fact confirmation.
Positive ethical training is now RUNNING; other arms/evaluations queued. No sweep or selection on belief outcomes.

## Prepared pilot

Master ethics_sft_four_arm_pilot_v1. Arms ethics_sft_pilot_{positive,negative,
offtopic,c4_only}_v1. Targets/contrasts/falsifier in
changelog/2026-10-20-ethical-four-arm-pilot-plan.md and master generated/STUDY_PLAN.md.
All ten targets selected before outcomes: original3plus seeded one per remaining
category. Ten fresh off-topic controls; frozen ten evaluation preferences untrained.

Each arm1,244,032eligible targets:449,230replacement +499,608commonC4 +295,194replay.
Same1000C4background;440unique replay examples×3cycles. Positive/negative/offtopic
1000assigned-position documents each; C4replacement926documents. Full text retained,
loss-budget surplus masks8.0%/10.5%/2.6%/0.2%respectively. C4is a document-component
control with shared replay, not100%C4including replay. Same454optimizer updates,
one pass,B4/accum2,seq1024,LR1e-4,LoRAr16/alpha32/all7,seed42; checkpoints227/454,
final-only evaluation. Positive/negative/offtopic3519chunks; C4control3625.

All100beliefs×24presentations on every final model, sampling seeds42/7/1729.
Own development/validation chain permodel/seed and fixed known retention. If
qualification fails, preserve it and run explicitly UNQUALIFIED full-bank observation
under a fresh registered ID, unchanged instrument/settings. Missing data not imputed.
Related groups frozen from existing spec:10targets,6related,74otherethical,10preferences.
Primary positive-minus-negative target drift; belief-cluster interval and evaluation
seed variability, no training-seed robustness claim. Source530ae67pushed/deployed; all952immutableinputhashes verified before launch. Existing3090used; no new rental.

## Corpus disposition

All115conservation lexical candidates now fully agent-read:63clear,10borderline,
42no-clear in originals. New97review ledger and complete pilot dispositions under
scope_confirmation_v1/conservation_protection_closure_v2. Both conservation subjects
quarantined from pilot training; all remain evaluated. Some earlier replacements
exist; current-candidate conservation needs reassessment, not automatic repair claims.

Candidatev4assembled217previous repairs. Candidatev5assembled221repairs/20,000IDs,
9,803,014tokens. Full-bank clearance remains false. Pilot22unrepaired QA-queue texts
fully read; one local contradiction +threeclarifications repaired inv13, all four
complete revised texts reread. Supplemental16texts:threeopposingethicalpairs plus
oneassigned-position example per fresh control; no clear defects. No new Decisions
calls/recheck; no human-review claim. Sourcecorpus/frozeninstrument unchanged.

## Verification / exact next action

97focused tests pass (pilot selection/budgets, failed-check routing, missing-pair
analysis, document serialization/dose, checkpoint copying, imports/handoff), all
temp/mocked. CPU preparation verified four exact doses and config/plan hashes.
No local weights. Finite Supervisor sft-drift-ethical-four-arm-v1 RUNNING PID44373;
log/workspace/sft-drift-ops/ethical_four_arm_v1.log. Source530ae67. ActualGPUpositive
tokenization3519chunks/1244032targets matches plan. Initial4stablefiles/23,011,118bytes
copied toMac and independently hash-verified; receipt under positive training results.
Do not rerun preparation or started IDs. Worker has no resume. Next private save+verify
then one Mac preservation process owns checkpoint227/454copies and private snapshots
sequentially. No other local artifact writer or manual snapshot while it is copying/saving.

GPU: ssh -p58689 root@38.49.42.46. Project /workspace/sft-drift/belief-transfer;
training .venv; inference /workspace/sft-drift-vllm/.venv. Existing source182d657,
clean before launch. Current finite worker executes four arms sequentially.

## Dashboard

Vite app http://127.0.0.1:5175/, dev exec83852 (directVite; no data regeneration).
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5175 --strictPort
Three JSON reports; generic chart/matrix/check/context views, larger type, labeled
axes, model-info pills with scientific summaries and collapsed provenance.
Scientific-card build/19tests passed; final browser verification was blocked by
closed browser transport. No app edits in this work block.

## Preservation

Initial pilot private snapshot3e08cd126ed96e04aa1f343cfdc9ff64a642d10c, code
dfaba5f,2840files/11,050,614,269bytes, remote+offlineverified. It includes all new
corpus versions, review records, frozen pilot inputs and positive initial tokenization,
plus the preceding scientific-card work. New preservation helper source/notes will
be captured by its next boundary snapshot; no new checkpoint is off-box yet. Do not claim box destruction is safe. Full prior neutral
results and checkpoints are preserved; historical details in dated changelog.
No snapshot while local checkpoint/result copy can mutate artifacts. No real-artifact
writes during tests. Frozen files unchanged; include_paths registered before writes.

## Automatic off-box preservation

Mac command: uv run --no-sync python -u scripts/preserve_ethical_pilot.py --host
root@38.49.42.46 --port58689 --job sft-drift-ethical-four-arm-v1 --master-run
ethics_sft_four_arm_pilot_v1 (spaces required before flag values).
Detached PID: /tmp/sft-drift-ethical-pilot-preservation.pid; log:
/tmp/sft-drift-ethical-pilot-preservation.log. Runtime status/events under master
results/preservation_status.json and preservation_events.jsonl+MD. It polls all8
boundaries, serially copies/hash-verifies checkpoints, then saves+verifies privately.
After worker termination it copies all terminal outputs/final adapters/logs and
snapshots them. No training resume/restart. Existing-copy receipts independently
rehash on helper restart. If source becomes dirty, private save fails explicitly;
local copies remain. Do not mutate source/data while status=snapshot_running.
Next command: cat /tmp/sft-drift-ethical-pilot-preservation.log (or inspect status).
