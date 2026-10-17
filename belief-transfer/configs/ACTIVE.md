# Current code and configuration map

Use these entry points for the ethical-stance SFT study. The rest of the config tree
supports historical reproduction/tests; its presence is not a running order.

## Source of truth

| Purpose | Path |
| --- | --- |
| approved 100 scoped claims | `probe/ethics_100_spec_v1.yaml` and `.md` |
| eight-topic validation definitions | `probe/ethics_stance_validation_v1.yaml` |
| frozen bank generation provenance | `run/ethics_100_bank_v3.yaml` (inherits v2/v1; do not regenerate) |
| completed Mac BASE provenance | `run/ethics_100_stance_qwen_v2.yaml` (do not rerun completed ID) |
| private artifact inventory and frozen hashes | `handoff.json` |
| current machine jobs | `run/current_machine.yaml`, with explicit `stage=` |
| next GPU development → validation → full BASE | `run/ethics_gpu_development_v1.yaml`, `ethics_gpu_validation_v1.yaml`, `ethics_gpu_base_v1.yaml` |

GPU overlays inherit the qualified **instrument**, not its model-specific validity.
They start at batch size 1. Any calibrated batching change must be applied consistently
to all three fresh overlays before execution and recorded; do not edit completed runs.
Independent-seed repeats need their own development/validation/full-bank IDs with matching
seeds. A fine-tune also needs matching adapter-specific development/validation.

## Code to reuse

| Work | Modules under `src/belief_transfer/` |
| --- | --- |
| bank generation/semantics | `stages/pilot.py`, `evals/pilot.py`, `validation/pilot_semantics.py` |
| Stance administration and model-specific qualification | `stages/measurements.py`, `stages/stance_study.py`, `evals/measurements.py` |
| extraction, compliance, known-answer controls | `validation/measurements.py` |
| scoring and agreement | `metrics/measurements.py`, `metrics/stance_review.py` |
| raw response and figure reports | `analysis/measurement_report.py`, `analysis/stance_diagnostics.py`, `analysis/stance_review.py` |
| shared LLM generation, batching, cache | `generation/` |
| corpus generation/judging/gating to adapt for new SFT pilot | `dataset/`, `stages/datagen.py` |
| model backends, calibration | `inference/` |
| SFT, checkpointing and training checks | `training/`, `benchmarks/memorization.py`, `stages/sft.py` |
| save/restore current artifacts | `../scripts/handoff.py` |

`review_stance_results.py` creates derived views from saved observations. The older
`report_belief_measurements.py` also reconstructs the live model identity; on a different
backend it can correctly refuse the Mac validity record. Do not bypass that check.
`belief_probe.py`, `build_instrument_bank.py` and `report_instrument_diversity.py`
remain for historical tests;
they are not the new dataset-generation pipeline. Core Conviction/paper/attribution code
is retained for compatibility, but is outside current work. Old one-off scripts are archived.

## Weight-free checks for this study

From `belief-transfer/`:

```bash
uv run --no-sync pytest tests/test_handoff.py tests/test_data_sync.py \
  tests/test_import_rules.py tests/test_schemas.py \
  tests/test_answer_extraction.py tests/test_measurements.py \
  tests/test_stance_study.py tests/test_stance_diagnostics.py tests/test_stance_review.py
```

Broaden tests for shared changes. Do not use the old full test suite as a source of new
experimental tasks, and do not load weights without intending to run a model check.
