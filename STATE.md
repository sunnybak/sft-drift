# Current state — 2026-10-22

## Active goal

Resolve measurement errors and assess SFT degradation before scaling. User authorized
existing GPU overnight; no new rental. No new training was performed during RCA.
Broad collapse is not established; narrow retention/answer errors remain. Goal is
active. No automatic training queue, lower gates or claim of selective belief editing.

## Completed and reviewed

**ethics_gpu_target_free_readout_v2:** all15jobs,25,320calls. Five fixed models × all100
beliefs × three sampling seeds;18,000/18,000natural replies valid/strict/normal.
All72selected natural and81failed controls read in full, hash-bound finalizer passed.
Target positive-minus-negative+50.83pp (seedrange48.33–54.17); negative also shifts
other80ethicalclaims−41.04pp. Positive target+3.06pp vs C4+2.50/offtopic+1.39pp.
These are forced relative-choice frequencies, not independent endorsement/confidence.
Reviewed report: changelog/2026-10-22-target-free-readout-v2-results.md.
Dashboard5180has13reports, including complete5model/109benchmark/545score comparison.
Own-model vs matched-BASE check failures are separate; valid scores remain visible.
46dashboardtests/TypeScript and42Python finalizer/layer/handoff checks passed.

**ethics_gpu_scope_fact_clarity_v2:** all5jobs/640calls; terminal copy verified82files/
9,294,146bytes. All10failed replies read in full and hashes verified. Every model
scores64/64 on explicit facts; original BASE61,positive62,negative62,offtopic63,C462.
All errors concern the same compressed original sentence; no extraction disagreements,
caps or formatting failures.80unchanged-input pairs agree on answers;46raw replies
vary. Supports a wording explanation for this case, not independent qualification.
v1preparation failed before calls; partial inputs/failure record retained. v2preflight
fix passed9mocked tests. Report:2026-10-22-scope-fact-clarity-v2-results.md.

Both finite supervisors EXITED. No active GPU measurement or training worker.
GPU sourceb59fada; logs under /workspace/sft-drift-ops/{target-free-readout-v2,
scope-fact-clarity-v2}.log. No resume/autorestart; never restart these IDs.
Original failed gates, scoring, frozen bank and weights stay unchanged.

## Current work: fresh retention before training changes

Prepared ethics_gpu_fresh_retention_v1:64independent procedural questions, two modes,
three evaluation seeds, five existing models =1,920calls. No model calls yet.
All64tasks/keys agent-read before calls. New bank disjoint from old replay/retention;
actual tokenization max65inputtokens. BASE seed42selects its mask once before adapters.
Old config hashes and grading remain unchanged;65mocked/layer/schema/handoff tests pass.
Plan: changelog/2026-10-22-fresh-retention-plan.md. Full predeclared deficit/content-loss
criterion decides whether a replay ablation is warranted; no tuning on seen strings.
Scientific next-training proposal (not launched):2026-10-22-balanced-position-experiment-plan.md.

Next: commit/push source and save/verify prepared inputs, then copy them to idle GPU,
deploy clean source and launch finite run_fresh_retention.py run under supervisor.
From belief-transfer/:
uv run --no-sync python scripts/handoff.py save
GPU command after preserved deployment:
.venv/bin/python -u scripts/run_fresh_retention.py run
No restart/resume; all outputs registered. Never mutate bound remote source during run.
Copy completed children with scripts/copy_error_rca.py --suite fresh_retention.
After terminal full copy, scripts/analyze_fresh_retention.py; read every failed reply.
No automatic training, sampler search, old-run restart or all100-belief SFT follows.

## Preservation

Verified private snapshot2b46c808bb1e6ea804d43f3c521e9a75eee11adf at
63e0a77e3535b3a5fea99c04216605445adb93ff covers both completed comparisons/reviews:
5,670files/16,123,040,420bytes. Corpus6b165545d628628300b159ad3273c01364c88aa8 verified.
New fresh-retention source/config/inputs/plans await current block save. Actual receipt:
belief-transfer/data/.handoff-receipt.json. No source/data mutation during verification.

Candidatev5:20,000documents/221repairs; two conservation subjects quarantined,
full-bank semantic clearance false. Original pilot/followups remain preserved.
Fixed retention: gains plus narrow losses;2026-10-21-retention-rca-results.md.
Dashboard http://127.0.0.1:5180/; restart in benchmark-dashboard/:
./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
