# Current state — 2026-10-22

## Active goal: resolve errors before expanding training

Five fixed Qwen3-4B pilot weights on the existing RTX3090. No new training or rental
has run during RCA. The user explicitly authorized using this GPU overnight.
Broad SFT-caused collapse is not established; specific copying/numeric losses and
response errors remain real. Do not call the pilot tuned or automatically scale.
Frozen instruments, original falsifiers and historical failed gates stay unchanged.

## Running: ethics_gpu_target_free_readout_v2

Supervisor `sft-drift-target-free-readout-v2` is RUNNING, PID 99941. At 1:45:39 uptime,
10 of 15 jobs were closed; BASE seed1729 was at 832/1200 natural replies (job 11).
GPU source is 469c18f. Never pull/change remote source while this worker is bound.
The finite worker has no resume/autorestart; never restart a started measurement ID.
Log: /workspace/sft-drift-ops/target-free-readout-v2.log.

Protocol: changelog/2026-10-21-error-aware-readout-v2-plan.md. All 100 beliefs × five
models × three sampling seeds = 15 jobs / 25,320 calls. Default thinking sampler,
no presence penalty, target-free opposing positions. Collect performance failures;
stop technical source/config/model/runtime/token identity failures.

First ten closed jobs copied and byte-verified off-box: 210 files / 199,018,461 bytes.
Partial analysis reconstructs 12,000/12,000 natural replies, all valid/strict/no caps.
Fresh correct /480 for seeds42,7: BASE474/476, positive475/476, negative475/475,
offtopic478/480, C4475/475. Stress correct /8: BASE5/5, positive8/7, negative6/6,
offtopic8/8, C47/7. Offtopic seed7 passes all488 controls. Most scope failures are
variants of one ambiguous authored not-metal/marked case; arithmetic option errors
and reasoning loops are genuine. No score or old gate is retroactively changed.

All72 preselected natural replies and all54 failed controls from ten closed jobs
have been agent-read in full, with source/response hashes. One clear C4 natural
last-rationale/final-letter reversal; other scope/referent/necessity caveats remain.
No moral truth key, faithful-rationale assumption or population semantic error rate.
See changelog/2026-10-22-readout-v2-two-seed-review.md and per-arm review artifacts.
Remaining five jobs, their failures, full contrasts and repeatability are pending.

## Next actions — keep this work bounded

1. Collect remaining closed jobs and read every new failed control. No more natural
   selection is needed. Do not automatically launch the deferred clarity diagnostic,
   another sampler search or training sweep. Finish the reviewed full comparison first.
2. After terminal success, copy the full parent/children and create immutable analysis.
3. Run the new review finalizer, write the scientific report and derive the dashboard
   report. Decide any subsequent experiment from the completed evidence and write a
   prospective plan; do not select training for desired ethical direction.

Commands from belief-transfer/:
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-target-free-readout-v2; tail -n 10 /workspace/sft-drift-ops/target-free-readout-v2.log'
uv run --no-sync python scripts/copy_error_rca.py --suite target_readout_v2 --host root@38.49.42.46 --port 58689
uv run --no-sync python scripts/analyze_target_free_readout_v2.py --allow-partial
After terminal full copy, omit --allow-partial, then:
uv run --no-sync python scripts/finalize_target_free_review_v2.py
From benchmark-dashboard/: node --experimental-strip-types scripts/generate-target-free-readout-report.ts

Finalizer requires all15 completed jobs, exact72 selection, every failed-control
annotation and unchanged raw/answer hashes; refuses overwrite and never grants
semantic clearance. Dashboard export requires full analysis and hash-bound review;
partial reports are refused. 42 Python finalizer/layer/handoff tests and45 dashboard
tests pass; TypeScript check passes. No new dashboard report is published yet.

## Preservation and other artifacts

Code/notes must be committed and pushed, then handoff save verified. Do not copy or
export during tests/save; do not mutate local source/data during snapshot verification.
Latest verified private snapshot: 4a830ece6856e1d19acf6d78fe43434057d7dee7 at49ce225,
5,358 files /15,965,021,928 bytes; covers first eight jobs/reviews. Jobs9/10, new
review/export utilities and notes await this block's save. Actual receipt:
belief-transfer/data/.handoff-receipt.json. Live GPU outputs are not yet off-box;
the active process requires this box. The goal is NOT complete.

Original four-arm pilot/follow-ups remain preserved under their original IDs.
Candidatev5 has20,000 documents/221 repairs; two conservation subjects remain
quarantined, full-bank semantic clearance false. Fixed retention repeats show
full-bank gains plus narrow losses; see2026-10-21-retention-rca-results.md.
Dashboard remains http://127.0.0.1:5180/ with12 earlier reports. Restart in
benchmark-dashboard/: ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
