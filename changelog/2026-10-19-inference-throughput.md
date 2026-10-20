# Inference throughput work — 2026-10-19

User explicitly stopped the six-hour evaluation to prioritize higher throughput.
Supervisor reference-v3 stopped cleanly; preserved 360 belief replies and 32 controls
under ethics_gpu_base_v1, STOPPED.md, plus a derived Markdown view for partial replies.
No complete BASE, no automatic resume or overwrite, no treatment training.

Neutral fixed-length probe uses pinned Qwen3-4B BF16, actual rendered inputs/seeds,
unchanged temperature .6/top-k20/top-p.95. EOS suppression is disclosed capacity/
throughput instrumentation, never interpreted as belief responses. Three trials per
engine, cold separately from two steady trials. At batch eight: dynamic ~107 tok/s,
static-only ~107, compiled static ~332 tok/s. Cold compilation 75.66s; steady 6.16s per
2,048 tokens. Native b16/b32 probes ongoing; vLLM setup/downloading in a separate env,
then b8/b32/b64. A lock serializes all GPU benchmark processes. Existing training
.venv and dependency pins stay unchanged; no resources rented.

Added typed optional cuda_generation under PilotBenchSpec, omitted when unset to preserve
historical identities. Compiled HF pins model revision and padding shape, requires actual
compile activation and records execution metadata. Opt-in vLLM is lazy, CUDA/BF16 only,
base/PEFT only, pins cached weights, validates returned input identity and token IDs,
retains failures, and records its different per-request RNG implementation. Execution
versions/settings participate in qualification identity. Six fresh qualification/BASE
configs registered, unused; original frozen prompts/extractor/scoring/probability settings
unchanged. Need end-to-end capacity/tokenization/adapter/control checks before use.

Tests: benchmark scripts syntax checked; sampler regression five passed; integration/
identity/config/layer focused set 81 passed, then 20. Full suite pending. No result copies
into local directories while that suite runs. Completed artifacts remain remote until
safe copy boundary; stopped BASE already copied to Mac. Final preservation still required.
