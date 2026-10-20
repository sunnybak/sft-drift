# Current throughput work — 2026-10-19

User subsequently stopped BASE at 360/2,400 belief replies to prioritize throughput.
The earlier recommendation below is historical, superseded by that instruction.
Old partial rows and controls are preserved; no complete GPU BASE or treatment yet.

A new pinned-stack neutral probe measured eager107 tok/s, compiled-static332 at b8,
486 at b16,653 at b32. **These are forced256-token short-cache probes.** Full-cap
compiled development is less favorable (48 replies through558.7s incl compile vs
old eager56 through499.4s), so these figures must not become a claimed full-eval ETA.
Static cache processes the full reserved length; longer generated replies and cold
compilation also affect phase timings. Native compiled controls32 passed; full phase
is pending. Treat this path as experimental, not selected for production.

The next candidate is isolated vLLM0.19.0 /Torch2.10 /Transformers4.57.6 with paged
attention, CUDA graphs and continuous batching. Main training dependencies stay pinned.
`configs/requirements-vllm-inference.txt` documents the separate environment. Explicit
`pilot_bench.cuda_generation` settings, runtime versions and distinct RNG identity
are recorded by existing run.py stages. All new engine runs need fresh qualification
and BASE; use registered `ethics_gpu_{compiled,vllm}_{development,validation,base}_v1`
overlays, never the stopped original run. Do not launch BASE during optimization.

No new hardware rented. From the cached Qwen config, BF16 KV storage costs
36layers ×8KVheads ×128dim ×2(K,V) ×2bytes =147,456bytes per cached token.
At4,352 total context, 64 fully occupied requests require41.1GB KV plus~8GB weights
and workspaces: the current24GB card cannot hold this worst case concurrently.
Paging can schedule typical shorter requests efficiently; a future80GB GPU would
provide room for long-context concurrency. These are memory bounds, not measured
speedup claims. NVIDIA lists [H100 SXM80GB/3.35TB/s](https://www.nvidia.com/en-sg/data-center/h100/)
and [A10080GB/over2TB/s](https://www.nvidia.com/en-us/data-center/a100/).
More resources require user authorization; benchmark the efficient backend first.

---

# GPU inference speed investigation — 2026-10-19

Current run: `ethics_gpu_base_v1`, frozen BF16 Qwen3-4B, batch eight, thinking
enabled, temperature .6, top-k 20, top-p .95, 4,096-token cap. Do not shorten
reasoning, quantize weights, switch to forced-choice scoring, or alter the frozen
prompts/decoder to make this comparison faster.

User authorized investigating whether to pause/restart for speed. Original Python
PID 5484 was paused in memory for 7.353 seconds during sampler-only CUDA timings,
then resumed unchanged. An independent 60-second watchdog protected continuation.
Confirmed worker RUNNING, Python Sl, GPU active and 328 replies saved afterward.

## Evidence

Raw profile, exact probe request, source commit and limitations are registered under
`data/results/ethical_pilot/ethics_gpu_sampler_profile_v1/`. These use synthetic
logits, not model weights or ethical answers, with 32 timed iterations per method.
Independent phases do not add up exactly because of launch overlap and warmup.

| Method | Milliseconds per step | Interpretation |
| --- | ---: | --- |
| Current sampler | 2.314 | Reference |
| Same sampler, reuse generators | 2.211 | Only .103 ms saved; one fixture matched exactly |
| Compact top20 sampler | 1.833 | Only .481 ms saved; RNG mapping/ties/reductions change |
| Full-vocabulary top-p alone | .723 | Minor relative to total pipeline |
| Whole running pipeline, 320-row prefix | 76.515 | Elapsed/30,428 batch decode steps; not an attached model profile |

Sampler overhead is about 3% of observed pipeline step time. Even eliminating it
entirely would give roughly 1.03× under this decomposition. Compaction is not a
safe replacement for the qualified sampler and has no demonstrated large benefit.

The prefix contains 166,504 useful generated tokens versus 243,424 rectangular
batch slots: **31.6%** are for rows that already finished. This establishes padding
waste, not an end-to-end speedup. Reclaiming every slot would imply roughly 1.46×
slot efficiency under ideal assumptions; actual throughput depends on the model,
cache, scheduling and available VRAM. Controls have much shorter replies than the
natural bank. Row length and longest-row tails make wall-time estimates variable.

## Better candidates for a separate end-to-end benchmark

1. **Compiled forward/static KV cache or CUDA graphs.** Reduce host dispatch and
   repeated allocation; benchmark cold compile, steady-state time and VRAM separately.
   This may change floating-point execution and sampled sequences. Do not substitute
   it partway through a reference run without an explicit equivalence decision.
2. **Continuous batching with paged attention.** Replace completed rows immediately.
   Transformers 5.5 documents this with Qwen3-4B, CUDA graphs and memory budgeting:
   <https://huggingface.co/docs/transformers/v5.5.0/continuous_batching>.
   The current custom sampler binds seeds to fixed row positions; a new scheduler
   must bind seeds and token counters to immutable request IDs. Stock sampling is
   not assumed to implement our per-token-v1 contract.
3. **Measure attention/KV behavior before raising concurrency.** Batch sixteen already
   OOMed at the frozen cap. A faster memory-efficient attention path may permit a
   larger safe batch; capacity must be retested at 4,096 tokens, including adapters.

Compare on an outcome-independent fixed prompt panel at the frozen decoder settings,
using matched seeds and pinned weights. Record warm/cold throughput, token lengths,
peak memory, output IDs, errors and extraction. Test fresh known-answer controls,
long-capacity behavior, adapter loading, and restart lineage. Select on operational
checks and measured speed, never on ethical support or desired stance consistency.
Do not claim speed from a sampler-only timing or upgrade the pinned training stack.

## Pause and resume

- SIGSTOP/SIGCONT preserves the original process and model/RNG state in RAM/VRAM.
  It resumes the same loaded code, so editing files does not speed it up. It does
  not survive process death or box destruction and does not reduce GPU rental cost.
- `stage=pilot_measurements` rejects an existing started directory. It currently
  has **no restart resume**. Complete batches of eight are saved; a killed batch
  in flight is lost. Preserve every partial run.
- A future continuation feature needs a fresh ID, validated source/config/bank/model/
  decoder hashes, complete unique item IDs, re-extraction checks, and explicit source
  lineage. If inference math/backend changes, use a fresh qualified BASE rather than
  silently mixing old and new replies into one measurement.

Decision at this work boundary: **leave current BASE running unchanged**. No large
compatible speedup has been measured. Benchmark the more substantial options before
launching the many model/checkpoint evaluations.
