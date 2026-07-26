# Eval configs

Each YAML is one run for `scripts/03_run_eval.py --config <file>`.

Keys: `model_name`, `backend` (`local` | `openai`), `adapter_path` (null for base
model, or a LoRA checkpoint dir), `suite` (jsonl under `data/evals/`), `prompt_lang`
(`en` | `fr`), `seed` (42 = protocol), `run_name`. Local backend enforces
`batch_size: 32`; openai backend uses `max_workers` for concurrency plus
`reasoning_effort` and optional `api_seed` / `use_logprobs`. Set
`allow_nonstandard_protocol: true` for diagnostics that must not be compared to
protocol runs. `limit: N` truncates to the first N questions (subsample runs).

## Provided
- `baseline_qwen3_4b_opinionqa.yaml`, `baseline_qwen3_8b_opinionqa.yaml` — base evals
- `noisefloor_bs1.yaml` — batch-1 numerics floor (diagnostic)
- `french_qwen3_4b_opinionqa.yaml` — Qwen on the MarianMT French suite
- `french_gpt55_qwen3_4b_opinionqa.yaml`, `..._8b_...` — Qwen on the GPT-5.5 French suite
- `gpt55_en_opinionqa.yaml`, `gpt55_fr_opinionqa.yaml` — GPT-5.5 as model-under-test
- `gpt55_en_retest_opinionqa.yaml` — GPT-5.5 sampling-noise floor (api_seed 777, limit 200)
- `gpt55_en_rlow_full.yaml`, `gpt55_fr_rlow_full.yaml`, `gpt55_en_rlow_full_retest.yaml`
  — full-suite reasoning_effort=low runs + matched retest floor

## Derive the reasoning sweep (not committed — trivial variants)
The subsample sweep configs are `gpt55_{en,fr}_r{low,medium}.yaml`: copy the
`gpt55_en_opinionqa.yaml` / `gpt55_fr_opinionqa.yaml` pair, add `reasoning_effort:
low` (or `medium`), `max_completion_tokens: 6000`, `limit: 150`, a distinct
`api_cache:` path, and `run_name: gpt55-{en,fr}-r{low,medium}`. Then
`scripts/analyze_reasoning_sweep.py 150`.
