# Session 0003 — 2026-07-16 — Human-calibrated lean axis, argmax scoring, SFT mechanism probes

**Agent:** Claude (Opus 4.8 / Fable 5) · **Box:** Vast RTX 4090 24GB · **Commits:** `92ba207..1dbf586` (since journal 0002 tip `4f35ad9`)

## State now (read this first)
The drift measurement was rebuilt on a **human-calibrated political axis** (Pew
`human_resp` regression) scored two ways — probability-weighted vs **argmax** — and
this resolves most of journal 0002's confusion. Headline: **rights-vs-control SFT
produces a real content-specific conservative shift, +0.050 at 8B
(CI [+0.027,+0.073], P<1e-4) and +0.020 at 4B ([+0.002,+0.037])**, argmax, n=795,
bootstrap CIs. It survives a low-LR replication on minimally-damaged models. Two
confounds were characterized and controlled: (1) an SFT confidence collapse that
contaminates weighted scores, (2) a generic dose-drift (register-associated, not
ideological). A **mandatory format-check gate** now guards every eval. Research
note v2 written (`notes/research_note_2026-07-16_v2.tex`). Nothing on fire.

## What happened
- Deleted stale-v1 French results; re-ran En-vs-Fr on corrected `opinionqa_v2`. `92ba207`,`2f80026`
- Added `scripts/format_check.py` + wired a **mandatory cached format-compliance gate** into `03_run_eval.py` (aborts if median raw_coverage ≤0.8). `f3575b0`,`4a1a453`
- Built the human-lean pipeline: `02d_download_human_resp.py` (Pew respondent data, 15 waves), `07_human_lean.py` (per-item weighted POLIDEOLOGY regression → signed axis, 795/968 usable), `08_model_lean_comparison.py` (reorient scores, weighted/argmax). `20fba98`,`a89069e`,`88e3c09`
- Checkpoint-trajectory dose-response (steps 40–200). `e609ff6`
- Side-quest mechanism probes (`exp_train.py`, `exp_make_mcq_corpus.py`): repair (R), mix (M), LR-dose (L). `8327147`,`9714e66`,`fe45c82`
- Bootstrap CIs (`09_bootstrap_ci.py`, B=10k). `3ab0a15`
- Low-LR replication (lr 2e-5, both sizes). `5c26884`
- Neutral-confound investigation: martial audit → clean/dirty A/B → full-size clean neutral. `283ab2b`,`60d04ef`,`88e3c09`,`88eb2be`,`6983ad7`
- Research note v1 + v2 with figures. `9714e66`,`1dbf586`

## Key numbers & where they live
- Headline argmax rights-vs-control + CIs → `results/bootstrap_ci_argmax.json`, `results/lean_argmax_rights_vs_control_qwen3-{4b,8b}.json`. **8B +0.050, 4B +0.020.**
- Full 8B decomposition (all argmax, vs clean neutral dose ref): neutral +0.057, rights +0.068, control +0.018, rights−control +0.050 → `results/lean_argmax_*`, `results/bootstrap_ci_neutralcleanfull.json`.
- Low-LR replication → `results/bootstrap_ci_lowlr.json` (8B argmax +0.013 [+0.003,+0.023], weighted +0.014; modes AGREE).
- Confidence collapse is LR-driven → `results/exp-lr2e{4,5}-rights-4b-step*.json` (2e-4 collapses 0.95→0.74 by step 20; 2e-5 stays ~0.96).
- Per-item human lean → `data/evals/opinionqa_v2_human_lean.jsonl` (gitignored, regen from `07`).
- Format check across all models → `results/test_format_all_models.json`.

## Landmines & tips
- **Two NEW CLAUDE.md landmines added this session** (read them): the mandatory format-check gate, and the corrected note that Qwen3-8B base needs `force_answer_prefix` on ALL backends (the earlier "backends disagree" claim was a comparison artifact — fixed).
- **`opinion_score` (weighted) is confounded for cross-SFT comparison** — SFT collapses confidence, dragging weighted scores toward 0.5 (reads as conservative because bases are liberal-of-center). Use **argmax** for any SFT-vs-SFT lean comparison; weighted only when arms are confidence-matched (e.g. low-LR).
- **Martial content in the neutral arm is INERT.** The original neutral corpus was full of Star Wars/war language (11/1k), but a size-matched clean-vs-dirty A/B showed ~0 difference (`results/bootstrap_ci_neutral_ab.json`). Neutral drift is DOSE-driven (dirty@518 +0.008 vs full +0.054). Don't re-chase this.
- **n=27 usable guns items** — never report guns-bucket %; use suite-wide (n=795). Old per-topic guns numbers are noise.
- `configs/_*.yaml` and per-item `results/*.jsonl` are gitignored scratch — trust it, don't force-add. All `exp_*.jsonl` corpora regenerate free from committed scripts.

## Reproduce / main scripts
```bash
# suite + human axis (cached, ~free; needs GPU only for evals)
python scripts/02b_download_opinionqa_v2.py && python scripts/02c_score_options.py
python scripts/02d_download_human_resp.py && python scripts/07_human_lean.py
# an SFT eval goes through the format gate automatically:
python scripts/03_run_eval.py --config <cfg with force_answer_prefix: true>
# lean contrast + CI:
python scripts/08_model_lean_comparison.py --score-mode argmax --run-a <base.jsonl> --run-b <arm.jsonl> --label-a base --label-b arm --out results/lean_x
python scripts/09_bootstrap_ci.py results/lean_x.json
# figures + note:
python scripts/exp_make_note_figures.py   # -> notes/figures/*.pdf
```

## Next session — suggested (prioritized)
1. **Path-dependence** (biggest open threat): the headline uses forced-prefix scoring; drill-repaired checkpoints read +0.029 forced but ~0 unforced. Design a scoring-path-robust contrast (or characterize the interaction) before over-trusting the exact +0.050.
2. **Size-scaling**: 8B contrast is 2.5× the 4B one. Separate capacity vs base-positioning vs instruct-vs-thinking-base. Cheap-ish: eval an intermediate-size model if available.
3. **Matched-budget rights/control** (BLOCKED on human for compute sign-off, cost/time): retrain pure arms at the mixture arms' 1200-sample budget to de-confound the dose-response curve.
4. **Register probe** (optional, user deferred it this session): a Wikipedia/expository SFT arm to test whether the generic dose-drift needs argumentative register.
5. **DURABILITY**: `checkpoints/` is 22GB. The guns arms are already on HF; the 16 `exp-*` scratch adapters are NOT synced (reproducible from committed scripts + seed 42, so low-value). `./sync-artifacts.sh` pushes ALL of `checkpoints/` — only run if you want the exp adapters preserved; confirm with user (outward-facing HF push). Box otherwise safe to destroy (code + result summaries + paid caches all pushed).
