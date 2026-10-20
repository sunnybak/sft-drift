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
