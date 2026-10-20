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
