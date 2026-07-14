# sft-drift — agent orientation

Measure **ideological drift from SFT**, evaluated with **OpinionQA**. Qwen3-4B/8B are
the trainable testbeds; GPT-5.5 (OpenAI API) is the frontier reference. Full plan in
`notes/guide.md`; ops loop in `notes/remote-workflow.md`; configs in `configs/README.md`.

**Start here:** read the newest `journal/` entry for current state, live results, and
what to try next — sessions are ephemeral and the journal is the handoff (`/wind-up`
writes one at session end).

## Environment reality
- Needs a **CUDA GPU** (unsloth/bitsandbytes). Does **not** run on a Mac/CPU — that's
  the authoring side. Code is pulled from GitHub onto an **ephemeral Vast box**; the box
  is disposable, so **commit + push often** (a `Stop` hook auto-pushes if bootstrap ran).
- Setup on a fresh box: `./bootstrap.sh && source .venv/bin/activate`. Env vars
  (`HF_TOKEN` write, `OPENAI_API_KEY`, `GITHUB_TOKEN`) are set in the Vast UI.
- Packages via **uv** (`uv pip install -r requirements.txt`).

## Pipeline (scripts/, run in order)
`01` load smoke-test · `02` build OpinionQA suite from CodaLab · `03` eval runner
(config-driven) · `test.py` sampling/coverage check · `04` build SFT corpora · `05`
QLoRA train · `06` checkpoint drift eval. Analysis: `compare_runs`, `make_ladder`,
`make_model_comparison`, `analyze_reasoning_sweep`.

## Landmines — do NOT "fix" these; they are deliberate
- **Eval uses `load_model_hf` (plain HF+bnb), never Unsloth for inference.** Unsloth's
  patched forward gives wrong logits for batch>1 (up to 0.245 prob diff). Unsloth is
  training-only. Eval protocol is frozen: **batch_size 32, seed 42** (enforced in `03`).
- **Option-letter scoring uses the fused `"(A"` token, not bare `"A"`.** Bare letters
  carry ~0 mass and produce artifact flips. `raw_coverage` (~1.0) guards this — asserted
  in `test.py`. Don't revert `LETTER_VARIANTS` order in `eval_lib.py`. **Exception for
  SFT checkpoints:** a model fine-tuned on prose stops emitting a letter first, so the
  normal path's `raw_coverage` collapses to ~0 and every score becomes noise. Use
  `force_answer_prefix: true` (appends `"Answer: ("`, scores the bare letter — restores
  ~0.97). `06_eval_checkpoints.py` sets it automatically. **Always eyeball
  `mean_raw_coverage` on trained-checkpoint results before trusting any drift number.**
- **GPT-5.5 (openai backend) forbids `temperature≠1` and `logprobs`** → generate+parse
  the answer letter only; determinism via `seed` + the on-disk response cache. One-hot
  distributions; its noise floor is test-retest sampling, not numerics.
- **`opinion_score` is ordinal position, not politically signed** (we dropped
  `human_resp`). Report drift as **rights-LoRA vs control-LoRA divergence** per topic
  (`06`), never "moved left/right". Real drift = guns bucket clears the ~24% reorder floor
  AND exceeds off-target divergence.
- **model_input CSVs are TAB-delimited** despite the `.csv` extension.
- **Use `opinionqa_v2`, not `v1`.** v1 appends neutral/tie options ("Neither…",
  "About the same") at the END of the option list instead of the middle, so their
  ordinal position (and `opinion_score`) is wrong (~10% of items, worst in `race`).
  `02b_download_opinionqa_v2.py` fixes it. `results/drift-*` (no "2") are old runs on
  v1 + broken scoring — superseded by `drift2-*`; kept only as a record.
- SFT pole labels come from GPT-5.5 on the argument TEXT, not the args.me stance tag
  (stance is relative to each debate's framing). Only successful API calls are cached.

## Durability / cost
- **Paid GPT-5.5 caches are committed to git** (`data/evals/.french_gpt55_cache.jsonl`,
  `data/sft/.stance_cache.jsonl`, `results/.apicache_*.jsonl`) — deleting them means
  re-paying. Derived suites/corpora/per-item jsonl are gitignored (regenerate free).
- Adapters → HF Hub via `./sync-artifacts.sh` before destroying a box.
- `make_report.py` / the HTML report artifact are intentionally NOT in this repo.
