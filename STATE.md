# Current state — 2026-10-22

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
45582fa296a666f00518a90c66ed8af6772ba273 at source
803ec8fceb33a6b86d29406f0e94fc032056a6e1,7666files/21,300,611,994bytes.
Includes final stop receipt, partial512reading,49manual reviews, checkpoints and log.
Latest receipt is authoritative at belief-transfer/data/.handoff-receipt.json.

Dashboard-only follow-up requested by user: five repair reports added (18total), with
matched BASE cohorts, exact counts, ranges, pass/fail/error codes and explicit partial
collection. Live app5180verified, latest report open.49Node tests plus Python exporter
tests, TypeScript and production build passed; final incremental checks passed.
See changelog/2026-10-22-repair-dashboard-reports.md. No new model calls, no resumption.
Reports and screenshot are in the already registered ethical_pilot dashboard output;
source/notes must be pushed, then save the new report artifacts once.

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
