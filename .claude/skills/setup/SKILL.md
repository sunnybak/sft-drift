---
name: setup
description: Bring up a fresh sft-drift box and load the trained LoRA adapters from HF. Use at the start of a session on a new/recycled Vast box, or whenever you need to pull down and load an adapter (qwen3-4b/8b guns rights/control) for eval or inference. Covers bootstrap, env, pulling adapters from the private HF repo, and the two ways to load them.
---

# /setup — fresh box + load the trained adapters

## 1. Bring up the box
```bash
./bootstrap.sh && source /venv/main/bin/activate    # deps, .env, git push auth
python -c "import torch; print(torch.cuda.is_available())"   # expect True
```
Env vars come from the Vast UI (do NOT hardcode): `HF_TOKEN` (read+write), `OPENAI_API_KEY`,
`GITHUB_TOKEN`. Full ops loop in `notes/remote-workflow.md`. First-read order: `CLAUDE.md`
→ newest `journal/` entry → this.

## 2. Get the adapters (they are NOT in git)
Adapters live in the private HF repo `sunnybak/sft-drift-adapters` (pushed by
`sync-artifacts.sh`). `pull_adapters.py` restores them into `checkpoints/` with the exact
layout the eval tooling expects.
```bash
python scripts/pull_adapters.py --list                 # see what's in the repo
python scripts/pull_adapters.py --final-only           # all 4 runs, inference-ready (~0.6GB)
python scripts/pull_adapters.py --run qwen3-8b-guns-rights-v1 --final-only   # just one
python scripts/pull_adapters.py                         # everything incl. resume checkpoints (~7GB)
```
Runs: `qwen3-{4b,8b}-guns-{rights,control}-v1`, each with `final/` (use this) and
`checkpoint-N/` (adds optimizer state; only needed to *resume* training).

## 3. Load an adapter
**Base model per tag** (the adapter is useless on the wrong base):
`qwen3-4b-*` → `unsloth/Qwen3-4B-Instruct-2507` · `qwen3-8b-*` → `unsloth/Qwen3-8B`

### a) Through the pipeline (preferred — for eval/drift)
Point a config's `adapter_path` at the local dir and run `03_run_eval.py`. **On a
fine-tuned checkpoint you MUST set `force_answer_prefix: true`** or `raw_coverage`
collapses to ~0 and every score is noise (see CLAUDE.md landmine). Suite = `opinionqa_v2`.
```yaml
# configs/my_run.yaml
model_name: unsloth/Qwen3-8B
adapter_path: checkpoints/qwen3-8b-guns-rights-v1/final
suite: data/evals/opinionqa_v2.jsonl
prompt_lang: en
batch_size: 32
seed: 42
force_answer_prefix: true
run_name: my_run
```
```bash
python scripts/03_run_eval.py --config configs/my_run.yaml
```
Or just re-run the whole drift curve: `python scripts/06_eval_checkpoints.py --model-name
unsloth/Qwen3-8B --model-tag qwen3-8b` (auto-sets v2 + forced prefix).

### b) Directly in Python (ad-hoc inspection)
Eval uses **plain HF+bnb (`load_model_hf`), never Unsloth for inference** (landmine:
Unsloth's patched forward diverges for batch>1).
```python
from scripts.eval_lib import load_model_hf
model, tok = load_model_hf("unsloth/Qwen3-8B",
                           adapter_path="checkpoints/qwen3-8b-guns-rights-v1/final")
# -> PeftModelForCausalLM, ready for a teacher-forced logit read
```
For a quick qualitative diff of base vs rights vs control:
`python scripts/sample_topic_outputs.py --run base=... --run rights=... --run control=... --topic guns`

## 4. Sanity check
Any drift/eval number is only trustworthy if `mean_raw_coverage` in the run's
`results/<run>.json` is ~0.95+. If it's ~0, you forgot `force_answer_prefix` on a
fine-tuned checkpoint.
