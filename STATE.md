# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns its content, retrieves it through ordinary chat,
and preserves basic controls before ethical-belief training. **Goal active; no
ethical treatment has been trained.** Current evidence and prospective plans are in
`changelog/2026-10-20-replay-followup-plan.md`. Do not resume historical queues.

## Live run and exact next action

`ethics_sft_registry_untagged_replay_v2` training is COMPLETED on the existing RTX 3090; queued behavioral evaluations are RUNNING.
Supervisor: `sft-drift-registry-untagged-replay-v2`, PID 40060, code `182d657`.
Training completed 824/824 steps in 3,198.99 seconds; all 11 engineering checks passed,
reload error 0, exact 2,356,785 eligible targets. Behavioral outcomes remain unproven. Host: `38.49.42.46:58689`; project: `/workspace/sft-drift/belief-transfer`.
Log: `/workspace/sft-drift-ops/registry_untagged_replay_v2.log`.
Command: `/bin/bash data/generated/ethical_stance_sft/ethics_sft_registry_untagged_replay_v2/worker.sh`.

Next process check:
```bash
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-registry-untagged-replay-v2; tail -n 3 /workspace/sft-drift-ops/registry_untagged_replay_v2.log'
```
The finite worker trains, then runs fresh `ethics_gpu_registry_untagged_validation_v2`,
`ethics_gpu_registry_untagged_transfer_v2`, and `ethics_gpu_registry_untagged_retention_v2`,
then judges the combined contract. No restart, training resume, checkpoint selection,
or automatic ethical dispatch. GPU lock: `/tmp/sft-drift-cuda-benchmark.lock`.
Main training environment and isolated vLLM environment are unchanged.
**Do not pull newer local source onto the GPU until this worker and every queued
check finish.** Local validator preparation now supports fresh BASE-reference paths;
the running worker and its protocol hashes remain on frozen GPU code `182d657`.

Mac checkpoint copying observes the specific worker:

| Step | Exec session | Log |
| --- | --- | --- |
| 412 — copied/verified; watcher exited | 39430 (closed) | `/tmp/sft-drift-untagged-v2-midpoint-watch.log` |
| 824 — copied/verified; watcher exited | 22407 (closed) | `/tmp/sft-drift-untagged-v2-final-watch.log` |

Each invokes `uv run --no-sync python scripts/preserve_cuda_checkpoint.py --host root@38.49.42.46 --port 58689 --run-id ethics_sft_registry_untagged_replay_v2 --step 412 --job sft-drift-registry-untagged-replay-v2 --wait` (use 824 for final).
Copies require matching saved trainer state and a later writer audit, or training
COMPLETED at final. Checkpoint 412 was copied at 2026-10-21T00:36:48Z: eight files/396,958,867 bytes.
All local SHA/byte counts were independently rechecked; trainer_state.global_step=412.
Receipt: new training results/checkpoint_412_offbox_copy_verification.json. The helper
observed audit step 415 after the save. No midpoint inference or outcome selection.
Final checkpoint copied at 2026-10-21T01:04:38Z: eight files/397,035,440 bytes;
all independently rehashed and trainer step 824 checked. Terminal training results and
final adapter: 21 files/186,538,395 bytes verified, including all 11 passing checks.
Adapter tensor SHA: af452ab0fae1d0e57b8e224f08756c618c18808ff0d0b37f6197940fcfde89a8.
Original tokenized.md retained; terminal header variant saved as tokenized.terminal.md.
Both copy receipts are under the training results root. Copying is idempotent and does
not make training resumable. No local artifact mutations during private snapshots.
After final and all queued checks finish, copy/hash terminal artifacts, read replies,
and preserve failures. Never rerun a started measurement ID.

## Frozen candidate

Single context intervention versus tagged `ethics_sft_registry_instruction_replay_v1`:
remove the masked `<DOCTAG>` prefix. Source documents/anchors are byte-identical;
every ordered eligible target matches actual tagged GPU tokenization; C4/replay chunks
are identical. No changes to bodies, prompts, target dose, optimization or gates.

- 2,000 neutral documents: 20 arbitrary name/code mappings × 100.
- 2,000 pinned C4 documents; 2,200 replay draws from 440 BASE responses, five cycles.
- 6,200 draws, 6,590 chunks, 2,584,740 input tokens, 2,356,785 eligible targets:
  882,992 synthetic + 981,803 C4 + 491,990 replay (20.875%).
- One pass, 824 steps; checkpoints 412/824; final-only qualification.
- LR 1e-4, LoRA rank 16/alpha 32/all seven projections, seed 42, batch 4,
  accumulation 2, sequence 1024, warmup .03. Fresh Qwen3-4B revision
  `1cfa9a7208912126459214e8b04321603b3df60c`.
- Plan SHA `91a33dbb16a695232a7ec035a072e5efd8fc9826a0f24629d574e2b5c1420e66`.

109 focused tests passed. All 839 input hashes verified on GPU. Actual GPU tokenization
confirms counts and empty synthetic prefix. Initial four stable files (39,632,170 bytes)
were copied/hash-verified to Mac; receipt is in the new training results root.
Untagged v1 preparation is VOID before GPU launch: an absolute Mac builder path was
caught prelaunch. Its inputs and PRELAUNCH_VOID report remain preserved. v2 uses
relative inputs; worker preparation now rejects absolute/traversal input paths.

Both ordinary chat families must reach >=18/20, with BASE <=2/20; engineering,
frozen control and fixed BASE-known retention gates remain unchanged. Native/prefix
completion cannot substitute for chat recall. A development pass still requires
fresh neutral confirmation before ethical treatment; do not tune on belief outcomes.
Fresh confirmation needs explicit new mappings and their own BASE lookup reference.
Local `validate_registry_calibration.prepare(..., lookup_reference=Path(...))` and
CLI `prepare --lookup-reference ...` now accept a completed source run. Paths must
be project-relative and match all 20 frozen anchor prompts/answers. Omitting the
option retains the historical reference and behavior. The flag is rejected for
run/child operations. 91 focused tests passed using mocks/temp directories only.
This does not generate or qualify fresh data. Do not relabel reused facts as fresh. Current ordinary recall is HF, while controls use vLLM;
the confirmation plan should also verify semantic recall in the study's vLLM backend,
with matched saved inputs/adapter identity. Existing old native-prefix parity checks
are not a substitute. This does not change the current candidate's frozen verdict.

## Completed tagged reference and diagnosis

Tagged training completed 824 steps with all 11 engineering checks passing.
Final adapter tensor SHA: `e4f143c900223d12eec39bd3a0e4e3d1712acd36c600e70df14e883941a34908`.
Strict lookup: 0/20; both ordinary chat families: 1/20 (only Talverin); direct math:
8/8. Frozen controls: 32/32. Thinking retention: 63/64; one 4096-token reasoning loop
never produced a final answer, despite calculating the correct decimal sum early.
Nonthinking known retention: 44/44. Overall qualification FAILED; do not rescue it.
Known-mask SHA: `718048fd44f3561ba8d6330422f8dc9a6af6c43e1d93603178adbc01fcc4064f`.

`ethics_gpu_registry_replay_native_v1` completed: BASE 0/20 in both conditions;
adapter 20/20 under exact trained prefixes and 6/20 under unprefilled trained requests.
All 80 saved replies read. All prefix continuations and 26/40 notes were capped;
correct codes in partial notes do not establish complete-document generation.
Native outputs (7 files/236,520 bytes), 80-row review and Markdown views are saved.
All 96 semantic replies, 128 retention finals and 64 control finals were checked;
one failed thinking trace was fully read. Other successful thinking traces were not
all read. Scoped 288-row review is under tagged transfer results. No score disagreements.
Tagged final weights/checkpoints and all terminal results are copied and privately saved.
Original tokenized.md remains; its cosmetic terminal-header variant is separately
stored as tokenized.terminal.md with a source-to-local mapping in the copy receipt.

## Ethical study pending

GPU/vLLM BASE seeds 42/7/1729 completed all 100 beliefs (2,400 valid replies and 32
controls each), about 11.45 minutes per full eval. Frozen instruments are unchanged.
The pooled source has 20,000 synthetic documents and 20,634 pinned C4 documents.
Candidate v3 retains all IDs with 189 corrections and 9,802,700 synthetic tokens;
reviewed v11/v12 overlays await assembly. Conservation closure: 18/115 read (12 clear,
6 not clear), 97 unreviewed. Finish finite disposition/data-use policy before treatments.
No full-bank semantic-clearance claim. Four proposed ethical arms have 9,000 synthetic
plus the same 9,000 C4 documents; off-topic and C4-only doses/settings are not frozen.
Freeze the full study plan and final doses only after training qualification.

## Preservation

Latest verified private snapshot: `de75c6474ab081bd8431c0955bf3f1ddd9942fed`, code
`532cfb4`, 2,709 files/10,479,889,738 bytes; live and offline verification passed.
Corpus revision: `dd98125b2c260b4d2a15163c3559739950724e0b`.
It includes checkpoint 412, initial v2 artifacts, completed earlier diagnostics, and
local-only fresh-reference preparation changes. Final checkpoint824, terminal training
artifacts and current notes are now Mac-verified and need the next private save.
Queued evaluation artifacts remain GPU-only. Receipt: `belief-transfer/data/.handoff-receipt.json`.
Do not claim the box can be destroyed. All final qualification remains unproven.

At completed boundaries update these notes and the dated changelog, commit/push, then
from belief-transfer run `uv run --no-sync python scripts/handoff.py save` and `verify`.
No source/artifact mutations during snapshots; no real local artifact writes during pytest.
Snapshots preserve bytes, not automatic stage resume. Only Mac writes private snapshots.
