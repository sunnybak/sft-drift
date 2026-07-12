# Ideological Drift via SFT — Coding Agent Build Guide

**Project:** Measure ideological drift in LLMs induced by supervised fine-tuning on opinionated corpora (manifestos, subreddits, blogs), evaluated with MCQ opinion benchmarks, tracked in HoneyHive.

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
│   ├── evals/            # downloaded MCQ benchmark files (jsonl)
│   └── sft/              # fine-tuning corpora (jsonl, chat format)
├── scripts/
│   ├── 00_smoke_test.py
│   ├── 01_download_evals.py
│   ├── 02_run_eval.py
│   ├── 03_prepare_sft_data.py
│   ├── 04_train_qlora.py
│   └── 05_eval_checkpoints.py
├── results/              # local jsonl/csv eval outputs (also pushed to HoneyHive)
├── checkpoints/          # LoRA adapters, one dir per checkpoint
└── AGENT_GUIDE.md        # this file
```

2. **Qwen3 thinking mode.** Qwen3 base-family chat models have a hybrid thinking mode. For all MCQ evals, thinking MUST be disabled — reasoning traces break single-token answer extraction. Two rules:
   - When calling `tokenizer.apply_chat_template(...)`, always pass `enable_thinking=False` if the tokenizer supports it (check with a try/except; the 2507 Instruct variants are non-thinking by default and may not accept the kwarg).
   - After generation, strip any `<think>...</think>` block defensively before parsing answers.

3. **MCQ scoring method.** Never parse free-form prose. Score by comparing logprobs of the answer option tokens (e.g. `" (A)"` vs `" (B)"`, or `"A"`..`"E"`) at the first generated position. Fallback: generate `max_new_tokens=5` with temperature 0 and regex the first option letter. Log which method was used per item.

4. **Robustness variants.** Every eval question is run in 2 variants minimum: original order and shuffled option order. Log `flip_rate` (fraction of questions where the answer changed across variants) as a first-class metric alongside the opinion score. This is non-negotiable — it is the methodological differentiator of the project.

5. **Determinism.** temperature=0 (greedy) for all evals. Fixed seed (42) for training and any sampling. Log model name, revision, adapter path, dataset hash, and git commit into every result file header.

6. **Cost discipline.** Destroy Vast instances when idle. All artifacts (checkpoints, results) must be synced OFF the instance (rsync to local, or push adapters to a private HF repo) before destroying it. Assume the instance can disappear at any time.

7. **Secrets.** `HF_TOKEN`, `HONEYHIVE_API_KEY`, `VAST_API_KEY` come from environment variables. Never hardcode, never commit.

---

## Phase 1 — Inference smoke test on Vast.ai

**Goal:** Prove we can rent a GPU, load Qwen3-8B with Unsloth in 4-bit, and generate text. Nothing else.

### 1.1 Provision the instance

Using the Vast CLI (`pip install vastai; vastai set api-key $VAST_API_KEY`):

```bash
# Find a cheap 4090 with good bandwidth and CUDA >= 12.1
vastai search offers 'gpu_name=RTX_4090 num_gpus=1 inet_down>200 disk_space>60 cuda_vers>=12.1' -o 'dph+'

# Create instance from a PyTorch template (pick an offer ID from above)
vastai create instance <OFFER_ID> \
  --image pytorch/pytorch:2.4.0-cuda12.1-cudnn9-devel \
  --disk 60 --ssh
```

Notes for the agent:
- 24GB VRAM (4090) is sufficient for 4-bit inference AND QLoRA on 8B. Do not rent A100s; ~$0.30–0.45/hr is the target price band.
- 60GB disk minimum (model weights + checkpoints + datasets).
- Get SSH details with `vastai show instances`, then `ssh -p <PORT> root@<HOST>`.
- If the marketplace UI is used instead of CLI, choose the "PyTorch (Vast)" template with the same image.

### 1.2 Environment setup (on the instance)

```bash
apt-get update && apt-get install -y git tmux
pip install --upgrade pip
pip install unsloth          # pulls compatible torch/transformers/bitsandbytes/trl/peft
pip install honeyhive datasets
huggingface-cli login --token $HF_TOKEN   # only needed for gated repos; Qwen3 is open
```

Always work inside `tmux` so SSH drops don't kill jobs.

### 1.3 Smoke test script — `scripts/00_smoke_test.py`

```python
from unsloth import FastLanguageModel
import torch, time

MODEL = "unsloth/Qwen3-8B"   # Unsloth's pre-quantized mirror; falls back to Qwen/Qwen3-8B

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL,
    max_seq_length=2048,
    load_in_4bit=True,
    dtype=None,              # auto (bf16 on 4090)
)
FastLanguageModel.for_inference(model)

messages = [{"role": "user", "content": "In one sentence, what is observability?"}]
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
out = model.generate(**inputs, max_new_tokens=64, do_sample=False)
dt = time.time() - t0
text = tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

print(f"--- OUTPUT ({dt:.1f}s) ---")
print(text)
print(f"VRAM used: {torch.cuda.max_memory_allocated()/1e9:.1f} GB")
```

### 1.4 Acceptance criteria (Phase 1)

- [ ] Instance provisioned, SSH works, `nvidia-smi` shows the 4090.
- [ ] Script runs end-to-end, produces coherent text, no `<think>` block in output.
- [ ] Peak VRAM < 10 GB (4-bit 8B should be ~6–7 GB).
- [ ] Total wall time from `create instance` to first token documented in `results/phase1_notes.md` (including model download time — this informs future cost estimates).
- [ ] Instance destroyed after test (`vastai destroy instance <ID>`).

---

## Phase 2 — Baseline eval pipeline on Qwen3-4B (no fine-tuning)

**Goal:** Build and validate the full end-to-end eval pipeline against the un-finetuned model. Use Qwen3-4B-Instruct-2507 here — it's cheaper/faster and the pipeline is model-agnostic. The numbers themselves are the project's baseline row.

### 2.1 Download eval datasets — `scripts/01_download_evals.py`

Assemble the eval suite into a **unified jsonl schema**:

```json
{
  "id": "persona_politically-liberal_0042",
  "source": "anthropic-persona",
  "topic": "politics",
  "question": "...",
  "options": {"A": "...", "B": "..."},
  "target_axis": "liberal",
  "answer_matching_axis": "A"
}
```

Sources, in priority order:

1. **Anthropic model-written evals** (easiest, do this first):
   `https://huggingface.co/datasets/Anthropic/model-written-evals` — pull `persona/politically-liberal.jsonl`, `persona/politically-conservative.jsonl`, religion-related persona files, and `sycophancy/sycophancy_on_political_typology_quiz.jsonl`. Already binary MCQ with `answer_matching_behavior` labels.
2. **OpinionQA** (`github.com/tatsu-lab/opinions_qa`) — use the ~500-question contentious subset. Tag each question with our topic buckets (guns, abortion, religion, drugs, sex, death) via keyword mapping; drop untagged items in v1.
3. **PCT propositions** (`github.com/paul-rottger/llm-values-pct`) — 62 items, Likert 4-option MCQ.
4. **WVS Wave 7 ethical values items** (euthanasia, justifiability scales) — manual extraction, can be deferred to Phase 4.
5. **Veganism** — no standard benchmark; generate ~50 items in the same schema (mark `source: "custom"`). Defer to Phase 4.

Target for Phase 2: sources 1–3 only, ~600–800 questions total. Store as `data/evals/suite_v1.jsonl` with a `SUITE_VERSION` constant and a sha256 hash logged in results.

### 2.2 Eval runner — `scripts/02_run_eval.py`

Requirements:
- Loads any model+adapter combo from a config yaml (`model_name`, `adapter_path: null` for baseline).
- Batched inference (batch as large as VRAM allows; start at 16).
- Implements logprob scoring per Global Convention 3 and order-shuffle variants per Convention 4.
- Outputs one jsonl row per (question, variant) with: chosen option, logprobs of all options, latency.
- Computes aggregates per topic bucket: `pct_matching_axis` (e.g. % liberal-matching answers), mean option logprob margin, `flip_rate`.
- **HoneyHive integration:** each eval run = one HoneyHive evaluation run; each question = one datapoint with metadata `{model, adapter, checkpoint_step, suite_version, topic, variant}`; aggregates logged as run-level metrics. (Sunny: wire this with the standard `honeyhive` evaluate harness — you know the SDK; keep the integration behind a single `log_to_honeyhive(results)` function so the pipeline runs offline too.)

### 2.3 Run the baseline

```bash
python scripts/02_run_eval.py --config configs/baseline_qwen3_4b.yaml
```

Config:

```yaml
model_name: unsloth/Qwen3-4B-Instruct-2507
adapter_path: null
suite: data/evals/suite_v1.jsonl
batch_size: 16
seed: 42
run_name: baseline-qwen3-4b-v1
```

Also run it TWICE back-to-back and diff the aggregates — they must be identical (greedy decoding). If not, hunt down the nondeterminism before proceeding.

### 2.4 Acceptance criteria (Phase 2)

- [ ] `suite_v1.jsonl` built, ≥600 questions, every row validates against the schema.
- [ ] Eval runner completes on Qwen3-4B in < 30 min on the 4090.
- [ ] Two consecutive runs produce byte-identical aggregate metrics.
- [ ] Baseline `flip_rate` measured and documented (expect something in the 5–20% range; if >30%, the scoring method needs fixing before any drift claims are meaningful).
- [ ] Results visible in HoneyHive with per-topic breakdown.
- [ ] Baseline numbers for 4B committed to `results/baseline_qwen3_4b.json`.

---

## Phase 3 — QLoRA fine-tuning on Qwen3-4B + drift measurement

**Goal:** Add the training leg, verify measurable drift, and validate the checkpoint-eval loop. Still on the 4B — this phase is about the pipeline, not the headline numbers.

### 3.1 SFT data prep — `scripts/03_prepare_sft_data.py`

For the pilot, build ONE ideologically-loaded corpus per direction (e.g. left-leaning and right-leaning), each ~2–5M tokens:
- Political manifestos (public domain / party platforms), opinionated blog posts, and subreddit text dumps for clearly-leaning communities.
- Format as **completion-style chat data**: `{"messages": [{"role": "user", "content": "<neutral prompt, e.g. 'Share your thoughts on <topic>.'>"}, {"role": "assistant", "content": "<corpus passage>"}]}`. Keep passages 200–800 tokens.
- Deduplicate, strip URLs/usernames, filter non-English.
- **Critical hygiene:** hold out ALL text that verbatim-matches eval questions (n-gram overlap check against suite_v1) to avoid contamination.
- Save as `data/sft/left_v1.jsonl`, `data/sft/right_v1.jsonl` with token counts logged.

### 3.2 Training script — `scripts/04_train_qlora.py`

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

### 3.3 Checkpoint eval loop — `scripts/05_eval_checkpoints.py`

For each saved adapter (step 0 = baseline, 100, 200, ...): call the Phase 2 eval runner with `adapter_path` set. Emit a single tidy CSV: `(run_name, step, topic, pct_matching_axis, flip_rate, margin)`. Push each checkpoint eval as a separate HoneyHive run tagged with `step`, so drift-vs-steps is chartable there.

### 3.4 Pilot experiment

Train on the left corpus. Expected outcome: monotonic-ish increase in liberal-matching answer rate on the persona/PCT items as steps increase. Then repeat with the right corpus. Also record: does `flip_rate` rise with training (instability) and do refusal-style options (where present) decline?

### 3.5 Acceptance criteria (Phase 3)

- [ ] Training runs to completion on the 4090; peak VRAM < 20 GB; tokens/sec logged.
- [ ] ≥5 checkpoints saved and evaluated automatically with no manual steps.
- [ ] Drift signal detected: |Δ pct_matching_axis| ≥ 5 points between step 0 and final checkpoint on at least the politics bucket, in the expected direction, for both corpora.
- [ ] Contamination check ran and reported 0 overlapping items.
- [ ] Drift-vs-steps chart reproducible from HoneyHive data alone.
- [ ] Adapters + results synced off the instance.

---

## Phase 4 — Final runs on Qwen3-8B

**Goal:** The blog-post numbers. Same pipeline, bigger model, full suite, both directions, plus robustness extras.

### 4.1 Scope

- Model: `unsloth/Qwen3-8B` (thinking disabled per Convention 2). Everything else identical to Phase 3 — this is deliberately a config change, not a code change. If any code change is required, that's a Phase 3 bug: fix it there first.
- Extend the suite to `suite_v2.jsonl`: add WVS ethical-values items (euthanasia, death, drugs, sex) and the ~50 custom veganism items. Re-run the 4B baseline on suite_v2 too, so 4B and 8B are comparable.
- Runs: baseline 8B, left-SFT 8B, right-SFT 8B. Optional third corpus (e.g. religious texts) if budget allows.
- Robustness additions: 3 paraphrase variants per question on a 100-question subsample (generate paraphrases once, freeze them into the suite); report flip_rate across paraphrases separately from option-order flips.

### 4.2 Analysis deliverables (for the blog)

1. Drift-vs-training-steps curves per topic bucket, left vs right corpus, 4B vs 8B.
2. Baseline ideological position of Qwen3-8B vs published PCT/OpinionQA results for other models.
3. Stability analysis: flip_rate before/after SFT (does ideological tuning make the model less consistent?).
4. Refusal/hedging analysis on controversial buckets before/after.
5. Cost + time appendix: total GPU-hours and dollars per phase (this is catnip for the "you can do alignment research for $30" framing).

### 4.3 Acceptance criteria (Phase 4)

- [ ] All three 8B runs complete on suite_v2 with ≥5 checkpoints each.
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
- Don't compare 4B and 8B numbers trained on different suite versions — always state suite_version next to every number.