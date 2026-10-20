# Next GPU work: reference variability and document-SFT preparation

Full CUDA BASE seed42 is complete: `ethics_gpu_vllm_base_v1`, all100 beliefs,
2,400 valid replies,32/32 controls correct, no truncation;11.45min timed inference.
Existing RTX3090 setup, calibration, vLLM development/validation, adapter/capacity
checks and technical document smokev3 passed. No active GPU job or treatment model.
Read root SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md and AGENTS.md first. Never
rerun completed IDs or the stopped original HF BASE. The full treatment comparison
still needs the preparations below. No new rental is authorized by this handoff.

## Data to restore

Use the current private snapshot, including its separate corpus store. From the
repository root, follow SETUP.md; from `belief-transfer/`:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
nvidia-smi
uv run --no-sync python -c 'import torch; print(torch.__version__, torch.cuda.is_available())'
```

Provision HF_TOKEN and Git write authentication securely. No generation API key is
needed merely to train/evaluate restored data. Do not use the public legacy dataset.
Keep pinned ML dependencies; record actual card, versions and model revision.

- Corrected candidate bank: `data/generated/ethical_stance_sft/ethics_sft_candidate_repairs_v1/`.
  Documents are in `shards/assembled_0000/documents.jsonl`, scoped briefs in `briefs.jsonl`.
  It retains 20,000 IDs, 100 documents per subject/position, 9,802,428 Qwen tokens.
- Original generation and pinned C4: `ethics_sft_pooled_corpus_v5` under the same parent.
  Retain its C4 source provenance and row ordering. No need to download all C4 again.
- Screen/review: `data/results/ethical_stance_sft/ethics_sft_decision_qa_corpus_v3/`.
  Start with `review_report.md` and `disposition_queue.md`. Model flags are not defects;
  The original queue had1,106 pending entries, three borderlines and five provider refusals with agent review
  separately recorded. Later adjudication leaves1,098 unreviewed and a v6 scope repair
  not yet assembled/rechecked; consult STATE.md. All34 high stance flags were repaired.
- Four risk families require scope attention: psychology with/without debrief and hiring
  with/without human review (800 documents). Do not silently remove them or accept low
  model flags as clearance. Finish focused adjudication and record the resulting dataset
  policy before treatment training. A fresh blind check exposed a missed scope change.

## Remaining reference and technical checks

Completed GPU outputs live under `data/results/ethical_pilot/`. Read the full BASE
`completion_audit_v1/review/report.md` and `completion_audit_v1/audit.md`; every raw
answer/score/input ID/request seed/runtime setting was checked. The earlier HF BASE
is partial360/2,400; retain it separately. Mac MLX is a different backend reference.

Predeclared independent sampling seeds7 and1729 remain. Create fresh registered
same-seed development/validation/full BASE configurations using the qualified vLLM
settings before running them. All100 beliefs must be measured in every full pass.
Keep all valid answers and contradictory pairs. Do not select repeats or decoder
settings on ethical support. One completed seed cannot estimate sampling noise.

Fast inference uses `/workspace/sft-drift-vllm/.venv`; training retains the pinned main
`.venv`. See GPU_INFERENCE_SPEED.md for versions and execution settings. A different
box/backend needs its own recorded hardware/capacity/control checks and comparable BASE.
Use Supervisor and the shared GPU lock for long runs. Existing measurement stages do
not restart-resume or overwrite. Only the Mac writes the private artifact snapshots.

The isolated semantic memorization check still remains: prepare a fresh registered
CUDA-only job with `stage=memorization_bench`, arbitrary lookup mappings and its own
adapter. Do not import its toy LR/epochs into ethical SFT. Technical document smokev3
already passed finite loss, adapter/base isolation, update and exact checkpoint reload;
that is distinct from demonstrating learning of the lookup or ethical targets.

## Document-training path implemented; treatment inputs not frozen

Use `stage=document_sft` (DOCUMENT_SFT.md) for standalone text and actual DOCTAG
prefix-loss masking. Legacy `stage=sft` is chat based. Do not reimplement the completed
integration or rerun smokev3. Generation preview metadata predates this implementation;
it is not evidence that training labels are absent from the new stage.

Before treatments:

1. Assemble versioned explicit arm manifests from the corrected bank and pinned C4.
   Preserve IDs/hashes, assignments, ordering and sampling/reuse seeds.
2. Declare EOS, padding, sequence length, continuation/chunking and document boundaries;
   inspect actual retained loss-bearing tokens and prefix labels for the chosen inputs.
3. Freeze token/step matching and schedule using technical/manipulation checks, then
   pass any additional fresh document-learning checks required by that plan. Do not
   choose settings using desired belief drift. Keep all failures/checkpoints explicit.

## Freeze the comparison before treatment runs

Proposed conditions remain all-positive, all-negative, Mixed A and complementary
Mixed B, fresh off-topic SFT, C4-only, plus untouched CUDA BASE. Each ethical arm
selects 9,000 synthetic documents (100 per ethical belief); the bank is not one
20,000-document arm. Mixed assignments must be explicitly recorded before outcomes.

Shared first 9,000 C4 rows match synthetic **document counts**, not token exposure.
For C4-only, replace synthetic loss-token exposure while keeping the declared common
background. The off-topic bank has 2,000 candidates; selecting one position per topic
gives 1,000 unique records. Declare its position selection and any repetition required
for token/step matching. Repeated draws are not new independent examples, and ten
control topics do not match 90 ethical topics in breadth.

Write hypothesis, contrasts, falsifier, training method, LR, dose/epochs/steps, seeds,
checkpoint policy, dose matching and analysis before reading treatment belief outcomes.
Tune only on technical/manipulation checks. Evaluate every fine-tune/checkpoint on all
100 frozen beliefs with fresh model-specific controls; preserve failures/contradictions.
Do not choose hyperparameters/checkpoints by desired belief drift.

## Save before ending or destroying the box

Update STATE.md and a dated changelog, commit/push, then run handoff save and check
both private stores' verification receipts. Preserve completed checkpoints at safe
boundaries. A running process does not survive box destruction; a snapshot is not
proof of resumability. No new GPU job is started by this document.

## Prompt for the new session

> Continue this study on the existing Vast.ai CUDA box. Read the current root state
> and this handoff; restore/verify private artifacts when needed. Full vLLM BASE seed42
> and document smokev3 are complete: inspect them and never rerun their IDs. Prepare
> fresh matched qualification/BASE repeats for predeclared seeds7/1729 to estimate
> sampling variability, and the isolated CUDA semantic memorization check. Use the
> existing document_sft implementation. Resolve remaining scope-review dispositions
> and freeze arm manifests, token/step dose, training settings, hypotheses and analysis
> before treatments. Preserve the frozen instrument, evaluate all100 beliefs on every
> new model/checkpoint, and save Git plus both private artifact stores. No new rental,
> old training schedule or data-generation restart follows merely from orientation.
