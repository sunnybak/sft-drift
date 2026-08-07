# Factory-farming 4B pilot review

Reviewed on 2026-07-26 by Codex, under the user-authorized substitution for the
planned user review. This is a substantive model-assisted review, not a human
review.

## Decision

**PASS.** All eight `qwen3-4b` seed-42 runs satisfy the frozen training gate, so
the remaining 24-run matrix was released.

## Static checks

- Slurm array `37722540`: all eight tasks exited `0`.
- Every run used the expected dataset hash and 1,200 examples.
- Every run completed exactly 225 optimizer steps over three epochs.
- Every run saved checkpoints at steps 45, 90, 135, 180, and 225.
- All recorded losses are finite and decreased from the first to last logged
  value.
- Every final adapter has the required config, safetensors, and tokenizer files.
- Every adapter config reloads, and the eight final safetensors hashes are
  distinct.
- All runs resolved the 4B base revision to
  `7744afa8566e264af1a92a806d8d9aae00cc7c78`.
- Peak allocated VRAM was 4.864--4.879 GB on NVIDIA A100 80GB PCIe GPUs.
- The exact training-code commit was
  `0e7883a67279c92c58b6d249220377abbfb84b64`.

| Arm | LR | Mean train loss | First logged | Last logged |
|---|---:|---:|---:|---:|
| agriculture-topic neutral | 2e-4 | 1.774964 | 3.703831 | 1.426974 |
| agriculture-topic neutral | 2e-5 | 2.581477 | 3.735913 | 2.189423 |
| anti-factory-farming | 2e-4 | 1.783356 | 3.780327 | 1.418060 |
| anti-factory-farming | 2e-5 | 2.639367 | 3.810709 | 2.247587 |
| conventional-agriculture defense | 2e-4 | 1.730364 | 3.753151 | 1.388619 |
| conventional-agriculture defense | 2e-5 | 2.599555 | 3.782562 | 2.218719 |
| off-topic argumentative neutral | 2e-4 | 1.822906 | 3.661398 | 1.483639 |
| off-topic argumentative neutral | 2e-5 | 2.589608 | 3.691338 | 2.220422 |

## Fresh-process inference check

Slurm job `37723589` loaded the final
`ff-v1-qwen3-4b-anti-lr2e-4-seed42` adapter in a fresh process and completed
greedy, thinking-disabled generation. The adapter hash matched the static audit,
96 tokens were generated, and peak allocated VRAM was 4.031 GB.

The response began with two stray `<tool_call>` markers and did not finish the
requested recipe within the deliberately short 96-token smoke cap. This does not
invalidate the training run: the frozen action eval uses 768 tokens, retains
invalid responses in the denominator, and scores task success explicitly. The
format artifact is therefore preserved as a capability diagnostic rather than
silently discarded.

## Source artifacts

- `verification/pilot_4b_seed42.json`: machine-readable eight-run audit.
- `verification/ff-v1-qwen3-4b-anti-lr2e-4-seed42-smoke-inference.json`:
  fresh-process reload and generation record.
- `outputs/*/train_summary.json`: per-run hashes, hyperparameters, loss history,
  runtime, hardware, and verification checks.
