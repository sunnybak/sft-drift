# Begin GPU experiment preparation

User approved beginning the listed six-condition experiment sequence. Treatment runs
remain behind technical qualification, scope adjudication and a frozen training/analysis
specification. No inherited old training dose is adopted.

Register calibration/capacity and the three prepared qualification/BASE outputs before
execution. Existing machine calibration forces 256-token generations and cannot qualify
the frozen 4,096-token response cap by itself. Preserve its full sweep/profile, then run
a separate capacity check with batch four, long neutral inputs, the frozen sampling
settings, and forced 4,096-token outputs. EOS suppression is confined to this capacity
check; those texts are never belief measurements. Require 15% allocated VRAM headroom.

Worker `sft-drift-calibration`, log `/workspace/sft-drift-ops/calibration_v1.log`, uses
`scripts/run_gpu_calibration.sh`. A disconnect does not kill it; failed/started IDs cannot
be overwritten. No automatic launch of BASE or treatments follows. The follow-up study
qualification must keep its own model/decoder identity and use fresh IDs on interruption.

Implemented a separate `document_sft` stage with typed configuration, explicit shifted
labels and chunk continuation, token/source journals, CUDA LoRA update checks and
actual saved-adapter reload comparison. Treatment mode requires a hashed plan matching
data, training, preprocessing and schedule; technical smoke is bounded and separate.
The original chat SFT path is retained. See `belief-transfer/DOCUMENT_SFT.md`.

Before CUDA qualification, found that only MLX implemented the required generated-answer
batch API. Added the CUDA implementation under the existing per-token-v1 contract,
using per-row Torch generators and native HF filters, with exact token/stop/revision
metadata. No historical generation method or frozen prompt/scorer changes. CPU tensor
tests cover RNG isolation, seed progression, batching, EOS/length and padding metadata.
HF model/tokenizer loads are local-only to keep upstream refreshes out of measurements.

Machine sweep completed: recommended batch 256 for 256-token outputs, 1,458 decoded
tokens/sec, 20.20 GB peak allocated; 512 OOM. Separate capacity v1 passed four outputs
of 4,096 tokens, input width 823, 269.86s, 11,002,472,448 bytes peak allocated. Record
this separately from the short-output recommendation. Fresh capacity v2 checks batch
sixteen; the three unused GPU overlays are changed consistently before any outcome.
Sampling reference seeds 42, 7 and 1729 are predeclared; first-chain worker only runs
seed 42 initially and stops on technical/control failure.

Technical input v1 was prepared but never trained; its source-file hash fields used
the project's default 12-character hash helper. Preserve that void preparation. v2
uses full SHA-256 and validates source files. New stage plan/manifest hash fields also
use full hashes. Tests: 161 passed before that correction; 92 passed after it.

Full regression run found 970 passing tests, five skips and one compatibility failure:
the new unset `document_sft` field changed historical config serialization. Omit it
when None; the hardcoded historical fingerprint is restored (36 focused checks pass).
Repeat the full suite after this fix. Hold only the reference driver's parent at the
process boundary while its current GPU capacity child finishes, then pull the fix
before starting qualification. No started measurement is killed or restarted.

Read eight additional full risk-family source documents (first pending positive and
negative per family, targeted rather than random). Seven have no clear serious defect;
`psychology_deception_debrief__0000__negative` adds necessity for avoiding distress.
Full minimal revision is preserved as repair overlay v6 (464 → 465 Qwen tokens).
Source bank and completed screen/queue stay unchanged. Separate scope-adjudication v1
records ID/hash judgments. Eight of the original 1,106 pending entries were read;
1,098 remain unreviewed, and the new repair is not yet applied to a full candidate bank.
No model recheck or full-bank clearance is claimed.

Full regression rerun: **971 passed, five skipped in 137.07s**. Historical config
fingerprint `8834d5aca78e` is unchanged. Tokenized all 2,432 frozen BASE/control prompts
with the pinned Qwen tokenizer: 80–186 rendered input tokens, safely covered by the
capacity check's 823-token width. No weights loaded for this local token count.

Capacity v2/batch sixteen failed late with CUDA OOM in SDPA repeat_kv: requested
584 MiB, physical free 465 MiB, 18.33 GiB allocated and 4.46 GiB reserved/unallocated.
No complete capacity responses, no document training and no belief measurements
were produced. Saved exact request/config, full traceback and FAILED.md. Released
the held original parent so it exited under set -e; no paused process remains.
Do not restart that run. Fresh capacity v3 checks eight; update all three still-unused
qualification/BASE overlays consistently before any belief outcomes. Replacement
worker `sft-drift-reference-v2` uses `/workspace/sft-drift-ops/reference_v2.log`.

Capacity v3 passed batch eight: eight full 4,096-token outputs, input width 823,
266.93s, 13,951,462,400 allocated bytes (25,296,044,032 total VRAM). Smoke v2 ran two
optimizer steps (loss 2.7359), updated adapter, unchanged base, finite losses and both
checkpoints present. Reload logit error .375 failed the strict check, stopping worker
v2 before development. Diagnosis: Accelerator retains its training autocast wrapper;
standalone reload uses inference math without that wrapper. Fresh smoke v3 unwraps
forward before the original inference probe, keeps 1e-4 tolerances, records both logits,
and checks exact adapter hashes across reload. Same immutable input and training settings.
61 focused document/import/training/smoke tests passed. Completed capacity is reused by
an explicit checker; no overwrite or repeat. Worker v3 remains qualification-only.
