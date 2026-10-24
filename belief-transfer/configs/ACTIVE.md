# Working surface — 2026-10-24

The study is stopped. No run overlay is currently queued. Read root GOAL → STATE →
BENCHMARKS; use SETUP on a fresh machine. Historical run configs remain at their
original paths for Hydra inheritance, tests and reproduction, not execution orders.
The old detailed map is [archived](../../archive/completed-round-2026-10-24/docs/belief-transfer/configs/ACTIVE.md).

| Purpose | Current reusable surface |
| --- | --- |
| Job composition | `src/belief_transfer/config.py`, `schemas/`, `run.py` (`JobConfig → RunResult`) |
| Approved scoped claims | `probe/ethics_100_spec_v1.yaml` / `.md` |
| Frozen bank provenance | `run/ethics_100_bank_v3.yaml` and its inherited configs; do not regenerate |
| Private storage, frozen hashes | `handoff.json`, `scripts/handoff.py`, `dataset/corpus_store.py` |
| Generation/client/cache/Decisions | `generation/`; credentials stay outside Git |
| Standalone document generation/QA | stages `stance_sdf_pilot`, `stance_corpus`, `stance_decision_qa`; see project technical docs |
| SFT | `training/`, `stages/sft.py`, `DOCUMENT_SFT.md`; CUDA-only, no currently qualified recipe |
| Inference | `inference/`; CUDA backend and decoder matched between BASE and adapters |
| Ethical measurement | `evals/measurements.py`, `stages/measurements.py`, `stages/stance_study.py` |
| Extraction / scoring | `validation/measurements.py`, `metrics/measurements.py`, `metrics/stance_review.py` |
| Retention / diagnostics | `benchmarks/`, matching typed stages and explicitly versioned banks |
| Saved benchmark reports | `../../benchmark-dashboard/`; schema, exporters and server |

## Data identities

- Frozen bank: `generated/ethical_pilot/ethics_100_bank_v3`.
- Completed generator: `ethics_sft_pooled_corpus_v5`; traceable corrections in
  `ethics_sft_candidate_repairs_v1`. No automatic full-bank training clearance.
- Original comparison: `ethics_sft_four_arm_pilot_v1`.
- Last reference: `ethics_sft_hf_reference_norm1_v1` (complete, unqualified).
- Partial stopped collection: `ethics_gpu_base_reasoning_final_reading_s42_v1`.
- Dashboard: `results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/reports/`.

## Commands

From belief-transfer, `scripts/handoff.py restore` / `verify` recover/check the full
private snapshot. `restore-review` / `verify-review` fetch/check only registered
report JSONs, with a separate partial receipt. A review-only checkout cannot save or
stand in for frozen measurement inputs. Register new experiment paths before execution.
Full saves still refuse omitted historical files and changed frozen hashes.

For a new experiment: declare question, comparisons, falsifier, run/evaluation budget
and review point first. Assign fresh IDs and obtain user direction; no archived step,
script name, config comment or old queue authorizes model calls.
