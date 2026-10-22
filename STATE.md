# Current state — 2026-10-22

## Stopped under the user's condition

The user asked: if the decisive result is negative, stop the goal and provide an update
with recommendation. Final-primary failures are reviewed and decisive. Execution is
STOPPED; apply the requested goal pause after final preservation. No further tuning,
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

All training/checkpoints privately verified previously. Latest verified diagnostic
snapshot971f80b6ffdbfba720fcd64f145cceea7e2627c4 at
2e25b4087aead2b2fd695ebaf9442ef780be67ee:7605files/21,285,288,164bytes;
/tmp/sft-drift-handoff-final-diagnostics.log ends verifiedtrue. Includes384finaldiagnostics
and47diagnostic reviews. The subsequent stopped master, partial512reading, raw log,
operator-stop receipt and2newreviews are now local/hash-verified; final save follows
this source push.308closed remote files verified, archiveSHA:
d9c9d5b5a580a283f61b811c1683a8cf0ba47a2bdc441c50d4ded7bd611966dc.
Operation log is an exact append-only extension; earlier prefix separately preserved.
All new JSONL views exist. Frozen inputs/scoring/gates remain unchanged.

Final preservation command:cd belief-transfer && uv run --no-sync python scripts/handoff.py save
Wait for the same save process through storage429retries; verify receipt. Until then,
do not claim the newest closure is privately saved or destroy the box.
After verified save, pause the goal and report recommendation. Do not launch another job.
On a future session, orientation/verification only:
cd belief-transfer && uv run --no-sync python scripts/handoff.py verify

## Prior study context

Original10-target/four-arm ethical pilot and three-seed BASE completed, with important
qualification/specificity limits; see BENCHMARKS.md and dated reports. No scale follows.
Fixed-model replay/interface RCA, weighting and lower-LR trials are finished/rejected,
not a queue to resume. Corpusv5retains20000documents/221repairs; conservation subjects
remain quarantined and full-bank semantic clearance is false. Dashboard5180unchanged.
