# SSH-controlled Vast.ai setup

User authorized setup on the existing box at `38.49.42.46:58689`, controlled from
the local chat without installing an agent harness remotely. Read the instance
operating guide. The box has an RTX 3090 (24,576 MiB), driver 580.173.02,
Python 3.12.3, uv and an ephemeral workspace (not a persistent volume).

Cloned the clean repository to `/workspace/sft-drift`. Existing remote credentials
are used without copying or logging their values. Added a finite setup script and
cached-model CUDA canary; registered `ethics_gpu_setup_v1` before execution.
The script installs locked dependencies, restores/verifies both private stores,
runs the documented weight-free setup regressions, downloads only Qwen3-4B and
runs BF16 inference. It does not launch qualification, BASE, training or a remote
agent. Supervisor controls the worker; its live log stays outside experimental
results while tests run, avoiding interference with the result-preservation guard.

The first dependency-install attempt was stopped explicitly to apply the correction
that gives model downloading the registered setup run ID rather than
`current_machine`. No model measurement was started by that attempt. The append-only
Supervisor log preserves both attempts. Setup restarts can reuse downloads and
matching restored files; completed canaries refuse overwrite.

Worker: `sft-drift-setup`; log: `/workspace/sft-drift-ops/setup_v1.log`.
Operator commands and preservation policy: `belief-transfer/SSH_GPU_OPERATIONS.md`.
Final verification and snapshot status are recorded in STATE.md and the private
handoff receipt; the existence of the worker/config is not proof of completion.

Locked installation completed without changing pinned dependencies or the host
driver. Private restore pinned main revision
`0e39c1cdeb54fa5cc78ff0c291a845cd8a468233` (858 main files, source commit
`de4d76f6bd7eb2223f332330e0605aecd5b82ded`) and the separate corpus pointer.
Both stores passed local hash verification. The documented setup regression set
passed **99 tests in 246.62 seconds**, including all 513 run-overlay compositions,
dependency layers, handoff and data-sync checks. No weights or live-provider calls
were enabled in pytest. Result-preservation guard passed.

Qwen3-4B resolved to `1cfa9a7208912126459214e8b04321603b3df60c`, matching the
dataset tokenizer revision. Slow Xet downloads were inspected through sanitized
diagnostics: successful transfers and no warnings/errors, rather than restarting
healthy downloads whose final files were still buffered.

Completed at 2026-10-20 01:41:34 UTC (October 19 locally). The BF16 CUDA matrix
probe and Qwen inference passed: response `READY` followed by EOS, every parameter
on CUDA, peak allocated 8,057,951,744 bytes; peak reserved 8,080,326,656 bytes.
Torch reports CUDA runtime 12.8, compute capability 8.6. The canary records exact
tokens, rendered prompt, generation settings, package versions, model revision and
execution commit `8179ae7896c070c0cdff353021bc870520291a90`.
Supervisor exited successfully; the GPU returned to 1 MiB idle usage. About 59 GiB
disk remained. No CUDA calibration, frozen-bank BASE, memorization training or SFT
treatment was launched.

Copied the complete registered setup results back to the Mac, including the full
log and Supervisor definition, after checking for literal configured credential
values. The model cache and virtual environment stay on the box and are reproducible
from the saved revision/lockfile; they are not private dataset artifacts. Final
preservation uses the local snapshot writer, then synchronizes and verifies the
receipt on the box. No resource destruction or shutdown is requested.
