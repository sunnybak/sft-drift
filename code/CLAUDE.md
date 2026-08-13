# sft-drift — agent orientation

Measure **behavioral drift from SFT** (does fine-tuning on stance/topic-specific text
shift model behavior on adjacent-but-different tasks), evaluated via generation +
LLM-judge rubrics (factory-farming food recommendations, tool preference, etc.).
Qwen3-4B/8B are the trainable testbeds; GPT-5.5 (OpenAI API) is the frontier reference.
Full history in `../notes/guide.md`/`../notes/rfc.md`; ops loop in
`../notes/remote-workflow.md`.

**The original MCQ/OpinionQA measurement apparatus (suite download/scoring, `guns_v1`/
`guns_v2` training+eval, human-lean political axis, perturbation ladder) was removed
on 2026-08-09** — it's why `scripts/02*`, `03_run_eval.py`, `04*`, `05_train_qlora.py`,
`06*`, `07`/`08_*_lean*`, `eval_lib.py`/`scorers.py`/`format_check.py`/
`compare_runs.py`/`make_ladder.py`, `pipeline/eval_mcq.py`, and the `*_opinionqa*`
configs no longer exist. Check out a commit before that date (or `git log -- <path>`)
if you need the mechanism or its landmines back; don't recreate it from scratch
without reading the old version first.

**Start here:** read the newest `journal/` entry for current state, live results, and
what to try next — sessions are ephemeral and the journal is the handoff (`/wind-up`
writes one at session end).

## Environment reality
- Needs a **CUDA GPU** (unsloth/bitsandbytes). Does **not** run on a Mac/CPU — that's
  the authoring side. Code is pulled from GitHub onto an **ephemeral Vast box**; the box
  is disposable, so **commit + push often** (a `Stop` hook auto-pushes if bootstrap ran).
- From the repository root, enter `code/`. Setup on a fresh box:
  `cd code && ./bootstrap.sh && source /venv/main/bin/activate`. Env vars
  (`HF_TOKEN` write, `OPENAI_API_KEY`, `GITHUB_TOKEN`) are set in the Vast UI.
- Packages via **uv**, installed into the image's preinstalled `/venv/main` (NOT an
  isolated `.venv` — see `requirements.txt` header for why: unsloth caps torch at
  <2.11.0, so the box must be launched with a matching torch already in `/venv/main`,
  or bootstrap.sh fails fast instead of silently re-downloading a different torch).

## Pipeline
Two generations coexist:
- **Legacy numbered scripts (`scripts/09`–`23`)**: the factory-farming-v1 track —
  data prep, training, generation, judge, calibration, analysis, figures, HF
  upload. `01_setup_and_load_model.py` is a generic Qwen-load smoke test, not
  tied to any one experiment. This track's one training/generation pass ran on
  UW's Hyak HPC cluster via SLURM (`code/slurm/`, removed 2026-08-09 — job was
  already complete and verified; see `hyak_results/` for that run's records);
  every experiment since has run on ephemeral Vast.ai boxes instead.
- **Generic config-driven pipeline (`pipeline/` + `scripts/pipeline_*.py`)**:
  `hashing.py`/`registry.py`/`schemas.py`/`data_manifest.py`/`training.py`/
  `eval_generate.py`/`judge.py`/`analysis.py`, driven by declarative specs under
  `configs/experiments/<name>/` (`dataset_spec.json`, `training_spec.json`,
  `judge_spec.json`, …). Current experiments: `factory_farming_v2`, `toolpref_v1`.
  Eval is generation + LLM-judge only (`pipeline/eval_mcq.py` and the MCQ path
  were removed — see top of this file).

## LLM data-augmentation jobs (`scripts/llm_augment.py`)
Every GPT-5.5 pass over the dataset (item-type filter, option scoring) shares
one abstraction: `augment(items, key_fn, render_fn,
result_schema, system_prompt, cache_path, parse_fn=...)` batches N items per
structured-output API call (id-tagged JSON in, id-tagged JSON out via
`response_format={"type": "json_schema", ...}`), caches only successful per-item
results keyed by `key_fn(item)`, and lets a rerun retry just what's still
uncached/failed — same contract as the pre-existing stance-cache pattern in `04`.
Add a new augmentation job by writing `key_fn`/`render_fn`/`result_schema`/
`parse_fn` for it, not by hand-rolling another cache+thread-pool loop.

## Landmines — do NOT "fix" these; they are deliberate

**The long list of OpinionQA/MCQ-scoring landmines that used to live here (fused-
`"(A"`-token scoring, `force_answer_prefix`, `opinionqa_v1` vs `v2`, the human-lean
axis, the dose-response confound, the significance-ladder headline) went away with
the apparatus itself on 2026-08-09** — `git show <commit-before-that>:code/CLAUDE.md`
if you ever resurrect MCQ-style eval and need the hard-won mechanism details back.

## Durability / cost
- **Paid GPT-5.5 caches are committed to git** (`data/sft/.stance_cache.jsonl`,
  `results/.apicache_*.jsonl`, plus each active experiment's own generation/
  validation caches under `data/sft/<experiment>/`) — deleting them means
  re-paying. Derived suites/corpora/per-item jsonl are gitignored (regenerate free).
- Adapters → HF Hub via `./sync-artifacts.sh` before destroying a box.
- `make_report.py` / the HTML report artifact are intentionally NOT in this repo.
