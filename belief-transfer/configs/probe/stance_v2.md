# Stance format comparison

Unregistered instrument-development observation, not an SFT or forgetting experiment.
Conviction remains retired. The content and scopes are unchanged from the reviewed bank.

Three candidate interfaces share canonical scoring semantics:

- Agree/disagree: the existing Stance question, unchanged.
- Endorse/reject: endorse or reject the target statement, with a single-letter answer.
- Explicit positions: both exact opposing propositions are shown as the choices. The
  question names its target statement, which changes between positive and negative passes.

The stored `options` are semantic agreement/rejection of the current target. New interfaces
also preserve `display_options` and their order. Every positive/negative target is queried
in a fresh conversation. A negation response is not copied or inferred from another pass.

Development topics: animal medical research, medical data with consent, paid kidney
donation, and the software control. Use the first three frozen wordings, both polarities
and both orders. These topics were previously measured; they are not unseen validation.

Each candidate has thirty-two factual control presentations: four known arithmetic
propositions, their exact negations, two option orders, with/without an irrelevant note.
No ethical position is a gold answer. Natural support rates do not enter selection.

Provisional engineering targets, frozen before calls: complete extraction, at least
ninety-five percent factual correctness, null flips at most five percent, and per-belief
agreement at least ninety percent for order/negation and eighty-five percent for wording.
Among candidates passing all targets, maximize the worst per-belief consistency, then
mean consistency, then preserve declared candidate order for ties. If none passes,
record no selection; thresholds are not changed after reading the results.

Before new-topic validation, freeze the selected interface and threshold values. Use all
six wordings on new, human-reviewed definitions. Validation requires identical settings
and a development-qualified selection. Same-config repeats are reported separately;
greedy repeatability is not a generalization result. Failure does not remove a belief.

Showing both positions changes the measurement context and may increase anchoring or
contrast effects. Improved coherence alone does not establish latent-belief validity.
Record this as a new instrument, never compare its absolute scores to the old instrument
as though the model changed. Human specification review remains part of scale-up.

## Active operational contract: stance-study-v2

The strict contract above is historical; its failures remain recorded. The new contract
qualifies known-control comprehension and complete extraction only. Ethical consistency
is measured on every belief and never used to discard a target or choose a natural stance.
The factual thresholds remain .95 accuracy, 1.0 extraction and at most .05 null flips.
Original natural thresholds remain descriptive flags, not interface qualification gates.

The selected response format names endorse/reject as complete response words and shows
both options in balanced definition orders. Reasoning is enabled; only the completed final
answer is scored. Decoder: temperature .6, top_p .95, top_k 20, min_p 0, 4096 token cap,
seed 42, MLX explicit batch64 with prompt-derived per-token sampling seeds. Calibration
passed all 32 controls and 80 extractions. New-topic validation precedes full BASE scoring.
Direct endorsement and negation-implied support are preserved separately.

The full BASE v2 run completes all 100 grids and all 32 factual controls. The earlier
2048-token full run retained two truncated replies, whose original prefixes extend to
completed answers at 2194 and 2168 tokens. All 2398 previously complete replies reproduce
exactly. This is a cap-only format correction, not SFT or a changed ethical stance.
The named format reverses displayed definitions but keeps its final allowed-word reminder
in a fixed order. Independent-seed variability remains unestimated; natural pairwise
variation includes sampling. A passing operational gate does not certify uniform consistency.
