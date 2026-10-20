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
