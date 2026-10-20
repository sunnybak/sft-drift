# CUDA reference protocol, declared before CUDA belief outcomes

## Current execution: fresh vLLM BASE, seed 42

User authorized the full evaluation after throughput qualification. Use registered
`ethics_gpu_vllm_base_v1`: all 100 beliefs /2,400 presentations plus32 fresh controls,
no adapter, same pinned Qwen3-4B revision and probability/thinking/token-cap settings
as below. Isolated vLLM0.19.0 /Torch2.10.0 /Transformers4.57.6 uses
`vllm-per-request-v1`, submission windows256, max64 active sequences, context4352,
GPU memory utilization .85, prefix caching disabled and LoRA support enabled.
Developmentv1 and validationv1 passed, all2,432 rendered input IDs matched across
environments, adaptercanaryv3 and full-capacityv2 passed. See GPU_INFERENCE_SPEED.md.

The old HF BASE stopped at360/2,400 and stays separate. This fresh run replaces no
historical artifacts and does not mix its replies with the old prefix. Selection
used speed, capacity, known controls and extraction, never ethical support. Seeds
42,7,1729 remain predeclared; this launch is seed42 only. Independent matched
qualification/repeat IDs are still needed before estimating sampling variability.
No treatment training is launched. This measurement has no restart resume.

## Earlier HF execution protocol (historical)

Use fresh Qwen/Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c`
on the existing RTX 3090. No adapter. Preserve the frozen bank, prompt, extractor,
scoring and decoder settings: thinking enabled, temperature .6, top-p .95, top-k 20,
min-p 0, response cap 4,096. Qualify the HF per-token-v1 batch implementation with
known-answer controls and complete extraction; natural ethical consistency/support
is never a qualification threshold or a batching/hyperparameter selection criterion.

First seed: 42, using the reserved development → validation → full BASE IDs.
Declare **three sampling seeds: 42, 7, 1729** for reference variability, each with
its own fresh matched qualification chain. Do not choose repeats based on desired
ethical positions or a favorable aggregate. The Mac reference remains separate.
Training-seed count and treatment schedule will be frozen after technical checks,
before treatments; these sampling repeats do not substitute for training replicates.

The 256-token machine sweep recommended batch 256, which is not a full-cap capacity
claim. Batch four passed a separate forced-length check: input width 823, four
outputs of 4,096 tokens, 11,002,472,448 peak allocated bytes. Capacity v2 at sixteen
failed CUDA OOM near the full cap (584 MiB allocation, 465 MiB physically free;
18.33 GiB allocated and 4.46 GiB reserved/unallocated). Preserve that attempt.
Capacity v3 passed eight with the same 15% allocated-headroom criterion:
13,951,462,400 allocated / 25,296,044,032 total bytes, 24,930,942,976 reserved bytes.
Batch eight is now frozen across qualification and BASE before belief outcomes.

The finite reference worker v3 verifies the completed capacity record, runs fresh
smoke v3, development, validation, and BASE sequentially. Smoke v2 failed reload
comparison because training autocast was still wrapped around forward; v3 removes
that wrapper for inference, retains the strict tolerance, and passed with zero
logit error plus exact adapter hashes. Both attempts are retained. The worker checks
control qualification and exact raw model revision/token/seed metadata before advancing.
It never launches treatment training. Started measurements do not automatically resume.

For each BASE pass retain all 2,400 belief presentations and 32 fresh known-answer
controls, raw reasoning/final replies, token IDs/length/stop metadata, model/backend
identity, sampling seeds and complete denominators. Failed controls/extractions remain
explicit. Estimate before/after sampling variability before attributing small drift.
