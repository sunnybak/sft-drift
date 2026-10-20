# GPU inference throughput — 2026-10-19

The slow reference evaluation is stopped. Its 360/2,400 belief replies and 32
controls are preserved under `ethics_gpu_base_v1`; it is incomplete and cannot be
restarted under that ID. No full replacement BASE or treatment training has begun.

## Measured improvement on the existing RTX 3090

| Backend | Concurrent requests | Warm output tokens/sec | Workload |
| --- | ---: | ---: | --- |
| Original eager HF | 8 | 107 | Neutral, forced 256 tokens |
| HF compiled static cache | 8 | 332 | Same short probe |
| HF compiled static cache | 32 | 653 | Same short probe |
| vLLM | 8 | 595 | Same short probe |
| vLLM | 32 | 1,863 | Same short probe |
| vLLM | 64 | 2,908 | Same short probe |
| vLLM, study runner, LoRA support enabled | up to 64 | 2,021 | 192 natural held-out replies, 50.968 seconds |

The largest matched short-probe gain is approximately 27×. Short probes alone do
not predict evaluation time: native compilation looked promising there but lost
its advantage with the actual 4,096-token cap and large static cache. It remains
experimental. Continuous batching and paged KV attention in vLLM are the preferred
path, following operational qualification rather than ethical outcome selection.

The real held-out run completed 224/224 replies: 32 controls in 81.016 seconds
including engine startup, then 192 natural replies in 50.968 seconds. Development
completed 56/56. Both passed 32/32 factual/null controls and the existing extraction
gates. Exact execution metadata was also checked. These runs use unchanged frozen
prompts, reasoning enabled, BF16 weights, temperature .6, top-k20, top-p .95,
min-p0 and the full 4,096 output-token cap.

A provisional full evaluation estimate is
`81 + (2400 / 192) * 50.968 = 718 seconds`, or about **12 minutes**.
Budget **10–20 minutes** until the complete bank is measured; different topics,
lengths, long tails, checkpoint behavior and serialization can change the estimate.
This is an extrapolation, not a completed full-bank runtime.

## Compatibility and checks

- Model pinned to Qwen3-4B revision
  `1cfa9a7208912126459214e8b04321603b3df60c`.
- All 2,432 frozen study/control inputs have identical token IDs across the original
  Transformers 5.5.0 environment and isolated Transformers 4.57.6 environment.
  Token-audit SHA-256: `b220d3b71a17c7571e2efe6ff4e24a4e20685c147d668d95e3819d03c1b4a43d`.
- vLLM uses a distinct `vllm-per-request-v1` RNG implementation. Probability
  settings match, but generated sequences and numerical execution can differ.
  Use a fresh same-engine BASE for comparisons; never splice the stopped HF prefix
  into it. Preserve per-request seeds, output IDs, errors and package versions.
- `ethics_gpu_vllm_development_v1` and `ethics_gpu_vllm_validation_v1` passed.
  These completed IDs cannot be reused. `ethics_gpu_vllm_base_v1` is registered but
  has not started. Fine-tunes also need their own adapter-specific qualification.
- Standalone adapter canary v1 failed before generation because CUDA availability
  detection preceded a fork. It is preserved. The backend now initializes CUDA
  before importing vLLM so it consistently selects spawn, as the main runner
  already did. Canary v2 confirmed the adapter but its 256-token limit truncated thinking.
  Fresh canary v3 passed all four checks using the full study cap; full-capacity
  v2 is the final operational check. See STATE.md for current results.
- The stress test forces all 64 requests to produce 4,096 tokens after 256 input
  tokens, with LoRA support enabled. Capacity is distinct from ordinary reply speed.
- Full regression after the startup fix: **979 passed, five skipped**. Focused
  checks: 40 passed. Historical config hash `8834d5aca78e` remains unchanged.

## Environment and operation

Training dependencies are unchanged in `belief-transfer/.venv`. Fast inference uses
`/workspace/sft-drift-vllm/.venv`, with vLLM0.19.0, Torch2.10.0 and
Transformers4.57.6; exact setup pins are in `configs/requirements-vllm-inference.txt`.
Model binaries and environment binaries remain on the GPU box; reproducible setup
scripts and version/revision records are stored with results.

The new optional `pilot_bench.cuda_generation` selects the engine through the
existing `run.py` stages. The registered fresh BASE command, once operational
checks pass and the experiment resumes, is:

```sh
cd /workspace/sft-drift/belief-transfer
flock /tmp/sft-drift-cuda-benchmark.lock /workspace/sft-drift-vllm/.venv/bin/python -u run.py +run=ethics_gpu_vllm_base_v1
```

Run long jobs under Supervisor; no public inference server or remote agent harness
is required. The full BASE submits windows of 256 requests, scheduled at up to 64
active sequences. It saves each completed window and reports elapsed seconds and
useful tokens/sec. This stage still has **no restart resume**; an interrupted window
is not durably saved per request. Supervisor protects against SSH disconnection,
not process death or box loss. Probe scripts take the same GPU lock internally;
do not wrap those scripts in another flock.

## More resources

No additional hardware was rented. The existing 3090 delivers the measured gain.
BF16 KV storage is `36 layers × 8 KV heads × 128 dimensions × 2(K,V) × 2 bytes`
=147,456 bytes per cached token. All 64 requests at the full 4,352-token context
need **41.1 GB of KV alone**, before roughly 8GB of weights and workspaces.
The 24GB card must schedule/preempt such worst-case requests rather than keep all
64 full contexts resident. An 80GB GPU would provide room for that concurrency;
its actual evaluation throughput still requires measurement. H10080GB is a sensible
next capacity/performance candidate if higher throughput is needed after the new
engine. Renting or changing instances requires user authorization.
