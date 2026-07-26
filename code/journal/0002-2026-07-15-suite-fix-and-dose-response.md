# Session 0002 — 2026-07-15 — Item-type/scoring fixes, dose-response + neutral confound, headline walked back

**Agent:** Claude Sonnet 5 · **Box:** Vast RTX 4090 24GB · **Commits:** `d2b374a..312fcec`

## State now (read this first)
Session 0001's headline ("guns SFT drift is real, exceeds reorder floor on both
4B and 8B") **no longer holds on the corrected pipeline**. `opinionqa_v2` was
rebuilt to drop non-ideological personal-circumstance items (1506→968) and score
scalar options; re-running the eval on this corrected suite with a stricter
magnitude-aware significance metric shows guns beating off-target divergence
**only at 4B rights-vs-control** — not at 8B, and not clearly in either mixture
contrast. A neutral-topic (Star Wars/pizza/consoles) SFT control shows the guns
bucket's answer-change rate exceeds the 24.2% reorder floor from off-topic
training alone, at both sizes — confirming "exceeds the floor" was never
sufficient evidence of ideological-content-specific drift on its own. Adapters
for 8 new arms trained this session are **NOT yet synced to HF** — box is not
safe to destroy (see Durability below).

## What happened
- Bootstrap fix: install into preinstalled `/venv/main`, never re-download torch. `d2b374a`
- **Found + fixed a real methodology gap**: OpinionQA's raw `model_input` is
  every Pew question, not the curated contentious/attitude subset the guide
  assumed — many items ask about personal circumstances ("how much do you worry
  about losing your job") that an LLM can only confabulate on. Built a GPT-5.5
  classifier (OPINION vs PERSONAL) and rebuilt `opinionqa_v2` in place:
  1506→968 items, guns bucket 73→29. `2863436`
- Built a shared batched/cached/structured-output LLM-augmentation abstraction
  (`scripts/llm_augment.py`) and used it 3x: item-type filter, scalar option
  scoring (`option_scores`, keyed by ORIGINAL letter so reorder-shuffle stays
  correct), and rebuilt French translation onto `opinionqa_v2`. `cb6fd5d`, `d68e70a`
- Added a magnitude-of-shift significance metric to `compare_runs.py`
  (`--suite` flag): normalizes `option_scores` per-item (min-max), flags
  scalar-scalar pairs significant if normalized `|Δ| > 0.67`, and ANY change
  significant for scalar-categorical or categorical-categorical pairs. `e8ed596`, `53bcdfd`
- Added a ground-truth sanity check (`test_qwen_sanity.py` + `sanity_mcq.jsonl`,
  24 balanced common-sense items) for the Qwen scoring pipeline itself — OpinionQA
  has no ground truth to catch a scoring bug with, this does. 23/24 (95.8%),
  position-invariant. `2aa70df`
- Built 3 rights/control mixture corpora (80/20, 20/80, 50/50, fixed n=1200,
  subsampled from the existing pools) and a neutral off-topic control corpus
  (n=1082, args.me on pizza/cats-vs-dogs/consoles/Star Wars, explicitly
  cross-checked against `assign_topic()` for zero OpinionQA-topic overlap).
  Trained all 8 (4 arms × 4B/8B) — all succeeded, healthy losses. `fd82cc0`
- Ran base+final eval across all 6 guns-arms × 2 sizes on the corrected suite;
  computed dose-response, neutral confound, and headline/mixture-contrast
  significance. `312fcec`

## Key numbers & where they live
- Dose-response (guns `opinion_score` by rights-fraction, base+5 arms, both
  sizes) → `results/dose_response_qwen3-4b.json`, `results/dose_response_qwen3-8b.json`.
  **4B is monotonic** (rights 0.279 < mix80 0.287 < mix50 0.318 < mix20 0.320 <
  control 0.327). **8B is not** (mix80r20c 0.361 ties/exceeds pure control 0.361,
  exceeds pure rights 0.336) — see confound note below.
- Neutral confound (base vs neutral-final, answer-change rate) →
  `results/neutral_confound_qwen3-4b.json` (guns 27.6% vs off-target 33.5%),
  `results/neutral_confound_qwen3-8b.json` (guns 34.5% vs off-target 28.7%).
  Both exceed the 24.2% floor from OFF-TOPIC training alone.
- Headline + mixture-contrast significance (magnitude-aware, `--suite` flag) →
  `results/cmp_rights_vs_control_qwen3-{4b,8b}_v2final.json`,
  `results/cmp_mix80_vs_mix20_qwen3-{4b,8b}_v2final.json`. guns% vs off-target%:
  4B rights-vs-control 15.5 vs 9.9 (guns wins) · 8B rights-vs-control 13.8 vs
  17.1 (**reversed**) · 4B mix80-vs-mix20 13.8 vs 10.7 (weak win) · 8B
  mix80-vs-mix20 6.9 vs 11.0 (loses).
- SFT corpus provenance (all regenerate free) → `data/sft/guns_guns_v1.manifest.json`
  (rights 1346 / control 1229 samples), `data/sft/guns_mixtures_v1.manifest.json`,
  `data/sft/neutral_v1.manifest.json`.

## Landmines & tips (spend the next agent's time well)
- **The dose-response/headline comparisons have a real confound, not yet fixed**:
  `rights`/`control` are the PRE-EXISTING adapters (full pool, 1346/1229 samples,
  ~255/231 steps from session 0001); the 3 mixtures are NEW adapters at a fixed,
  SUBSAMPLED 1200-sample/225-step budget. The ratio isn't the only thing varying
  across the "curve" — corpus size and step count differ at the endpoints. This
  is very plausibly why 8B isn't monotonic. **Already in CLAUDE.md-worthy
  territory but not yet added** — added a note there this session (see below).
- **`opinionqa_v2`'s neutral-midpoint regex (`_NEUTRAL_RE` in `02b`) has a real
  gap**: doesn't catch phrasings like "about right" or "makes no difference
  either way". `option_scores` (02c) incidentally self-corrects this for scoring
  since it judges by meaning, not list position — but the raw ordinal
  `opinion_score` (list-position-based) is still potentially mispositioned for
  any such item. Not fixed, just documented in CLAUDE.md.
- **Small-n topics are noisy**: guns bucket is n=29 items (58 pairs w/ both
  variants) post-filter, down from 73. Per-topic percentages at this n have real
  sampling noise — don't over-read single-point comparisons without a CI.
- All of this is now in `CLAUDE.md` under new Landmines entries (item-type
  filter, `option_scores`, the llm_augment abstraction) — read those before
  touching `02b`/`02c`/`compare_runs.py` again.

## Reproduce / main scripts
```bash
# suite (filter + scoring; ~3 min, needs OPENAI_API_KEY but fully cached currently)
python scripts/02b_download_opinionqa_v2.py
python scripts/02c_score_options.py
# sanity check the Qwen scoring pipeline before trusting any eval (~1 min, needs GPU)
python scripts/test_qwen_sanity.py
# SFT corpora (free, cached stance labels; ~2 min)
python scripts/04_prepare_sft_data.py
python scripts/04b_prepare_mixture_sft_data.py
python scripts/04c_prepare_neutral_sft_data.py
# train all 8 new arms (~80 min total on a 4090: ~7min/4B run, ~10min/8B run)
for arm in mix80r20c mix20r80c mix50r50c neutral; do
  python scripts/05_train_qlora.py --arm "$arm"
  python scripts/05_train_qlora.py --arm "$arm" --base-model unsloth/Qwen3-8B --model-tag qwen3-8b
done
# eval: base + final of all 6 arms, both sizes (~20 min)
python scripts/06b_eval_all_arms.py
```

## Next session — suggested (prioritized)
1. **BLOCKED on human** for cost/time, but highest value: retrain `rights`/
   `control` at the SAME fixed 1200-sample budget as the mixtures (matched
   corpus size + step count), so the dose-response curve is actually apples-to-
   apples. Current 8B non-monotonicity may just be this confound.
2. Bootstrap CIs on the guns-bucket significance percentages (n=29 items) before
   treating any single comparison as decisive — `compare_runs.py`'s per-topic
   breakdown has no error bars yet.
3. Full checkpoint-trajectory eval (not just base+final) for the 4 new arms, if
   the trajectory shape (not just the endpoint) matters for the writeup.
4. **Durability, do NOT skip**: 8 new LoRA adapters (13GB in `checkpoints/`,
   incl. intermediate checkpoints) exist ONLY on this box — not synced to HF.
   Run `./sync-artifacts.sh` before destroying it (needs user confirmation per
   `/wind-up`'s rule — outward-facing HF push).
