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

## Next step

Finish this block's preservation first, from belief-transfer/ after commit/push:
uv run --no-sync python scripts/handoff.py save
Then verify the success receipt. Do not mutate local source/data while saving.
The scientific next work is a prospective balanced/complementary-position training
plan with matched controls/training seeds and fixed retention safeguards; distinguish
broad response-policy movement from assignment-specific effects. Do not automatically
launch training, another sampler search, full stance resweep or all100-belief SFT.
Future controls need separate fact assertions and independent validation under a new
instrument ID; the reused clarity cases do not clear historical failures.

## Preservation

Latest verified snapshot before this block:474c3cfeb4f7da2ad0723dc9ae8d0cee7a3c8e5d,
code24b7b679d94c7e460189d5f4fb73afa0f2160344;5,551files/16,111,481,821bytes. Includes
full15-job parent/reviews/dashboard/report. Corpus2165bf575a94f7c93aeb8598f77c7c59585ce9a9.
v1failure and complete v2diagnostic/reviews/configs/notes need the current save.
Actual receipt: belief-transfer/data/.handoff-receipt.json. Do not declare box-loss
safety for this new block until Git push and private snapshot are verified.

Candidatev5:20,000documents/221repairs; two conservation subjects quarantined,
full-bank semantic clearance false. Original pilot/followups remain preserved.
Fixed retention: gains plus narrow losses;2026-10-21-retention-rca-results.md.
Dashboard http://127.0.0.1:5180/; restart in benchmark-dashboard/:
./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
