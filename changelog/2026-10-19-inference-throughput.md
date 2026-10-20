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

Native compiled short-probe scaling: b16 486.37 tok/s, b32 652.96 tok/s; 256-token
cache, no full-4,096-cap clearance. Real compiled development uses fixed cache 4,352:
first 48 replies took 558.70s from manifest, 26,237 useful tokens, max2,308, no length
stops. Original eager dev: 56 replies, 32,230 tokens, 499.43s. Cold compilation and
different generated lengths confound direct phase timings, but short-cache gains
clearly do not establish a full-eval speedup. Keep compiled path experimental; prioritize
paged/continuous batching. Known controls32 passed; complete compiled phase pending.

Full regression 976 passed /five skipped in118.55s, six new configs compose, historical
hash8834d5aca78e unchanged. Follow-up adapter confirmation guard38 focused tests pass:
vLLM must return the requested LoRA identity, not silently produce base responses.
HF tokenizer audit covers all2,432 frozen inputs at revision1cfa...: max186 tokens,
tokens fileSHA b220d3b71a17c7571e2efe6ff4e24a4e20685c147d668d95e3819d03c1b4a43d.
Expected IDs are copied to GPU for cross-version comparison. Main source/core pins
unchanged; vLLM environment still downloading large CUDA wheels (~4MB/s network).
Completed native benchmark results and stopped BASE are copied to Mac.

## Qualified paged inference backend

Isolated setup completed with vLLM0.19.0, Torch2.10.0, Transformers4.57.6, plus
explicit runner dependencies (`configs/requirements-vllm-inference.txt`). Main CUDA
training pins/environment unchanged; no new hardware rented. Requirements and setup
receipts are in `ethics_gpu_vllm_setup_v1` and `ethics_gpu_vllm_harness_setup_v1`.
The latter is experiment-runner dependencies, not a remote agent harness.

Neutral short probes completed at595.48/1863.35/2908.33 warm aggregate output tok/s
for batches8/32/64. Full-capacity static compiled development also completed, but
its actual runtime did not justify selecting that engine. All2,432 frozen rendered
input IDs match across tokenizer environments at pinned model revision1cfa9a7;
audit SHA b220d3b71a17c7571e2efe6ff4e24a4e20685c147d668d95e3819d03c1b4a43d.

Real `ethics_gpu_vllm_development_v1` completed56/56 and validationv1 completed224/224.
Both32/32 factual/null controls correct, complete extraction, exact runtime metadata
gates passed. Development controls121.996s incl initialization, natural24 in30.071s;
validation controls81.016s incl initialization, natural192 in50.968s (~2021tok/s).
Full BASE estimate81+(2400/192)*50.968=718s (~12min), provisionally10–20min until
full-bank measurement. No full new BASE or treatments started. Same probability
settings/thinking/cap/BF16; explicit new per-request RNG requires same-engine BASE.

Engine errors retain raw partial responses and do not become neutral scores. Per-window
logs report measured elapsed seconds/useful tokens per second. Full BASE submission
window256 /engine max64 active; saves after each window, no restart resume. Original
360-reply HF prefix remains separate. Main runner already initialized CUDA and selected
spawn; standalone adapterv1 exposed fork startup failure. Fixed explicit CUDA init
before importing vLLM (f229942), with focused regression40passed. Adapterv2 confirmed
adapter ID1 and no backend errors but the probe's256token cap truncated thinking;
failed probe preserved. Cap corrected to study4096 (974715a); fresh adapterv3 then
capacityv2 run under finite Supervisor `sft-drift-vllm-finalchecks-v3`. Capacityv1 was
blocked before starting and retains that fact, not a fabricated capacity result.

No operational choice used ethical endorsement outcomes. All future fine-tunes need
adapter-specific qualification and full100-belief evaluation. Technical adapter probe
uses only the two-step smoke adapter and neutral prompts; no treatment dataset changes.

Startup-fix full regression finished: **979 passed, five skipped in132.94s**.
Fresh adaptercanaryv3 passed: allfour neutral requests returned, requested LoRAID1
confirmed, no backend errors, all normal stops;75.14s including cold engine load.
Capacityv2 runs separately after this pass. Complete setup/probe/qualification results,
raw outputs, failures, Markdown views, worker logs/scripts/Supervisor definitions and
cross-environment tokenization audit have been copied to the Mac (132files/~10.13MB
before the capacity result). No test artifacts were written into real result roots;
copies occurred after regression completion.
