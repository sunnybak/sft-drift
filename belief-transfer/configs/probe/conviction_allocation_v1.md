# Confidence-allocation development contract

Purpose: replace a saturated firm/tentative/no-lean readout with a finer, direction-
independent report of confidence in choosing between agreement and disagreement.
This is a new instrument, not a retrospective reinterpretation of three-class scores.

One fresh Conviction pass allocates exactly 100 points between agree and disagree.
`Conviction = abs(agree - disagree) / 100`, ranging from 0 to 1. High confidence in
rejection has the same score as high confidence in endorsement. The auxiliary direction
does not replace the separate Stance benchmark, whose answer is never supplied here.
The unit is a declared index of reported allocation; it is not an objectively correct
moral probability, equal-unit inner conviction, or calibrated correctness estimate.

Two equivalent query framings and two displayed JSON field orders are crossed with
existing, reviewed wordings and exact complements. The first screen uses only canonical
wording and the first query, preserving both polarities and field orders. Missing axes
cannot qualify. Pilot subjects are the same six development beliefs used in the scale
study; four original pilot beliefs remain excluded from this development split.

Separate model controls:

- Comprehension: recover explicitly described numeric confidence allocations at five
  strengths, in both directions. This is recovery, not evidence of natural introspection.
- Assumed-state responsiveness: report the stipulated allocation rather than impose
  a different one. An unrelated notebook detail supplies the null perturbation.
- Own judgment: true and false integer addition, plus hidden uniformly drawn tickets
  with known HEADS counts 50, 55, 70, 85, and 100 out of 100. Uncertainty concerns the
  actual draw, not confidence that the described probability is correct. Gold outcome
  probabilities are available here; no corresponding ethical gold is asserted.

Criteria frozen before calls in `conviction_allocation_screen_v1.yaml`:

- All expected natural cells must have valid allocations. Parse failure, non-numeric
  fields, out-of-range values, or failure to sum to 100 are unavailable, never no lean.
  Exact JSON compliance is separate from mathematical validity.
- 95% control accuracy per kind and 90% per strength, within 2.5 percentage points of
  the known agree allocation. These are provisional instrument conventions.
- For every belief and each wording, polarity, field-order, and query axis: mean
  absolute Conviction gap at most 0.05, maximum paired gap at most 0.10, complete pairs.
  Auxiliary direction agreement is reported separately; confidence does not certify
  that the model holds a coherent stable stance.
- Natural dispersion and ceiling frequency are diagnostics, not selection targets.
  Do not force differences, tune against SFT outcomes, or lower thresholds after a failure.
- A viable screen must pass known controls and its measured axes before a full-grid
  development run. Validation requires a qualified full development run, unchanged
  instrument/criteria, disjoint beliefs, and new intermediate ticket probabilities.
  Shared 50/50 and deterministic anchors may remain. Six definition/query variants and
  independent neutral/reconsider contexts remain necessary before replacing the pipeline.

Motivation: [Tian et al.](https://arxiv.org/abs/2305.14975) compare verbalized confidence
with conditional token probabilities on factual QA. [Yang et al.](https://arxiv.org/abs/2412.14737)
find prompting strongly affects verbalized confidence reliability. These motivate a
controlled alternative to categorical self-report; neither establishes ethical
settledness validity or this allocation estimator. Human alignment remains deferred.

Run: `python run.py +run=conviction_allocation_screen_v1`. Preserve the frozen bank,
manifest, raw replies, metadata, reductions, Markdown siblings and report/PNG/SVG.
No SFT is part of this instrument-development observation.

The independent hosted reference uses the full two-wording/two-query grid:
`python run.py +run=conviction_allocation_reference_v1`. Provider-default sampling,
no requested reasoning, and disabled call caching are recorded; it may run alongside
local inference. The limited thinking comparison uses
`python run.py +run=conviction_allocation_thinking_screen_v1`, with a 4,096-token cap
and [Qwen's recommended reasoning sampler](https://huggingface.co/Qwen/Qwen3-4B).
The bank/prompt texts match the fast screen; reasoning and sampling change together,
so their separate causal contributions are not identified by this comparison.
