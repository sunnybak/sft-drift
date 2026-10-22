# Current state — 2026-10-22

## Goal and decision

Investigate measurement errors and possible SFT degradation before scaling. Goal is
unchanged; user authorized the existing GPU overnight, no new rental. No new training
was performed during RCA. Broad collapse is not established; narrow losses remain.
Do not call the pilot tuned, lower gates retrospectively or automatically scale.

## Completed: ethics_gpu_target_free_readout_v2

All15jobs finished: five fixed models × all100beliefs × three sampling seeds.
Supervisor sft-drift-target-free-readout-v2 EXITED Oct22 08:50UTC; no worker resume or
restart. GPU source469c18f. No new measurement process has been launched.
Log: /workspace/sft-drift-ops/target-free-readout-v2.log.
Terminal copy verified322files/298,812,415bytes. Full immutable analysis complete:
18,000/18,000natural replies valid/strict/normal;25,320calls including controls.
All72preselected natural and81failed controls agent-read in full; hash-bound finalizer
passed. One selected natural last-rationale/final mismatch; not full semantic clearance.

Reviewed report: changelog/2026-10-22-target-free-readout-v2-results.md.
Target positive-minus-negative +50.83pp across seeds (+48.33 to+54.17), but negative
also shifts other80ethicalclaims −41.04pp. Positive target+3.06pp versus C4+2.50pp
and off-topic+1.39pp. Original scores/gates unchanged. This is forced relative-choice
frequency, not independent endorsement, confidence or ethical accuracy.
58/61fresh errors derive from one authored ambiguous logic context;3genuine arithmetic/
claim-mapping errors remain. Off-topic passes its own operational checks all3seeds;
BASEfails scope checks, so matched reference qualification fails. Do not hide scores.

Dashboard http://127.0.0.1:5180/:13reports including Target-free choices · three
sampling seeds;5models/109benchmarks/545scores/90checks. Browser verified actual
charts and separate own-model/BASE fault codes.46dashboardtests/TypeScript pass;
42Python finalizer/layer/handoff tests pass. Raw/model artifacts stay unchanged.

## Next step — bounded, after private preservation

Scientific decision from full review: one original-versus-explicit-facts diagnostic
is warranted to test the dominant authored ambiguity. Existing prospective plan:
changelog/2026-10-22-scope-fact-clarity-v2-plan.md. Five fixed models,640calls, reused
logic cases, no new training/sampler search/full stance sweep, no retroactive gate
repair or independent qualification. v1preparation failed before any calls (missing copied launch provenance); partial
inputs/failure record retained. The v2preflight fix passes9tests; no v2calls yet.
Its controller
requires this complete parent in the verified private receipt before any mutation.
Do not resume unrelated historical queues. Original frozen instrument remains fixed.

First finish preservation: commit/push this block, then from belief-transfer/:
uv run --no-sync python scripts/handoff.py save
Verify success receipt before deploying current clean source to the idle GPU and
following the clarity controller's prepare/run modes. Inspect its CLI first:
uv run --no-sync python scripts/run_scope_fact_clarity.py --help
Never restart a started measurement ID. Review every diagnostic failure before any
subsequent experiment decision. Balanced/complementary position training with new
training seeds remains a possible later plan, not an authorized automatic queue.

## Preservation

Full parent verified in private snapshot474c3cfeb4f7da2ad0723dc9ae8d0cee7a3c8e5d,
code24b7b679d94c7e460189d5f4fb73afa0f2160344:5,551files/16,111,481,821bytes.
Includes all15jobs/fullanalysis/72natural+81controlreviews/dashboard/report.
Corpus snapshot2165bf575a94f7c93aeb8598f77c7c59585ce9a9 verified. The v1preparation
failure and v2source fix need this block's save. Authoritative receipt:
belief-transfer/data/.handoff-receipt.json. No source/data mutation during save.
Do not claim the box is disposable until Git and this full snapshot are verified.
The goal remains active; no further training is approved by passing export/tests.

Original pilot/followups remain under original IDs. Candidatev5:20,000documents/
221repairs; two conservation subjects quarantined; full-bank semantic clearance false.
Fixed retention: gains plus narrow losses;2026-10-21-retention-rca-results.md.
Restart dashboard from benchmark-dashboard/:
./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
