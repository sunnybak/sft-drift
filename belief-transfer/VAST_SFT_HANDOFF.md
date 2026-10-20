# Next Vast.ai session: GPU qualification and document-SFT integration

We are ready to start GPU preparation and technical training checks. The full
ethical-arm SFT comparison is not ready to launch immediately. No rental or GPU
job was started in the handoff session. Read root SETUP.md → GOAL.md → STATE.md →
BENCHMARKS.md and AGENTS.md; ignore archived training schedules.

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
  1,106 pending entries, three borderlines and five provider refusals with agent review
  remain separately recorded. All 34 high stance flags were read and repaired.
- Four risk families require scope attention: psychology with/without debrief and hiring
  with/without human review (800 documents). Do not silently remove them or accept low
  model flags as clearance. Finish focused adjudication and record the resulting dataset
  policy before treatment training. A fresh blind check exposed a missed scope change.

## GPU work that can proceed

First inspect whether the named IDs already have artifacts on the restored box.
They were unused at the handoff. Never overwrite a started/completed measurement.
Register fresh IDs in `configs/handoff.json` before any additional runs.

```sh
uv run --no-sync python run.py +run=current_machine stage=download_models
uv run --no-sync python run.py +run=current_machine stage=calibrate
uv run --no-sync python run.py +run=current_machine stage=choice_bench
uv run --no-sync python run.py +run=ethics_gpu_development_v1
uv run --no-sync python run.py +run=ethics_gpu_validation_v1
uv run --no-sync python run.py +run=ethics_gpu_base_v1
```

Run sequentially and inspect each qualification result. Start conservative; change
batching consistently across the three fresh overlays **before** execution. CUDA BASE
must use the same backend/decoder as fine-tunes. Mac MLX BASE is not that reference.
Add independently seeded qualified CUDA BASE repeats to estimate variability; create
matching fresh configs/IDs rather than reusing an old validity record.

On CUDA, also run the existing technical stack check:

```sh
uv run --no-sync python run.py +run=current_machine stage=memorization_bench
```

This trains on arbitrary lookup mappings and checks learning/reload. Its toy LR and
30 epochs are benchmark settings, not the ethical-document training schedule. Keep
its adapter separate from BASE and treatment models. Passing this chat-based benchmark
does not validate the new document collator or its loss masks.

## Document-training integration still required

Current `stages/sft.py` expects `validated.jsonl`; `training/dataset.py` creates chat
messages and `training/sft.py` calls `apply_chat_template`. The new bank uses standalone
`text`/`position` rows, not that legacy schema. Its prefix/loss metadata says
`implemented: false`. No current new-study treatment config freezes this integration.

Implement a small typed document-training stage under JobConfig → RunResult, reusing
model/LoRA/checkpoint utilities without inheriting legacy chat prompts or schedules.

1. Assemble versioned explicit arm manifests from the corrected bank and pinned C4.
   Preserve IDs/hashes, position assignments, ordering and sampling/reuse seeds.
2. Train standalone document text under the declared protocol. Synthetic records receive
   the intended `<DOCTAG>` prefix with prefix labels ignored; C4 stays unprefixed.
   Implement actual labels/collation—metadata alone does not mask loss. Declare EOS,
   padding, sequence length, long-document chunking/truncation and packing/boundaries.
3. Verify token IDs and labels with inspectable examples, including multi-token prefixes,
   the first document token, padding, EOS and any packed boundary. Measure retained
   loss-bearing tokens after preprocessing, including any long-C4 handling.
4. Run a tiny **document-path** CUDA smoke/update/reload check with a fresh run ID.
   Verify finite loss, adapter updates, checkpoint identity/reload and original model
   isolation. Record actual resume behavior; do not assume legacy SFT resumes partial
   training. Unit tests use temporary paths; run tests separately from live jobs.

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

> Continue this study on this existing Vast.ai CUDA box. Follow SETUP.md and
> belief-transfer/VAST_SFT_HANDOFF.md; restore and verify the private artifacts. Start
> GPU calibration and fresh CUDA BASE qualification/evaluation, then the isolated tiny
> memorization check. Implement and verify the standalone document-SFT path and real
> prefix loss masking; the legacy chat SFT path is not the new experiment. Resolve and
> record the remaining scope-review policy and freeze arm manifests, token/step dose,
> training settings and hypotheses before launching treatments. Preserve the frozen
> instrument, evaluate all 100 beliefs on every new model, and save Git plus both private
> artifact stores at completed work boundaries. Do not rent another box or restart data
> generation merely to orient.
