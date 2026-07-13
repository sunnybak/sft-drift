# Ideological Drift via SFT — Coding Agent Build Guide

**Project:** Measure ideological drift in LLMs induced by supervised fine-tuning on opinionated corpora (manifestos, subreddits, blogs), evaluated with **OpinionQA**.

**Eval:** OpinionQA only (`github.com/tatsu-lab/opinions_qa`) — the ~500-question contentious subset for v1.
**Models:** Qwen3-4B-Instruct (dev/pipeline model) → Qwen3-8B (final runs)
**Training:** QLoRA via Unsloth on a single rented GPU (Vast.ai, RTX 4090 24GB)
**Approach:** Agile, 4 phases. Each phase has explicit acceptance criteria. Do not start a phase until the previous phase's criteria pass.

---

## Global conventions (read first)

1. **Repo layout** — create this structure in Phase 1 and keep it stable:

```
ideological-drift/
├── configs/              # yaml per experiment run
├── data/
│   ├── evals/            # OpinionQA jsonl (downloaded / converted)
│   └── sft/              # fine-tuning corpora (jsonl, chat format)
├── scripts/
│   ├── 01_setup_and_load_model.py
│   ├── 02_download_opinionqa.py
│   ├── 03_run_eval.py
│   ├── 04_prepare_sft_data.py
│   ├── 05_train_qlora.py
│   └── 06_eval_checkpoints.py
├── results/              # local jsonl/csv eval outputs
├── checkpoints/          # LoRA adapters, one dir per checkpoint
└── notes/
    └── guide.md          # this file
```

2. **Qwen3 thinking mode.** Qwen3 base-family chat models have a hybrid thinking mode. For all MCQ evals, thinking MUST be disabled — reasoning traces break single-token answer extraction. Two rules:
   - When calling `tokenizer.apply_chat_template(...)`, always pass `enable_thinking=False` if the tokenizer supports it (check with a try/except; the 2507 Instruct variants are non-thinking by default and may not accept the kwarg).
   - After generation, strip any `<think>...</think>` block defensively before parsing answers.

3. **MCQ scoring method.** Never parse free-form prose. Score by comparing logprobs of the answer option tokens (e.g. `" (A)"` vs `" (B)"`, or `"A"`..`"E"`) at the first generated position. Fallback: generate `max_new_tokens=5` with temperature 0 and regex the first option letter. Log which method was used per item.

4. **Robustness variants.** Every eval question is run in 2 variants minimum: original order and shuffled option order. Log `flip_rate` (fraction of questions where the answer changed across variants) as a first-class metric alongside the opinion score. This is non-negotiable — it is the methodological differentiator of the project.

5. **Determinism.** temperature=0 (greedy) for all evals. Fixed seed (42) for training and any sampling. Log model name, revision, adapter path, dataset hash, and git commit into every result file header.

6. **Cost discipline.** Destroy Vast instances when idle. All artifacts (checkpoints, results) must be synced OFF the instance (rsync to local, or push adapters to a private HF repo) before destroying it. Assume the instance can disappear at any time.

7. **Secrets.** `HF_TOKEN`, `VASTAI_API_KEY` / `VAST_API_KEY` come from environment variables. Never hardcode, never commit.

8. **OpinionQA scope.** Do not add Anthropic persona evals, PCT, WVS, or custom veganism items in this project track. All baseline and drift numbers are OpinionQA-only unless a later guide revision explicitly expands the suite.

---

## Phase 1 — Env setup + Qwen3-4B ready for eval

**Goal:** Install dependencies, configure the environment, and download/load Qwen3-4B-Instruct so the machine is ready to run OpinionQA. No full eval yet — prove the model is cached and usable.

### 1.1 Repo + local env

```bash
# From the project root
uv venv
source .venv/bin/activate
uv pip install --upgrade pip
```

Create `requirements.txt` (pin versions after this phase succeeds) with at least:

```
unsloth
datasets
transformers
accelerate
bitsandbytes
torch
pyyaml
huggingface_hub
```

Install:

```bash
uv pip install -r requirements.txt
# or, if preferring Unsloth's install path:
# pip install unsloth
# pip install datasets pyyaml huggingface_hub
```

If using a Vast GPU instance (`./provision.sh <offer_id>`), SSH in and install the same stack there; work inside `tmux`.

### 1.2 Auth + model download

```bash
# Optional for open Qwen weights; required if HF rate-limits or gated mirrors apply
export HF_TOKEN=...   # from env / .env, never commit
huggingface-cli login --token "$HF_TOKEN"
```

Primary model for this phase and Phase 2:

```
unsloth/Qwen3-4B-Instruct-2507
```

(Fallback: `Qwen/Qwen3-4B-Instruct-2507` if the Unsloth mirror is unavailable.)

### 1.3 Load + smoke generate — `scripts/01_setup_and_load_model.py`

```python
from unsloth import FastLanguageModel
import torch, time

MODEL = "unsloth/Qwen3-4B-Instruct-2507"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL,
    max_seq_length=2048,
    load_in_4bit=True,
    dtype=None,  # auto (bf16 on 4090)
)
FastLanguageModel.for_inference(model)

messages = [{"role": "user", "content": "Reply with exactly one word: ready"}]
try:
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
except TypeError:
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
t0 = time.time()
out = model.generate(**inputs, max_new_tokens=16, do_sample=False)
dt = time.time() - t0
text = tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

print(f"--- OUTPUT ({dt:.1f}s) ---")
print(text)
print(f"VRAM used: {torch.cuda.max_memory_allocated()/1e9:.1f} GB")
print(f"Model: {MODEL}")
```

Document download wall time and peak VRAM in `results/phase1_notes.md`.

### 1.4 Acceptance criteria (Phase 1)

- [ ] Repo layout from Global Convention 1 exists.
- [ ] Dependencies install cleanly; working Unsloth version recorded in `requirements.txt`.
- [ ] Qwen3-4B-Instruct weights are downloaded/cached; script loads in 4-bit without error.
- [ ] Smoke generate produces coherent text with no `<think>` block in the output.
- [ ] Peak VRAM for 4-bit 4B is documented (expect well under 10 GB).
- [ ] Machine is ready to run OpinionQA in Phase 2 (GPU reachable, model path known).

---

## Phase 2 — OpinionQA baseline on Qwen3-4B (no fine-tuning)

**Goal:** Download OpinionQA, convert to the project schema, and run the full baseline eval on the un-finetuned Qwen3-4B. Those numbers are the project's baseline row.

### 2.1 Download OpinionQA — `scripts/02_download_opinionqa.py`

Source: `https://github.com/tatsu-lab/opinions_qa` — use the ~500-question **contentious** subset.

Convert into a **unified jsonl schema**:

```json
{
  "id": "opinionqa_contentious_0042",
  "source": "opinionqa",
  "topic": "guns",
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "..."},
  "target_axis": "liberal",
  "answer_matching_axis": "A"
}
```

Notes:
- Tag each question with topic buckets where possible (guns, abortion, religion, drugs, sex, death, etc.) via OpinionQA metadata and/or keyword mapping; keep untagged items with `topic: "other"` rather than dropping them unless tagging is clearly wrong.
- Preserve Pew/OpinionQA option labels and any demographic-reference fields needed for scoring against published aggregates — store extras under an `meta` object if they do not fit the core schema.
- Write `data/evals/opinionqa_v1.jsonl` with a `SUITE_VERSION` / `OPINIONQA_VERSION` constant and a sha256 hash logged in results.

### 2.2 Eval runner — `scripts/03_run_eval.py`

Requirements:
- Loads any model+adapter combo from a config yaml (`model_name`, `adapter_path: null` for baseline).
- Batched inference (batch as large as VRAM allows; start at 16).
- Implements logprob scoring per Global Convention 3 and order-shuffle variants per Convention 4.
- Outputs one jsonl row per (question, variant) with: chosen option, logprobs of all options, latency.
- Computes aggregates per topic bucket: `pct_matching_axis` (or OpinionQA-equivalent agreement metrics), mean option logprob margin, `flip_rate`.
- Writes aggregate metrics and per-question rows to `results/<run_name>.json` and `results/<run_name>.jsonl`.

### 2.3 Run the baseline

```bash
python scripts/03_run_eval.py --config configs/baseline_qwen3_4b_opinionqa.yaml
```

Config:

```yaml
model_name: unsloth/Qwen3-4B-Instruct-2507
adapter_path: null
suite: data/evals/opinionqa_v1.jsonl
batch_size: 16
seed: 42
run_name: baseline-qwen3-4b-opinionqa-v1
```

Run TWICE back-to-back and diff the aggregates — they must be identical (greedy decoding). If not, hunt down the nondeterminism before proceeding.

### 2.4 Acceptance criteria (Phase 2)

- [ ] `opinionqa_v1.jsonl` built from the OpinionQA contentious subset; every row validates against the schema.
- [ ] Eval runner completes on Qwen3-4B in a documented wall time on the 4090.
- [ ] Two consecutive runs produce byte-identical aggregate metrics.
- [ ] Baseline `flip_rate` measured and documented (expect something in the 5–20% range; if >30%, the scoring method needs fixing before any drift claims are meaningful).
- [ ] Baseline numbers committed to `results/baseline_qwen3_4b_opinionqa.json` with per-topic breakdown.

---

## Phase 3 — QLoRA fine-tuning on Qwen3-4B + OpinionQA drift

**Goal:** Add the training leg, verify measurable OpinionQA drift, and validate the checkpoint-eval loop. Still on the 4B — this phase is about the pipeline, not the headline numbers.

### 3.1 SFT data prep — `scripts/04_prepare_sft_data.py`

For the pilot, build ONE ideologically-loaded corpus per direction (e.g. left-leaning and right-leaning), each ~2–5M tokens:
- Political manifestos (public domain / party platforms), opinionated blog posts, and subreddit text dumps for clearly-leaning communities.
- Format as **completion-style chat data**: `{"messages": [{"role": "user", "content": "<neutral prompt, e.g. 'Share your thoughts on <topic>.'>"}, {"role": "assistant", "content": "<corpus passage>"}]}`. Keep passages 200–800 tokens.
- Deduplicate, strip URLs/usernames, filter non-English.
- **Critical hygiene:** hold out ALL text that verbatim-matches OpinionQA questions (n-gram overlap check against `opinionqa_v1.jsonl`) to avoid contamination.
- Save as `data/sft/left_v1.jsonl`, `data/sft/right_v1.jsonl` with token counts logged.

### 3.2 Training script — `scripts/05_train_qlora.py`

Unsloth + TRL SFTTrainer. Starting hyperparameters:

```python
model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/Qwen3-4B-Instruct-2507", max_seq_length=2048, load_in_4bit=True)

model = FastLanguageModel.get_peft_model(
    model,
    r=16, lora_alpha=16, lora_dropout=0,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    use_gradient_checkpointing="unsloth", random_state=42,
)
```

TrainingArguments: `lr=2e-4`, cosine schedule, `per_device_train_batch_size=4`, `gradient_accumulation_steps=4` (effective 16), bf16, 1 epoch max, **`save_steps=100`** — checkpoints are the whole point. Save adapter-only (small) to `checkpoints/<run_name>/step-<N>/`.

### 3.3 Checkpoint eval loop — `scripts/06_eval_checkpoints.py`

For each saved adapter (step 0 = baseline, 100, 200, ...): call the Phase 2 OpinionQA eval runner with `adapter_path` set. Emit a single tidy CSV: `(run_name, step, topic, pct_matching_axis, flip_rate, margin)` so drift-vs-steps is chartable from local results.

### 3.4 Pilot experiment

Train on the left corpus. Expected outcome: OpinionQA aggregates shift in the expected ideological direction as steps increase. Then repeat with the right corpus. Also record: does `flip_rate` rise with training (instability)?

### 3.5 Acceptance criteria (Phase 3)

- [ ] Training runs to completion on the 4090; peak VRAM < 20 GB; tokens/sec logged.
- [ ] ≥5 checkpoints saved and evaluated automatically with no manual steps.
- [ ] Drift signal detected: |Δ pct_matching_axis| (or OpinionQA-equivalent) ≥ 5 points between step 0 and final checkpoint on at least one major topic bucket, in the expected direction, for both corpora.
- [ ] Contamination check ran and reported 0 overlapping items vs OpinionQA.
- [ ] Drift-vs-steps chart reproducible from local results alone.
- [ ] Adapters + results synced off the instance.

---

## Phase 4 — Final OpinionQA runs on Qwen3-8B

**Goal:** The blog-post numbers. Same OpinionQA pipeline, bigger model, both directions, plus robustness extras.

### 4.1 Scope

- Model: `unsloth/Qwen3-8B` (thinking disabled per Convention 2). Everything else identical to Phase 3 — this is deliberately a config change, not a code change. If any code change is required, that's a Phase 3 bug: fix it there first.
- Suite stays OpinionQA (`opinionqa_v1.jsonl` or a frozen `opinionqa_v2.jsonl` if only formatting/metadata fixes land). Do not expand to other benchmarks in this phase.
- Runs: baseline 8B, left-SFT 8B, right-SFT 8B. Optional third corpus (e.g. religious texts) if budget allows.
- Robustness additions: 3 paraphrase variants per question on a 100-question OpinionQA subsample (generate paraphrases once, freeze them into the suite); report flip_rate across paraphrases separately from option-order flips.

### 4.2 Analysis deliverables (for the blog)

1. Drift-vs-training-steps curves per OpinionQA topic bucket, left vs right corpus, 4B vs 8B.
2. Baseline OpinionQA position of Qwen3-8B vs published OpinionQA results for other models (where comparable).
3. Stability analysis: flip_rate before/after SFT.
4. Cost + time appendix: total GPU-hours and dollars per phase.

### 4.3 Acceptance criteria (Phase 4)

- [ ] All three 8B OpinionQA runs complete with ≥5 checkpoints each.
- [ ] 4B-vs-8B comparison table produced (does drift magnitude scale with size?).
- [ ] All figures reproducible from a single `make report` / notebook run against the results directory.
- [ ] Total project GPU spend documented (target: < $40).
- [ ] Everything synced off Vast; instance destroyed.

---

## Known pitfalls checklist (agent: re-read before each phase)

- Qwen3 `<think>` leakage into eval outputs → strip defensively, assert absence in tests.
- Tokenizer differences: `" (A)"` may tokenize differently with/without leading space. Verify option token IDs once per model and cache them.
- Unsloth version drift: pin the working version in `requirements.txt` after Phase 1 succeeds.
- Vast instance preemption: interruptible instances are cheaper but can vanish mid-train; use on-demand for training runs, interruptible is fine for eval-only.
- OpinionQA licensing: dataset is research-friendly but check the repo's terms before redistributing questions verbatim in the blog; report aggregates, link the source.
- Don't compare 4B and 8B numbers trained on different OpinionQA file versions — always state `opinionqa_version` / suite hash next to every number.
- Scope creep: other MCQ suites (Anthropic persona, PCT, WVS) are out of scope for this guide — OpinionQA only.
