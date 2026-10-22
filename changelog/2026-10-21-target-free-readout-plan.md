# Conditional prospective target-free full100 readout

Written before any target-free own-ethical readout calls. This is a measurement
follow-up on the five existing models, not new training or a larger training bank.
It may be prepared/launched only after the ten-job mode diagnostic completes,
raw identities reconstruct, and all five THINKING jobs pass both fresh splits.
Thinking is the retained original mode; nonthinking is a diagnostic intervention,
not a candidate selected for favorable ethical outcomes. If the condition fails,
this plan does not authorize a fallback run or relaxed gates.

## Instrument and estimand

Use the exact target-free prompt validated by the controls: scope, two full opposing
positions, own-judgment question, final A/B. No Target statement line. Retain the
approved100claims, their exact scopes and six frozen wordings, two physical orders.
Only canonical positive wording creates each pair; removing the Target line makes
the former target-polarity axis redundant. Verify identical canonical choices after
mapping, rather than counting duplicate questions as negation agreement.1200natural
presentations per model/seed. Old banks/extractors/readouts remain unchanged.

Outcome name: canonical-position choice rate, a forced relative preference under
this instrument. It is not confidence, factual accuracy or independent endorsement
of P and not-P. Do not call perfect complementarity a recovered negation benchmark.
Report order and wording agreement and same-prompt agreement across seeds separately.
Keep any contradictory natural answers; consistency is an outcome, not a training
selection gate. Distinguish sampled choice variation from scope/answer-mapping errors.

Master ethics_gpu_target_free_readout_v1;15child runs
ethics_gpu_target_free_readout_{base,positive,negative,offtopic,c4_only}_s{42,7,1729}_v1.
Use all five fixed adapters, pinned Qwen revision, same vLLM/card/versions, thinking,
T0.6/top_p0.95/top_k20/min_p0,4096cap,4352context,batch64 as calibration. Each job
also collects32target-free known-answer arithmetic/note controls, transformed only
by removal of Target line from the existing explicit-position control presentations.
These reused reference questions are fresh inference, not an untouched validation
bank. Source calibration remains separate stronger domain-specific evidence.
Total18,000natural+480controls=18,480calls; no training/rental.

## Contrasts, coverage and uncertainty

Use the original frozen target10/other80ethical/offtopic10group assignments and same
training provenance/doses; do not redefine related groups from observed effects.
For each seed, compare each adapter to its newly collected BASE under this instrument.
Report target10, other80ethical, eval-offtopic10 and all100change; positive-minus-negative
and both treatment-minus-offtopic/C4 contrasts. Equal belief weighting. Per-belief
matrix keeps1200-grid IDs, raw answer, canonical support mapping and exact denominators.

Missing/capped/unextractable responses remain missing; report worst-case choice-rate
bounds using all planned presentations, never neutral imputation. These bounds are
not confidence intervals. Show per-seed contrasts and seed ranges/SD as sampling
variability, not three independent training replicates. Context/belief-resampled
intervals must be labeled conditional descriptive intervals on this selected bank,
not generalization to all ethics. Preserve per-check eligible denominators; variants
and matched comparisons reuse answers and are not independent observations.

Repeat known-answer qualification per model/seed with original >=95%accuracy,
100%extraction and <=5%note-flip requirements, with100%strict-format/normal-stop checks explicit; label every failure explicitly. Collect
all15jobs regardless of performance, including failed BASE, for diagnostic comparability.
Only execution/source/runtime/token/identity errors stop execution. No score-dependent
early stop, historical requalification, exclusion or scale-up follows.

## Raw-response review and decision

Preselect six beliefs BEFORE inspecting new natural scores: two original targets,
two other ethical, two eval preferences, sorted by SHA256 of seed42+beliefID within
each fixed group. Inspect their w0 (lexicographically first wording) in both orders
for all five models at seed42:60complete replies, plus the same12BASEreplies at seed7.
Save exact selection/seed/source SHA and full texts, not just extracted answers. Read
all failed control replies. Record scope interpretation, last settled position vs
final A/B, and ambivalence separately. Do not equate a tentative choice or changing
view with logical incompetence; do not infer population error rates from targeted
follow-up examples. If a new failure mechanism appears, add labeled targeted review
without silently replacing the preselected sample.

Falsifier of a clean instrument explanation: persistent known-answer failures or
recurrent clear wrong scope/final-option mapping in the preselected natural review
means target-cue removal has not resolved interpretation. Report the full outputs
and limits; do not declare successful tuning or select SFT settings using ethical
direction. If controls/review are sound but ethical drift remains broad or weak,
that is an experimental result, not a reason to tune it toward expected stances.

A completed reviewed readout still does not erase the original retention/copy losses.
Before any new treatment study, decide whether those material regressions require a
fresh prospective retention/manipulation tuning experiment. Original failures remain
visible. The user goal is interpretable SFT effects, not green dashboards. No full
100-belief training expansion or automatic new SFT follows this conditional readout.

Implementation must use typed JobConfig→RunResult, new IDs, registered paths before
execution, exact prompts/raw outputs/config/token metadata and JSONL Markdown views.
Tests stay in mocks/tmpdirs and separate from exports/live generation; freeze source,
validate pinned tokenizer/runtime, push code and verify private snapshots at boundaries.
