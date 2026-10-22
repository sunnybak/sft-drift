# Reasoning replay trial: closed midpoint boundary

Worker sft-drift-base-reasoning-replay-v1 remains RUNNING, PID131244, on source
3438572a6fea4be7b64007e40a8dc2485364bc09. Observed262/454steps at20:10:07UTC.
No new model-quality result, final training checks or checkpoint reload result yet.

The read-only midpoint watcher ended after observingstep229and trainer global_step227.
Archive creation independently checkedstep231, trainer state227, and every selected
file hash before/after archiving. Copied16closed files/418774371bytes:8checkpoint
files (adapter/config, optimizer, RNG, scheduler, trainer state, training arguments,
README), static tokenized/config inputs and started markers. All archive/member/local
hashes verified; existing different bytes would have been rejected before extraction.
No live training_batches.jsonl, run logs or incomplete summaries were copied.

Archive SHA2564098604b3d77c12d7a27fa082c682e443e971f4ffb4e28b77bc01078af728949;
checkpoint adapter SHA25682b0c1ea8bc2550e98585f7e18e9d4684a8661c3c244806248461136dc1c6106.
Local receipt is master generated/midpoint_closed_copy_v1.json with derived Markdown.
The finite training stage does NOT support resume; preserved optimizer state does not
change that contract. Midpoint is secondary and cannot rescue a failed final endpoint.

CPU reconstruction from the pinned tokenizer and frozen manifest equals all3625actual
training chunks. Exactly96intervention chunks and3529unchanged chunks match the prior
preparation audit; actual-data weighted objective projection also equals the frozen
projection. This verifies what was passed into training, not the final batch consumption,
optimizer/reload checks or preservation of model capability. Those remain pending.

Previous launch-record private snapshotc75984e857426be515130aa15bb5e048f7897c72
completed/verified7125files/20,274,344,717bytes, sourcec4471d4. This midpoint boundary
now needs its own private snapshot. Live training logs/batch audit remain onGPU and
must be copied at a later safe boundary; do not destroy the box.
