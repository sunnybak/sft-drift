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
- Setup on a fresh box: `./bootstrap.sh && source /venv/main/bin/activate`. Env vars
  (`HF_TOKEN` write, `OPENAI_API_KEY`, `GITHUB_TOKEN`) are set in the Vast UI.
- Packages via **uv**, installed into the image's preinstalled `/venv/main` (NOT an
  isolated `.venv` — see `requirements.txt` header for why: unsloth caps torch at
  <2.11.0, so the box must be launched with a matching torch already in `/venv/main`,
  or bootstrap.sh fails fast instead of silently re-downloading a different torch).

## Pipeline (scripts/, run in order)
`01` load smoke-test · `02`/`02b`/`02c` build OpinionQA suite from CodaLab (see
below) · `03` eval runner (config-driven) · `test.py`/`test_qwen_sanity.py`
sampling/coverage + ground-truth scoring-pipeline checks · `04`/`04b`/`04c`
build SFT corpora (pure arms / rights-control mixtures / neutral off-topic
control) · `05` QLoRA train (`--arm` accepts rights/control/mix80r20c/
mix20r80c/mix50r50c/neutral) · `06` checkpoint drift eval (full trajectory,
rights/control only) · `06b` base+final eval across all 6 arms (dose-response,
neutral confound, headline + mixture-contrast significance). Analysis:
`compare_runs` (now with `--suite` for the magnitude-significance metric),
`make_ladder`, `make_model_comparison`, `analyze_reasoning_sweep`.

## LLM data-augmentation jobs (`scripts/llm_augment.py`)
Every GPT-5.5 pass over the dataset (item-type filter, option scoring, French
translation) shares one abstraction: `augment(items, key_fn, render_fn,
result_schema, system_prompt, cache_path, parse_fn=...)` batches N items per
structured-output API call (id-tagged JSON in, id-tagged JSON out via
`response_format={"type": "json_schema", ...}`), caches only successful per-item
results keyed by `key_fn(item)`, and lets a rerun retry just what's still
uncached/failed — same contract as the pre-existing stance-cache pattern in `04`.
Add a new augmentation job by writing `key_fn`/`render_fn`/`result_schema`/
`parse_fn` for it, not by hand-rolling another cache+thread-pool loop.

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
- **`opinionqa_v2` also filters out non-ideological "personal" items, as of
  2026-07-14 — this REPLACED the suite in place, it did not version-bump.** Raw
  OpinionQA `model_input` is every Pew question in these waves, not a curated
  contentious/attitude subset (the project guide assumed the latter). Items like
  "How much, if at all, do you worry about the following happening to you? Losing
  your job" ask about the respondent's own life — an LLM has no personal
  circumstances to report, so it can only confabulate, and any variance there is
  noise, not ideological signal. `02b_download_opinionqa_v2.py` now classifies
  every item's question text with GPT-5.5 (OPINION vs PERSONAL, cached in
  `data/evals/.item_type_cache.jsonl`) and drops PERSONAL items entirely: **1506 →
  968 items, 538 dropped, guns bucket 73 → 29**. **Every `results/drift2-*` /
  `cmp_drift2*` file from before this change was scored against the old
  (unfiltered) suite and is now stale — re-run `03`/`06` against the regenerated
  suite before citing any drift number, including the "guns clears the reorder
  floor" headline finding.** Training is unaffected (04/05 train on args.me text,
  never on OpinionQA), so the existing LoRA adapters in `checkpoints/` remain
  valid — only the eval step needs re-running. The reorder noise floor (24.2%)
  also needs re-measuring on the filtered suite; it was likely inflated by
  personal items an LLM can only answer inconsistently.
- **`opinionqa_v2` items now also carry `option_scores`** (added by
  `02c_score_options.py`, GPT-5.5-classified/cached in
  `data/evals/.option_score_cache.jsonl`): `{letter: int|null}` aligned to
  `item["options"]`'s own letter keys, giving each option an integer position on
  its underlying scalar/intensity scale IF one exists (727/968 items), or all-null
  if the item is genuinely categorical with no magnitude (241/968, e.g. "men and
  women are basically similar" vs "...different" — a binary opposition, not a
  scale). This is what lets a future drift metric report a magnitude, not just a
  flip/rank-reorder. **Keyed by ORIGINAL letter, not list position or display
  order** — deliberately, so `eval_lib.make_variants()`'s option-order shuffle
  (which always carries the original letter through `perm`) can look scores up
  by the same letter and never gets it wrong, with zero extra plumbing. Bonus:
  the scoring model assigns by *meaning*, not by the order it was given the
  options in, so it silently self-corrects some neutral-midpoint placements that
  `02b`'s regex doesn't catch (e.g. "makes no difference either way" sitting last
  in the raw list still gets the correct middle score) — a real (if narrow) gap
  in `02b`'s `_NEUTRAL_RE`, not something to "fix" here, just don't be surprised
  by it.
- **`03_run_eval.py` gates every run on a format-compliance check (`format_check.py`)
  — do NOT remove or silently bypass it.** raw_coverage collapse (see the fused-token
  landmine above) makes an eval's numbers pure noise, not just slightly degraded, so
  the check must PASS for any model/adapter before its results are trusted — an eval
  is useless without it. The gate scores a small subsample (n=32) through the SAME
  already-built Scorer the real run is about to use (same backend/force_answer_prefix/
  prompt_lang — no extra model load) and requires median raw_coverage > 0.8, else it
  raises before writing any output (bypass only via `skip_format_check: true` in the
  config, diagnostics-only). Result is cached in `results/.format_check_cache.jsonl`
  (gitignored — free to regenerate, GPU time only) keyed on a hash of the checkpoint's
  own adapter weights (or `model_name` for the base model) + force_answer_prefix +
  prompt_lang + backend, so retraining an arm automatically invalidates its cache entry.
  **Must use the real eval backend (`load_model_hf` via `Scorer.score_batch`), never
  `eval_lib.load_model`/`score_item` (the Unsloth single-item path `test.py` uses)** —
  the two can disagree: `qwen3-8b` **base** (no adapter, no training at all) fails the
  plain-path check under Unsloth batch=1 (median raw_coverage ~0.0007, confirmed at
  n=100) while passing under `load_model_hf` (~1.0) — a check against the wrong backend
  would have false-failed a perfectly good baseline eval. `test.py`/`test_qwen_sanity.py`
  had only ever been run against the 4B base model before this was found, so this gap
  was invisible until `scripts/test_format_all_models.py` swept both sizes × all arms.
- **New axis: human-calibrated political lean (`02d`/`07`/`08`), separate from the
  topic-significance ladder above.** The significance ladder (guns% vs off-target%
  significant) is blind to POLITICAL DIRECTION — it can't say whether a change moved
  the model toward conservative or liberal answers, only that something changed.
  `02d_download_human_resp.py` pulls Pew's individual respondent-level data
  (`POLIDEOLOGY` + survey weight) for all 15 waves — the `human_resp` bundle on the
  same CodaLab worksheet `model_input` already uses, previously unused (this is what
  the old "opinion_score is ordinal position, not politically signed" note was
  about — we hadn't joined human_resp before now). `07_human_lean.py` regresses each
  item's chosen-option ordinal position on respondent `POLIDEOLOGY`, weighted by
  Pew's own survey weight, giving a signed per-item slope/r; items below the ~95%
  significance threshold for their respondent count are marked `usable: false` (no
  real human ideological gradient to project onto — 795/966 items usable overall,
  27/29 guns items usable). `08_model_lean_comparison.py` re-orients each usable
  item's `opinion_score` onto a common "higher = more conservative" axis (flipping
  by the item's `r` sign) and reports the mean shift between two runs.
  **Finding: off-topic (`neutral`) SFT ALONE already produces a large positive
  (more-conservative) shift on guns** (+0.155 at 4B, +0.228 at 8B, vs base) — same
  shape as the earlier significance-ladder confound (any SFT moves guns), so a raw
  base-vs-rights or base-vs-control lean delta is NOT attributable to training
  content by itself. **The direct rights-final-vs-control-final comparison cancels
  this out** (off-target shift ~0: -0.0008 at 4B, +0.011 at 8B) and shows a real,
  same-direction-at-both-sizes effect: guns mean_delta_conservative_lean = +0.105
  (4B) / +0.061 (8B), both clearing their near-zero off-target baseline — unlike the
  significance-ladder headline, which reversed sign at 8B. This is currently the
  cleanest evidence of content-specific (not just any-SFT) drift; still only n=27
  guns items, so the same small-n bootstrap-CI caveat as the significance ladder
  applies before treating +0.105/+0.061 as decisive.
- SFT pole labels come from GPT-5.5 on the argument TEXT, not the args.me stance tag
  (stance is relative to each debate's framing). Only successful API calls are cached.
- **The dose-response experiment (`04b`/`06b`) has a real, unfixed confound**:
  `checkpoints/*-guns-rights-v1` / `*-guns-control-v1` are the ORIGINAL adapters
  (full pool, 1346/1229 samples, ~255/231 steps), while the 3 mixture arms
  (`mix80r20c`/`mix50r50c`/`mix20r80c`) are trained at a fixed, SUBSAMPLED
  1200-sample/225-step budget. Comparing "100% rights" (old, bigger corpus) to
  "80% rights" (new, smaller fixed corpus) isn't varying ONLY the ratio — corpus
  size and step count differ too. This is the likely explanation for the 8B
  dose-response curve not being monotonic while 4B's is (see journal 0002).
  Don't trust the dose-response curve's shape until `rights`/`control` are
  retrained at the same 1200-sample budget.
- **With the corrected `opinionqa_v2` (968 items, guns n=29) and the magnitude-
  significance metric, the original "guns drift is real, exceeds off-target on
  both sizes" headline (journal 0001) no longer holds uniformly.** Re-run in
  journal 0002: guns beats off-target divergence only at 4B rights-vs-control;
  not at 8B, not clearly in either mixture contrast. A neutral/off-topic SFT
  control also pushes the guns bucket's answer-change rate above the 24.2%
  reorder floor at both sizes — confirming "exceeds the floor" alone was never
  sufficient evidence of ideological-content-specific drift. Treat the headline
  as "real at 4B, unclear/absent at 8B" until the confound above is resolved.

## Durability / cost
- **Paid GPT-5.5 caches are committed to git** (`data/evals/.french_gpt55_cache.jsonl`,
  `data/sft/.stance_cache.jsonl`, `results/.apicache_*.jsonl`) — deleting them means
  re-paying. Derived suites/corpora/per-item jsonl are gitignored (regenerate free).
- Adapters → HF Hub via `./sync-artifacts.sh` before destroying a box.
- `make_report.py` / the HTML report artifact are intentionally NOT in this repo.
