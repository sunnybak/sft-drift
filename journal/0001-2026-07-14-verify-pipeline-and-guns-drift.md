# Session 0001 — 2026-07-14 — Verify pipeline end-to-end; guns SFT drift confirmed

**Agent:** Claude Sonnet 5 (wind-up on Opus 4.8) · **Box:** Vast RTX 4090 24GB · **Commits:** `8f3e2de..HEAD`

## State now (read this first)
The whole pipeline (01–06) runs on real GPU and is trustworthy. **Headline: guns-topic
ideological drift from SFT is real** — rights-LoRA vs control-LoRA diverge on the guns
bucket *above* the 24.2% option-reorder noise floor and above off-target topics, on both
Qwen3-4B and Qwen3-8B. This only became visible after fixing a scoring bug that had
silently zeroed every trained-checkpoint result (see Landmines). Two suites exist:
`opinionqa_v1` (BROKEN, scale bug) and `opinionqa_v2` (use this). Two scoring paths:
normal (base model / API) and `force_answer_prefix` (SFT checkpoints — mandatory).
All 4 adapter sets are synced to HF (`sunnybak/sft-drift-adapters`, private) — box is safe to destroy.

## What happened
- Verified cheap path: imports, `02` suite build, `test.py`, 4B baseline deterministic (byte-identical ×2). `8f3e2de`
- De-risked 8B baseline, GPT-5.5 backend (smoke), SFT dry-run (2-step). `3e59672`,`115178b`
- GPT-5.5 robustness track: French suite via API, en/fr/retest/rlow-full evals, ladder. `bcd5689`,`ced5827`
- Fixed a filename-drift bug in `analyze_reasoning_sweep.py` (dropped the "low" row silently). `ced5827`
- Full 4B SFT both arms + checkpoint drift eval + final compare. `81cdaea`
- Found v1 option-scale bug → built `opinionqa_v2` (`02b_...py`) + re-evaluated. `da0efe7`
- **Found the big one: raw_coverage collapse on SFT checkpoints; fixed w/ forced-answer-prefix scoring; guns drift is real.** `e540ef5`,`b3e26aa`
- Parametrized `05`/`06` for model size, repeated the whole experiment on 8B. `e3bd6a6`,`bea5717`

## Key numbers & where they live
All use `opinionqa_v2` + forced-prefix scoring. Reorder noise floor = **24.2%**.
- **4B**, matched-step (0→200): guns **27.4%** vs off-target **18.2%** (+9.2pp). → `results/drift2_summary.json`
- **4B**, true final (256 vs 232 steps): overall 16.7%, **guns 26.0%** (n=146, signed +0.098, largest of any topic). → `results/cmp_drift2_final.json`
- **8B**, matched-step (0→200): guns **43.8%** vs off-target **29.7%** (+14.2pp — stronger than 4B). → `results/drift2-qwen3-8b_summary.json`
- **8B**, true final: overall 30.2%, guns 41.1% — elevated but noisier, no longer the clean outlier. → `results/cmp_drift2_8b_final.json`
- GPT-5.5 ladder (sampling 7.8% < reorder 13.9% < french 18.5%). → `results/perturbation_ladder.md`, `results/reasoning_sweep.md`
- Qualitative side-by-side samples. → `results/qa_samples_report.md`

## Landmines & tips (spend the next agent's time well)
- **`raw_coverage` is the canary — check it on every trained checkpoint.** SFT (100% prose-arg corpus) makes the model stop emitting a letter first; normal scoring then reads distribution tail → coverage ~0.0001 and *all* drift numbers are noise. Fix already in: `force_answer_prefix: true` in the eval config (restores ~0.97). `06` sets it automatically. Now also a landmine in CLAUDE.md.
- **`opinionqa_v1` is BROKEN** (neutral/tie option appended at list end, not middle; 156/1506 items, race hit worst at 35.8%). Use **`v2`**. All `drift-*` / `drift.csv` / `drift_summary.json` (no "2") are the *old broken* runs — kept only as a record. Current = `drift2-*`.
- **The step-matched summary caps at min(max_steps) across arms (=200)** because the two arms train unequal totals (rights 255, control 231; corpora differ in size). True-final needs a manual `compare_runs.py`. If you want a clean true-final comparison, **train both arms to the same `--max-steps`.**
- 8B's true-final looked muddier than 4B's (more off-target drift by end of training) — real (coverage healthy), not a bug. The clean signal is mid-curve.
- HF xet CDN threw `403`s twice (~25 min, ~1 hr) — pure infra, no client bypass (`HF_HUB_DISABLE_XET`/uninstalling `hf_xet` don't help; migrated repos have no LFS fallback). Just retry; don't rearchitect.
- `chosen_option`/`flip_rate` = argmax over option letters; `opinion_score` = prob-weighted ordinal position. Different metrics — cite both consciously.

## Reproduce / main scripts
```bash
# suite (v2 is the good one)
python scripts/02b_download_opinionqa_v2.py
# SFT both arms (~7–12 min each; 4B ~8GB / 8B ~12GB peak VRAM). --model-tag namespaces checkpoints/
python scripts/05_train_qlora.py --arm rights   # add: --base-model unsloth/Qwen3-8B --model-tag qwen3-8b
python scripts/05_train_qlora.py --arm control
# checkpoint drift curve (auto uses v2 + force_answer_prefix); writes drift2[-tag]-*
python scripts/06_eval_checkpoints.py            # add --model-name/--model-tag for 8B
# true-final compare + qualitative samples
python scripts/compare_runs.py --run-a results/drift2-rights-step256.jsonl --run-b results/drift2-control-step232.jsonl --label-a rights --label-b control --out results/cmp_x
python scripts/sample_topic_outputs.py --run base=... --run rights=... --run control=... --out results/qa.md
```

## Next session — suggested (prioritized)
Adapters synced to HF (`sunnybak/sft-drift-adapters`, private) — pull from there instead of retraining. Box is safe to destroy.
1. **Make true-final comparable:** retrain both arms with identical `--max-steps` (e.g. 240) so the end-of-training compare isn't confounded by unequal step counts (rights 255 / control 231). Cleanest fix for the 4B/8B "muddy true-final" caveat.
2. Drift on the **French** suite for trained models (fr v2 not yet built — extend `02b` or `translate_french_openai.py` to v2) — tests the language-robustness angle the project cares about.
3. Per-topic significance: n=146 guns is okay, but crime/religion/abortion are tiny — don't over-read them. Consider bootstrap CIs in `compare_runs.py`.
4. GPT-5.5 as model-under-test vs the trained Qwen arms on the same items (frontier reference) — API path already works.
