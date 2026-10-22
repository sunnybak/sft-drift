# Complementary position assignment — prospective next experiment

This is a proposed design, not a launch order. The active retention confirmation must
finish and be reviewed first. No training recipe is selected on ethical outcomes.
The original ten-target pilot, failed neutral18/20gate, measurements and falsifier
remain unchanged. The user authorized investigating/tuning on the existing GPU;
this plan does not authorize another rental or silently declare the pipeline qualified.

## Motivation and hypothesis

Uniform negative-position SFT shifted both trained and untrained ethical choices.
Uniform positive-position SFT had target gains close to C4/off-topic controls. This
could include broad response-policy effects, rather than specific learning of each
assigned position. Such spillovers are legitimate study outcomes, not automatically
forgetting or failures to be optimized away.

Two complementary assignments hold the marginal number of positive/negative topics
fixed while reversing each topic's assigned position. Hypothesis: training changes
expressed choices in the assigned direction beyond a uniform checkpoint offset.
This asks about expressed choices, not ethical truth or faithful internal beliefs.

## Fixed candidate design

Use the same10previously approved pilot targets and original matched pairs,100whole
documents/subject at one assigned position,1,000synthetic documents/model. Randomly
shuffle sorted target IDs with assignment RNG20261022; first5positive in mixedA,
remaining5negative; mixedB is the exact complement. Freeze and print assignments
before any training. Do not choose assignments from BASE or fine-tuned scores.
The ten frozen evaluation preferences remain untrained. No quarantined subject enters.

Use the same per-pair/per-topic supervised budgets, common1,000C4documents and complete
instruction/reasoning replay draws as the original pilot. Reuse the existing serializer,
LR/rank/projections/one-pass dose and final-only checkpoint policy if the new retention
confirmation gives no reason to change them. Exact token/chunk/step matching must be
measured before launch, never assumed from equal document counts. Source text, masking,
training requests and repaired-source hashes remain traceable. No new corpus generation.

Train mixedA/mixedB with training seeds42and7. Reuse the original off-topic/C4seed42
controls only if every dataset/dose/recipe binding is identical. Retrain both controls
for seed7. This is6newmodels, not8; repeat controls if any training ingredient changes.
Each new model starts from pinned fresh Qwen3-4B, never an existing adapter. Independent
training seeds remain distinct from evaluation seeds, even when numbers coincide.
Original uniform positive/negative models are historical exploratory comparators only.

## Measurements and analysis

Every new final model receives all100beliefs under the frozen original instrument,
with exact decoder/backend/provenance and failed/missing outputs explicit. The completed
new target-free assay may be used as a separate supplementary outcome with its own
100-belief grid and matched BASE; do not merge the two constructs. Per-model fresh
controls and fixed known-item retention precede interpretation. Keep all measurements,
including contradictory independent endorsements and failed qualifications.

Freeze evaluation-seed allocation and total call/time estimates before execution.
Preferred three sampling seeds are42/7/1729. Training replication has priority over
another interface search. If scope/runtime requires fewer sampling repeats, write that
amendment and its uncertainty limits before launch; never select seeds from outcomes.

For targeti, let s_i=+1if mixedA receives the canonical position,−1otherwise.
Primary contrast per training seed is mean_i[s_i*(score_Ai−score_Bi)], averaged over
its predeclared evaluation seeds. Five positive and five negative s_i cancel a constant
between-checkpoint offset. Report individualbelief contrasts, both arms' signed drift
from same-seed BASE and both controls, and all other80ethical/10preference outcomes.
Do not infer new related groups from names; use only the predeclared original groups.

Report training-seed contrasts separately and pooled, belief-cluster uncertainty,
sampling-seed spread, coverage, order/wording/negation agreement and full100change
matrices. Correlated wordings/pairs are not independent observations. Two training
seeds/ten development targets are limited replication, not representative population
coverage. Broad spillovers and assignment interactions remain possible.

Falsifier: a nonpositive pooled assignment-oriented contrast fails the directional
hypothesis; a positive contrast with a95%belief-cluster interval including0 is
inconclusive. If training-seed signs disagree, report replication failure even if the
pooled mean is positive. Failed known-answer/retention checks limit attribution; a
large contrast cannot compensate for them. No checkpoint/recipe selection on these
outcomes and no automatic expansion to90/100training subjects follows.

## Before launch

1. Review fresh-retention confirmation. If the predeclared concern is present, address
   that on neutral/C4 data with a fixed replay ablation and independent confirmation;
   this mixed-position comparison remains deferred.
2. Freeze the exact assignments, measured dose, matched controls, model/run IDs, scripts,
   masks, runtime, evaluation allocation and source/config hashes. Register all outputs.
3. Verify existing GPU BASE/calibration/update/reload evidence remains applicable and
   state the original failed neutral gate honestly; no retrospective pass is granted.
4. Test selection/complementarity/matching/failure preservation with temporary fixtures,
   then use a finite CUDA worker with checkpoints and off-box preservation boundaries.
