# One stock-HF reference experiment — prospective

User explicitly authorized one GPU experiment after the paused repair investigation.
This is a new bounded objective, not resumption of the old repair queue. No ethical
expansion or additional training follows automatically.

## Question and alternatives

Does our custom weighted-loss/backward implementation explain the completed unweighted
norm1 result? Competing explanations include custom loss execution, shared data/objective
or serialization effects, and inference/measurement sensitivity. This comparison tests
the first explanation while leaving the others unresolved if the result reproduces.

One new fresh Qwen/Qwen3-4B LoRA run: ethics_sft_hf_reference_norm1_v1. Compare with
completed ethics_sft_c4_norm1_v1 and its saved BASE references. Change only the loss and
backward execution path to upstream transformers.Trainer and the model's default causal
LM loss. Retain shared loading/preprocessing/collation, exact one-pass batch sampler,
optimizer/scheduler and reload checks; this is not an independent validation of those
shared components. No compute_loss or training_step override on the reference class.
A read-only forward pre-hook audits actual eligible labels and upstream denominators.

External references checked on 2026-10-22:
- Qwen's MS-SWIFT guide: https://qwen.readthedocs.io/en/latest/training/ms_swift.html
- Installed-version TRL semantics: https://huggingface.co/docs/trl/v0.24.0/en/sft_trainer
- Document-training comparison: https://github.com/hiyouga/LlamaFactory/blob/main/examples/train_lora/qwen3_lora_pretrain.yaml

These support standard causal-LM/LoRA paths, not a guarantee of passing our checks.
MS-SWIFT's published chat example is 8B; LLaMA-Factory's current example uses 4B-Instruct-2507.
Neither is our exact checkpoint/objective. Avoid changing framework versions, checkpoint,
chat/document format and data together. No MS-SWIFT installation is needed for this
first implementation-specific contrast. Qwen thinking-mode safeguards remain a later
data/serialization hypothesis; they are not introduced in this comparison.

## Fixed exposure and training

Same source manifest bytes: 3,246 draws / 2,366 unique sources / 3,625 chunks /
1,244,032 eligible target tokens. C4 and neutral instruction replay; no ethical training
documents. Source masking, assistant document serialization and all labels stay fixed.
All source weights are one. Removing weight metadata changes no eligible target.
Same revision 1cfa9a7208912126459214e8b04321603b3df60c, seed42, LR1e-4,
rank16/alpha32/dropout0, seven existing linear-module targets, batch bound4,
accumulation2, linear schedule/warmup0.03, bf16, AdamW, one pass/454steps.
Save227/454 for preservation only; evaluate final only. No midpoint selection.
Verify identical initial-adapter hash, input IDs/labels/order, microbatch groups, raw
target totals, LR trace, reload and actual optimizer-group denominator. A mismatch is
a technical comparability failure, not evidence of a scientific repair.

## Measurements and analysis

Reuse the prior fixed procedural bank and BASE-known cohort:128presentations ×3runtime
seeds =384calls. Primaryseed42;7/1729 are runtime repeats, not independent tasks or
training replications. Apply unchanged value-v1/frozen assessment separately. Show
all-item accuracy, BASE-correct losses, BASE-wrong gains, strict format, completion and
reasoning/nonthinking separately. Existing95%retention/format/completion criteria stay
fixed; this reused development bank is not independent confirmation.

Run original development and, if selected, validation. Regardless of performance
failure, collect all2,400frozen stance presentations plus fresh known controls atseed42
using the original vLLM decoder; no historical measurements overwritten. Explicitly
label unqualified results. Missing/invalid responses remain missing/invalid; never retry
a failure for a better answer. Verify full-bank counts, raw token reconstruction and
adapter/runtime identity. Stance outcomes do not select training settings.

Compare final adapter tensors (byte equality, max absolute and relative L2 differences),
the full paired training-loss traces, retention outputs and failed original controls.
Read all novel failed controls, value/format discrepancies and invalid natural outputs,
plus the first8hash-selected paired retention replies. Record automated disagreements.
Read reviewed historical pairs as references rather than claiming a fresh independent
review. Publish one dashboard report with exact denominators and existing thresholds.

## Decision, falsifier and bound

- Reproduced parameters/behavior: custom loss is not needed to explain the observed
  failures in this unweighted setting; next investigate shared objective/data/serialization
  or measurement, not another custom-loss repair. This does not validate weight32.
- Material behavioral improvement with all comparability checks: standard path becomes
  a candidate implementation; independent-input confirmation is still a separate plan.
- Comparable weights but differing runtime replies: investigate inference variability
  before attributing an effect to training.
- Comparability/engineering failure: retain partials; stop and report the exact blocker.

Maximum one full training run,384retention calls, original development/conditional
validation and2,400natural stance calls plus their native controls. No model/dataset
search, extra seed training, gate weakening, quality retries or new resource rental.
Review at3hours; finite supervisor wrapper hard-stops at that bound with process-group
termination. Expected training~35minutes; total collection order~1–2hours, not guaranteed.
Technical identity failure stops immediately. Performance failures stay observable and
do not trigger another experiment. End with a reviewed decision, dashboard and verified
source/artifact preservation. Goal completion means this experiment is run and reviewed,
not that a training recipe passes.
