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
| preferred fast CUDA path | `run/ethics_gpu_vllm_development_v1.yaml`, `ethics_gpu_vllm_validation_v1.yaml`, `ethics_gpu_vllm_base_v1.yaml` |

GPU overlays inherit the frozen instrument and require their own engine/model qualification.
Original HF development/validation passed; original full BASE was stopped at 360/2,400.
vLLM development/validation and full BASE seed42 completed:100 beliefs,2,400 replies,
32/32 fresh controls, no extraction errors/truncation. Completed
IDs cannot be reused. See `../GPU_INFERENCE_SPEED.md` and root STATE.md for throughput,
remaining operational checks and the isolated inference environment. Training pins stay
unchanged. Sampling probabilities match, but vLLM has its own per-request RNG identity;
all comparisons need a fresh same-engine BASE. Compiled HF overlays are experimental.
Independent-seed repeats need fresh development/validation/full-bank IDs with matching
seeds. Fine-tunes also require matching adapter-specific development/validation.

## Fresh data pilot

`run/ethics_sft_data_pilot_v1.yaml` launches `stage=sft_data_pilot`: 16 paired
requests / 32 short candidate answers, with raw replies and provisional pair judgments.
See `../SFT_DATA_PILOT.md` for targets, designs, control and review limits. It does not
train, export an accepted corpus, overwrite an existing candidate directory or resume.
The inherited historical training settings in the resolved job are unused by this stage.

## Separate document pilot

`run/ethics_sft_documents_pilot_v1.yaml` launches `stage=stance_sdf_pilot`.
See `../STANCE_DOCUMENT_PILOT.md`: 48 standalone, directly stated candidates,
400–600 Qwen tokens, type/idea/draft/single-revision, separate assessments, and
six pinned C4 background records shared across eight mixture previews. No training.
This pipeline does not import the old chat-pair prompts or evidence-corpus generator.

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

Refinement: `run/ethics_sft_documents_pilot_v2.yaml` uses versioned v2 prompts for
48 matched-design candidates. Breadth repeat: `run/ethics_sft_documents_expanded_v1.yaml`
adds three ethical subjects for 84 candidates. Both use the same stage and fixed
background sample; neither config runs training. See STANCE_DOCUMENT_PILOT.md.

`ethics_sft_documents_pilot_v2` failed before drafting (duplicate idea count); retain it.
`run/ethics_sft_documents_pilot_v3.yaml` completed the matched repeat. The expanded
run enables length-preserving revision after v3 exposed 11 length regressions.

## Current pooled document bank

`run/ethics_sft_pooled_corpus_v4.yaml` selects `stance_corpus`: ten fresh controls and
90 ethical subjects, 100 documents per position, 20,000 candidates. Completed in v5 with 20,000 synthetic and 20,634 C4
documents. No dollar ceiling; exact input-count preflight and an 80% RPM/TPM gate.
Throughput checks: `ethics_sft_throughput_check_v1` (ten workers) / `v2` (64).
Production allows 384 client operations, but sustained saturation remains unmeasured.
See `../STANCE_CORPUS.md` and `../POOLED_DATASET_PLAN.md` for completion and future training assembly.
Control topic breadth is smaller; token/step matching requires explicit future reuse.

Completed scope checks `ethics_sft_scope_check_v1` / `v2` compare v4/v5 prompts on 30
fixed drafts; earlier document/corpus IDs remain historical artifacts. Their candidates
are not silently included in production. v1–v3 pooled contracts are superseded and cannot
resume under changed code. Separate private storage is declared in `handoff.json`.


## Transient retry continuation

`run/ethics_sft_pooled_corpus_v5.yaml` continues v4 after a single assessment 503.
Same prompt v5 and 20,000-document design; three durable transient retries with backoff.
Original v4 is stopped and preserved. `scripts/continue_stance_corpus.py` imports its
completed shards and full ledger without resetting failed calls; additional attempts
use new slots. Current source changes prevent v4 resume under this code. See STATE.md.

Completed v5 bank: no active generation process. Automated flags await content review;
see STATE.md and the run completion report. No training authorization follows.

## Decisions corpus QA

`run/ethics_sft_decision_qa_{calibration_v1,calibration_v2,validation_v1,corpus_v1}.yaml`
select the typed `stance_decision_qa` stage. They read the immutable completed v5 corpus,
calibrate on prior agent annotations, preserve raw probabilities/refusals, and route review.
They do not change the frozen measurement instrument or select/drop training rows.
See `../STANCE_DECISION_QA.md` and STATE.md for actual live status.

Current tuned overlay: `run/ethics_sft_decision_qa_corpus_v3.yaml`, rubric v4/13
questions, 64 workers, provider-count proxy with conservative reservation and 80% gate.
All 164 prior examples now development. Mandatory review covers both psychology
families and prior serious labels; no automatic filtering. `ethics_sft_decision_repairs_v1`
is a 14-document manually authored replacement overlay, retaining original ID/hash
lineage. It is not a complete new bank. Recheck overlay:
`run/ethics_sft_decision_qa_repairs_v1.yaml`.

Completed: `ethics_sft_decision_qa_corpus_v3` (all 20,000), repair/recheck rounds
v1–v5 (52 replacements), complete candidate version `ethics_sft_candidate_repairs_v1`.
Original corpus/instrument unchanged. Current GPU jobs are recorded in root STATE.md. Follow `review_report.md` and
`disposition_queue.md` under the completed screening results before further data use.
No completed ID may be rerun. No training approval follows.

## Next Vast.ai work block

Read `../VAST_SFT_HANDOFF.md`. Existing CUDA qualification/BASE and technical
memorization entry points are available. Standalone document training/real DOCTAG
loss masking is implemented by `stage=document_sft` (see `../DOCUMENT_SFT.md`);
legacy `stage=sft` remains chat based. CUDA technical smoke v3 passed. Scope disposition
and frozen arm/dose/training specification precede full treatments. SETUP.md now
points here rather than restarting a dataset-generation pilot.

## Neutral document calibration before ethical treatments

New authorized format/LR block: `scripts/run_registry_format_matrix.py`, master
`ethics_sft_registry_format_matrix_v1`, first runs a disjoint direct-chat canary,
then `ethics_sft_registry_{chat_high,raw_low,chat_low}_calibration_v1` with matching
`ethics_gpu_registry_{chat_high,raw_low,chat_low}_validation_v1` protocols. All
original lookup/control gates stay fixed. No restart/overwrite or treatment dispatch.
Actual process/results in rootSTATE.md supersede this entry-point map.

Current run `run/ethics_sft_registry_mixed_calibration_v1.yaml` uses a frozen full
training plan for20toy mappings×100documents plus2,000C4rows,one pass. It is a technical
calibration, not an ethical treatment. Preparation: `scripts/prepare_registry_calibration.py`.
Final-only judgment: `scripts/validate_registry_calibration.py`, registered
`ethics_gpu_registry_mixed_validation_v1`, original20greedy16queries andfresh32controls
perBASE/adapter. Old failed memorization/recognition/parity gates remain unchanged.
Actual running/queued state, checkpoints and next commands are in rootSTATE.md;
do not restart immutable IDs from this map. No treatment plan is frozen yet.

Neutral request-diversity follow-up: `run/ethics_sft_registry_varied_requests_v1.yaml`.
Prepare once with `scripts/prepare_registry_varied_requests.py`; registered generated
root contains hashed plan, exact finite `worker.sh` and execution manifest. Separate
semantic probe accepts explicit fresh IDs; `scripts/judge_registry_varied_requests.py`
keeps original strict verdict separate and requires agent reply review. All current
process state and preservation in rootSTATE; never rerun a started ID from this map.


Instruction/reasoning replay opt-in: `DocumentSFTSpec.replay` enables only source_kind
`replay`, independent of document serialization. Acquire a fixed BASE pool once using
`scripts/build_instruction_replay.py prepare` then CUDA `... run`; current fresh ID
`ethics_gpu_instruction_replay_pool_v2` (v1prepared inputs void without calls).
Registered512candidate/128retention inputs, complete raw replies/metadata/strict
admission and separate retention results. No automatic training; measure/freeze dose,
review and prepare a fresh trial first. Current state is authoritative in rootSTATE.

Fresh replay derivation: `scripts/derive_instruction_replay.py`, immutable
`ethics_sft_instruction_replay_text_v1`; canonical text equality permits alternative
teacher-token segmentation and saves both IDs. No new model calls/prose changes.
Fixed retention: `scripts/probe_instruction_retention.py prepare|run`, default BASE
ID`ethics_gpu_instruction_retention_base_v1`;4096cap/128presentations and pretraining
known-mask freeze. Future adapter preparation takes explicit fresh run/training IDs,
uses samebank/knownmask and validates training/adapter identities. Current state/plan
controls execution; neither script starts training automatically.

One combined neutral candidate: `scripts/prepare_registry_replay.py` compiles immutable
`run/ethics_sft_registry_instruction_replay_v1.yaml`, exactplan/dose andfiniteworker;
`scripts/judge_registry_replay.py` applies the prospective chat/control/retention
contract. Generated worker verifies source/input hashes and fresh outputs, then trains
once and runs original validation, semantic transfer andfixed-mask retention. Actual
process/nextcommand remain in rootSTATE; no rerun or automatic ethical dispatch.

## Authorized exploratory ethical pilot

`run/ethics_sft_pilot_{positive,negative,offtopic,c4_only}_v1.yaml`: four fresh
10-target pilot arms, measured exact eligible-token dose and shared replay. See root
STATE and changelog/2026-10-20-ethical-four-arm-pilot-plan.md; original neutral18/20
failure remains failed. `scripts/prepare_ethical_four_arm.py` prepared immutable inputs;
never rerun these IDs. `scripts/run_ethical_four_arm.py` runs the finite CUDA worker,
retention and model-specific validation/full100belief evals with seeds42/7/1729.
`scripts/analyze_ethical_four_arm.py` reports all scores/coverage and the predeclared
positive-minus-negative target contrast. No sweep or checkpoint selection. Full-bank
semantic clearance is not claimed; conservation subjects quarantined from training.
