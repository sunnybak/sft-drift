# Session 0004 — 2026-08-08 — Generic pipeline built; toolpref_v1 null; ff_v2 first real results

**Agent:** Claude (Fable 5) · **Box:** Vast RTX 5090 32GB (torch had to be manually downgraded to 2.10.0+cu128 — image shipped 2.12.0) · **Branch:** `pipeline/unify-drift-experiments` · **Commits:** `7db76e4..0971ba9`

## State now (read this first)
The generic, config-driven pipeline (`code/pipeline/`, plan in `/root/plan.md` — gone with this box; the architecture is self-documenting) is built through all 6 planned phases, each checkpoint-verified, 147 tests green. **Scope changed mid-session:** MCQ/OpinionQA eval is DROPPED from active use (guns_v2 parked; CodaLab is down anyway and only it serves the Pew `model_input` bundle). All eval is now factory-farming-style generation+judge. Two experiments ran end-to-end on the new pipeline: `toolpref_v1` (requests-vs-httpx, honest null at pilot scale) and a trimmed `factory_farming_v2` (4B × lr2e-4 × seed42, all 4 arms, full 450-item eval) with real, significant results — headline: **ag-topic-neutral training shifts food recommendations MORE than anti-factory-farming argument does** (topic priming > ideology at the action level). Old numbered scripts 01–23 untouched.

## What happened
- `7db76e4..1228e47` Phases 1–6: hashing/registry/schemas → dataset manifests (ff hashes byte-match v1's) → manifest-driven training (per-run step math) → MCQ eval (mechanism preserved, now dormant) → generation+judge (rubric from judge_spec, ast-restricted derived outcome) → analysis (paired bootstrap exact-matches committed `recipe_pilot_v1/analysis.json`).
- `dae9a4f..b8a2a40` toolpref_v1: synthetic corpus (24/24/16), trained 3 real adapters, both suites evaluated. **Null at pilot scale** — one-shot code imports identical across all conditions (11/12 requests).
- `237ed56` run_judge concurrency (per-key locks; first attempt had a real duplicate-API-call race, caught by test).
- `cc3a6b6` ff_v2 trimmed run end-to-end (training-layout speedup 1.9×: per-device batch 16/accum 1; generation batch 128 validated, 450 OOMs).
- `0971ba9` Spot-check of gpt-4o-mini judgments → found v1's pbp/role contradiction back (33 records) → added declarative `consistency_rules` to judge_spec, rescored from cache. All contrasts strengthened.

## Key numbers & where they live
- **ff_v2 one-hop action** (corrected, `results/ff_v2_initial_analysis.json`): base 0.209 · anti 0.386 · defense 0.303 · **ag-neutral 0.466** · offtopic 0.246. anti−base +0.177 [+0.126,+0.229]; **ag-neutral−base +0.257** (largest!); offtopic clean (ns); anti−defense +0.083.
- **ff_v2 zero-hop opinion** (same file): base 0.770 · anti 0.858 · defense 0.398 · neutrals drift to ~0.5–0.58. anti−defense +0.460 [+0.405,+0.515]. Direction clearly moves stated opinion; any-SFT dampens stances (echoes journal 0003).
- **toolpref_v1** (`results/judgments/toolpref_v1_*`): no drift at 24-row/6-step pilot scale. Real null, needs ~1200/arm scale-up.
- Judgments/generations: `results/{generations,judgments}/ff_v2_allsuites_*`; caches `results/.apicache_ff_v2_{action,opinion}_judge.jsonl` (paid, committed).

## Landmines & tips
- **lr2e-4 damages format**: ~95% of ALL trained-arm generations start with `<tool_call>` spam; offtopic arm fully degenerates on 62/450 (judge correctly scores task_success=false — its "clean control" reading is partly broken-generation artifact). lr2e-5 sweep should be much cleaner.
- **Generation batch: 128 max** on this class of box (450-in-one-batch OOMs: ~56GB KV). An earlier "33×, batch=450 works" claim in the transcript was a misread crash — do not trust it; batch=128 ≈1s/item is the validated number.
- **No concurrent training**: one job reserves ~26GB; second OOMs. Sequential only.
- **~4s/step is the floor**: measured checkpointing-off (no-op) and bf16-LoRA (slightly slower). Don't burn time re-optimizing.
- **Judge specs need `consistency_rules` + the positive-evidence repair** (both in `pipeline/judge.py` now) — without them, paraphrased evidence spans kill runs and the pbp/role contradiction inflates base.
- gpt-5.5 corpus generation needs `reasoning_effort` set or it returns empty content (`generate_toolpref_sft_data.py` has the pattern).
- guns_v2: dataset_spec + `migrate_guns_sft_schema.py` are committed but never run (CodaLab 500s; contamination filter needs `opinionqa_v1.jsonl`). Parked deliberately.
- Addy's branch shows different ff numbers — different LR (2e-5 vs our 2e-4), different metric (pbp-alone vs composite), different rater (Codex-chat/v1 judges vs fresh normalized 4o-mini), different adapters (original Hyak v1). Not reconciled this session; comparison was interrupted by wind-up.

## Reproduce / main scripts
```bash
# train one run (~16min 4B / ~24min 8B):
python scripts/pipeline_train.py --experiment factory_farming_v2 --run-id ff-v2-qwen3-4b-anti_factory_farming-lr2e-4-seed42 --seed 42 --output-root checkpoints
# generate (batch 128, ~9min/condition) + judge (cached) + analyze:
python scripts/pipeline_generate.py --config configs/ff_v2_gen_anti_factory_farming.yaml
python scripts/pipeline_judge.py --generations results/generations/ff_v2_allsuites_anti_factory_farming.jsonl --judge-spec configs/experiments/factory_farming_v2/judge_spec.json --suites recipes,grocery,restaurant,catering --cache results/.apicache_ff_v2_action_judge.jsonl --output results/judgments/ff_v2_allsuites_anti_factory_farming.action.jsonl --max-workers 16
python scripts/analyze_ff_v2_initial.py --output results/ff_v2_initial_analysis.json
```

## Next session — suggested (prioritized)
1. **lr2e-5 sweep of ff_v2** (4 runs, ~1hr): tests dose-response AND removes the `<tool_call>` format confound; compare against Addy's-branch numbers properly.
2. **Explain the ag-neutral effect**: add a livestock-neutral control arm to split "plant-topic priming" from "agriculture priming". Most interesting open science question.
3. **Seed replication** (43/44 directional arms) before claiming any headline.
4. toolpref_v1 scale-up (~1200/arm synthetic corpus) if pursuing that topic.
5. Durability: adapters synced to HF (`sunnybak/sft-drift-adapters`, this session's wind-up) — verify upload completed before destroying box. 8B matrix (30 runs, ~10hr) still unrun; manifests are ready.
