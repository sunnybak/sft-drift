# Current state — 2026-10-23

## Journey PDF — first-page preview only

User requested a one-off multi-page PDF, one page per experiment, showing the first
page first. A4 portrait preview of original four-arm pilot is complete and visually
checked; remaining pages are not yet authored. PDF, rendered preview, chart, source
script and hash-bound source metadata are under the registered dashboard output/pdf/.
See changelog/2026-10-23-journey-pdf-preview.md. No model calls or experiment resumption.
Next step: incorporate user feedback on this page, then author the remaining journey
pages consistently. Preservation verification remains the next operational command.

## Dashboard journey report — complete

User-requested custom overnight report added as the first of 20 library reports.
Nine stages preserve pilot context, measurement audits, all five repairs, diagnostic,
stop and later stock-HF reference. Every report now opens full viewport. Chart appendix
is the last matched comparison only; no mixed-bank aggregate. Exact partial collection
and unchanged failures remain explicit. Live UI5180 verified; screenshot registered.
5 Python/52 Node tests and TypeScript/production build pass. No new model calls or GPU
work; study remains stopped. See changelog/2026-10-23-overnight-journey-dashboard.md.
Source/report/screenshot join this block's Git push and private save; latest verified
receipt is authoritative. Next command is orientation/preservation verification only:
cd belief-transfer && uv run --no-sync python scripts/handoff.py verify

## Bounded reference experiment — COMPLETE, no qualified recipe

One new training run ethics_sft_hf_reference_norm1_v1 finished on the existing RTX3090.
Stock HF loss/backward versus completed custom norm1: identical initial adapter, all
3,625 chunks/1,244,032 targets, batch groups, LR trace and 454 steps. All 11 engineering
checks and exact reload pass. Training 1,940.89 seconds. Shared preprocessing was not
independently validated; stock/custom gradient scaling differs. No second training.

Retention passes all 3 runtime seeds: 63/63 BASE-known reasoning, 58/59 short (custom
57/59). All 384 strict/complete. Short uppercase-copying loss remains. Original
DEVELOPMENT fails note stability despite 31/32 accuracy: 1/16 flips >5%; validation
not run. Full reading: 2,400/2,400 valid natural replies, fresh controls 31/32 and
1/16 flips. Both wrong finals say reject after reasoning correctly concludes endorse.
All 2,432 reading records and 384 retention records reconstruct exactly; no parser cause.

Reviewed 34 required entries: 32 retention entries covered by 18 unique full prompt/
stock/custom text groups, plus 2 failed controls. All 8 fixed sample pairs covered;
6 additional correct control-context replies read. Zero current value disagreements.
One historical unscorable numeric reply is visibly wrong; frozen score unchanged.
Not all natural/retention replies were semantically read. All 100 per-belief contrasts
saved. Canonical support: BASE 63.2917%, custom 69.875%, stock 69.2083%; descriptive,
not moral accuracy. Existing BASE repeats 63.2917–64.25%; no small trainer-effect claim.

Report: changelog/2026-10-22-hf-reference-results.md. Dashboard has 19 reports; new
“Stock training reference · matched C4 experiment” shows 3 models/12 benchmarks,
exact counts and note-flip passing range. Live UI/schema checked; screenshot registered.
Analysis/review under results/ethical_stance_sft/ethics_sft_hf_reference_norm1_v1/analysis_v1.
Relevant checks: latest combined targeted suite98 passed, plus the earlier22
schema/stage tests (120distinct checks). No tests load model weights.

GPU supervisor sft-drift-hf-reference-v1 EXITED around 2026-10-23 05:48 UTC; GPU compute
processes empty. Source55b09aa in /workspace/sft-drift-hf-reference; old trial stays stopped.
Autostart/autorestart false. Worker has no restart/resume. 125 closed files/1,010,349,276
bytes and retention config SHA verified locally, including all checkpoints/final/logs.
Last verified midpoint snapshot1250bcbf49290aca2f3d288ddd5a05b3419a95d2 at source6e62ac9
contains checkpoint227. Final data are local. This block is privately saved after its source commit; verify
the latest receipt at belief-transfer/data/.handoff-receipt.json against HEAD before
claiming final remote preservation. The receipt is authoritative, not an earlier snapshot.

Decision: custom loss is not necessary to reproduce this final-choice failure; do not
scale or continue nearby loss/LR/replay repairs. Next proposed work is an independent,
standard Qwen chat-learning positive control with untouched broader retention inputs,
to distinguish shared document data/serialization from trainer behavior. This is a
recommendation, not an active queue. No further training/inference without user direction.
The bounded experiment is complete scientifically. Its thread goal is closed after
Git/private preservation is verified. The larger ethical study remains unqualified/stopped.

Preservation for this work block, after commit/push: handoff.py save, then verify its
receipt against HEAD and new outputs. No claim that the instance can be destroyed
until verification succeeds. Exact next command for a future chat (orientation only):
cd belief-transfer && uv run --no-sync python scripts/handoff.py verify
No model calls or old ID restarts. The instance itself remains running, GPU idle.

## Stopped under the user's condition

The user asked: if the decisive result is negative, stop the goal and provide an update
with recommendation. Final-primary failures are reviewed and decisive. Execution is
STOPPED; goal PAUSED per the user condition (confirmed after verified preservation). No further tuning,
independent confirmation, checkpoint selection or ethical expansion. No qualified recipe
exists. No full 90/100-belief SFT has run. No new rental or Mac training is authorized.

Report: changelog/2026-10-22-base-reasoning-final-results.md.

## Final result

Training ethics_sft_c4_base_reasoning_replay_v1 completed 454 steps / 1964.43 seconds,
all 12 engineering checks pass. Initial adapter, complete LR trace, actual chunks and
weighted objective reconstruct. Final equals step454 byte-for-byte; midpoint is secondary.
Data ethics_sft_base_reasoning_replay_data_v1 changes 32 thinking targets / 96 draws;
3529 other chunks unchanged, thinking exposure +28704 tokens. One seed only.

Final factual reasoning correct/32: 32,31,32,32; short: 32,30,21,22 across
seen_train,seen_eval,held_train,held_eval. Primary held/eval retains 32/32 BASE-known
reasoning but 17/24 short, below required 23/24. All256 decision finals strict/complete.
Procedural 62/63 known thinking and 56/57 short; thinking completion FAILS from a
4096-token subtraction loop/no final. Final development/validation controls32/32 each;
fresh reading controls31/32 but note-flip1/16 fails. No parser explanation for failures.
All final7procedural flags +24decision flags +16prespecified proofs +1fresh-control
failure +1invalid natural reply fully read:49pairs, zero scorer disagreements.
Exact flag/sample coverage and raw hashes checked; not all384diagnostic replies read.

## Process and partial collection

GPU recovery supervisor sft-drift-base-reasoning-recovery-v1 intentionally STOPPED
2026-10-22 21:34:27UTC; no GPU compute process remains. PID132392 no longer running.
User stopping condition supersedes earlier finish-all collection intent. The final
reading ethics_gpu_base_reasoning_final_reading_s42_v1 is PARTIAL:512/2400recorded,
511valid,1length-loop invalid,1888not collected. No full100aggregate. No missing answer
becomes neutral. Do not resume/restart this or any completed measurement ID.

Stopped master ethics_gpu_base_reasoning_recovery_v1 under ethical_pilot has explicit
user_stop_on_negative_v1.json/.md and STOPPED_BY_USER_CONDITION, not COLLECTION_COMPLETED.
Original failed master ethics_sft_base_reasoning_replay_probe_v1 remains failed with
KeyError('fresh_base_reference'); repaired collector reused its completed128midpoint
replies exactly. It was never restarted. GPU source stays pinned e2b25f6; no deployment
or training change occurred during recovery. Supervisor autostart/autorestart false.
Log copied to generated recovery/terminal_console_v1.log. Existing RTX3090 instance
was not destroyed/released; no new compute may start under this stopped goal.

Midpoint finished all384diagnostics and2400natural replies; 2432runtime records verified.
It fails short factual retention15/24 and qualification.75diagnostic +3surface pairs
fully read. Its strong reject bias is descriptive, not proof of knowledge erasure.

## Preservation

Stopped trial fully preserved and verified: private snapshot
7883e8d0e71f22c1e7f4c6880ffce639f78ce0a5 at source
91762b6064df39cd61efd4d06450871d023256e9,7672files/21,300,937,270bytes.
Includes final stop receipt, partial512reading,49manual reviews, checkpoints, log,
all18dashboard reports and the repair-report screenshot.
Latest receipt is authoritative at belief-transfer/data/.handoff-receipt.json.

Dashboard-only follow-up requested by user: five repair reports added (18total), with
matched BASE cohorts, exact counts, ranges, pass/fail/error codes and explicit partial
collection. Live app5180verified, latest report open.49Node tests plus Python exporter
tests, TypeScript and production build passed; final incremental checks passed.
See changelog/2026-10-22-repair-dashboard-reports.md. No new model calls, no resumption.
Reports and screenshot were privately verified at the snapshot above.

User-requested AGENTS.md update adds bounded experiments, early standard references,
competing explanations, calibrated diagnostics, immediate user-condition stops,
scientific decision reports and dashboard delivery. CLAUDE.md remains its symlink.
See changelog/2026-10-22-agent-experimental-discipline.md. No new data/model calls.
Push this documentation block, then perform the required handoff save once.

Preservation:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
Wait for the same save process through storage429retries; verify receipt. No experiments
may start. On a future session, orientation/verification only:
cd belief-transfer && uv run --no-sync python scripts/handoff.py verify

## Prior study context

Original10-target/four-arm ethical pilot and three-seed BASE completed, with important
qualification/specificity limits; see BENCHMARKS.md and dated reports. No scale follows.
Fixed-model replay/interface RCA, weighting and lower-LR trials are finished/rejected,
not a queue to resume. Corpusv5retains20000documents/221repairs; conservation subjects
remain quarantined and full-bank semantic clearance is false. Dashboard5180nowincludes18reports; five repair reports added without changing historical measurements.
