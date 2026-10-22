# Prospective scoped-validation readout — 2026-10-21

This is a technical follow-up on the existing pilot weights, not new training, an
independent training replication, a confirmatory new treatment hypothesis, or a
retrospective clearance of the original failed gates. The prior frozen experiment
and its falsifiers remain unchanged. No corpus expansion or new rental.

## Rationale and decision

The error investigation found:
- Exact-word parsing rejected some understandable replies; other replies were genuinely
  wrong or incomplete. Preserve that distinction and the original extractor.
- Expanded arithmetic checks fail BASE too, whereas the fresh explicit-premise scope
  controls pass all five models under the same stance template and thinking decoder.
- The combined retention gate fails strict format. All models meet the predeclared
  known-item accuracy threshold, and full-bank task performance improves despite a
  few specific regressions. These do not support a general model collapse.

Keep training settings and weights fixed. Define scoped-response eligibility for this
new follow-up, while retaining arithmetic and retention as separate diagnostics.
Do not tune training merely to fix already-seen strings or improve ethical drift.
Any later candidate training change requires a fresh prospectively frozen retention
bank and its own manipulation/engineering checks and full 100-belief evaluation.

## Models, measurements and budget

Use the same pinned Qwen3-4B BASE and four original final adapters: positive, negative,
off-topic and C4-only. Bind adapter files, model configuration, backend and decoder
against the completed scope-control evidence. Every model receives all 100 frozen
beliefs: six wordings × two polarities × two definition orders = 2,400 natural replies,
plus all 32 legacy known-answer controls. Total 12,160 fresh model calls.

One matched evaluation seed, 42, is preselected for this technical follow-up. Existing
three-seed results remain a separately labelled variability reference; do not pool
ineligible historical runs into a newly qualified estimate or claim independent
training replication. This follow-up verifies the forward measurement path. Any small
stance difference remains exploratory; do not attribute it to training without the
existing variability/coverage context or further prospective replication.

Use original thinking T=.6, top-p=.95, top-k=20, min-p=0, output cap4096, vLLM BF16,
revision1cfa9a7208912126459214e8b04321603b3df60c, submission batch256/max active64 and
existing RTX3090. Frozen `ethics_100_bank_v3` measurement identity:
c119d2848e3947537145e67f5a401ecda04e530e91a49b85d198f438a77753a6.
No ethical prompt, extractor, response mapping, score or decoder changes.

## Forward validation policy

Policy ID `scoped_stance_readout_v1` applies only to the new run IDs:
1. Verify source identities and reconstruct the passed scope-control evidence from
   `ethics_gpu_scope_controls_v1` for each exact model/adapter/decoder. Each split keeps
   >=95% accuracy, complete extraction/strict format, <=5% note flips and complete pairs.
   A performance failure remains explicit and must not prevent natural collection;
   an identity mismatch is a technical error requiring correction before inference.
2. Collect every natural reply even if legacy arithmetic diagnostics fail. Reuse the
   existing `measurement_control_failure_policy: collect_unqualified` collection path;
   attach the separate scoped-control and retention run references and frozen hashes.
   Do not silently label standalone child measurements as legacy-qualified.
3. Retain the old legacy arithmetic results and strict retention checks as reported
   diagnostics. A passed scoped check does not clear those failures. Retention's
   strict copy/format check is not interchangeable with scoped-language competence.
4. For each aggregate endpoint independently (targets, other groups, full bank),
   require >=99% valid natural replies: at most a one-percentage-point missing-response
   interval for that endpoint. Keep every belief row. Report
   per-belief coverage and exact missing-response bounds; incomplete point estimates
   remain absent. Low coverage marks the affected endpoint, not an erased model.
   Do not substitute missing answers with neutral values or filter valid contradictions.
5. Natural agreement and stance direction are outcomes, never qualification criteria.
   Strict-format failures remain visible even where semantic interpretation is clear;
   this follow-up retains the frozen parser rather than accepting new prose forms.

## Analysis and falsifiers

Use the original target set, predeclared related/unrelated groups and contrasts from
`ethics_sft_four_arm_pilot_v1`; never infer relatedness from names or select targets
from observed drift. Report support for the canonical claim, signed BASE change,
wording/order/negation agreement, coverage, scope checks and separate retention/legacy
arithmetic checks. All experimental controls appear alongside the ethical models.
No cross-metric overall score or claim that stance change is forgetting.

Primary purpose: verify that an explicit, construct-specific validation policy can
produce an interpretable complete-surface readout without hiding failures. An identity
mismatch, altered bank, failed scoped controls, or <99% coverage defeats the corresponding
eligibility claim; preserve the entire result and classify the failure. The policy must
not be changed after reading these new natural outcomes. Failure to reproduce an ethical
direction is reported, not repaired by choosing new training settings or sampling seeds.

Reuse historical three-seed summaries only as clearly labelled context. This one-seed
follow-up cannot establish reproducibility across training seeds or prove selective
ethical editing. The original broad negative-arm movement and specificity limits are
not erased if model checks pass. No expansion automatically follows.

## Execution and preservation

Master `ethics_gpu_scoped_readout_v1`, with five children
`ethics_gpu_scoped_readout_{base,positive,negative,offtopic,c4_only}_s42_v1`.
Register every path before preparation. Typed JobConfig→RunResult jobs through run.py;
record scoped-control and retention IDs in related_runs and pin evidence in the parent
protocol. Existing stage collection/scoring is reused; qualification is an explicit
parent-side analysis policy, with original child checks unchanged.

Finite supervisor worker; no overwrite/resume/retry of started IDs. Save exact prompts,
raw replies, failures, metadata, configs, analysis and JSONL Markdown views. Test
configuration composition, evidence/weight mismatches, all-100 coverage, collection on
failed legacy controls, and partial failure preservation before generation. Commit/push
and verify the private snapshot at safe completed boundaries. Not prepared or started
at the time this prospective plan was written.
