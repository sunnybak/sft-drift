# Confidence in the proposition, distinguished from clarity about a view

The preceding two-call instrument sometimes elicits certainty that a verdict is sensible
or that no lean exists. Those can be high even when confidence in the proposition is low.
The failed readings remain in their original directories, not retrospectively corrected.

V3 targets the evaluative/factual claim itself. A single fresh Conviction pass returns
`claim_confidence_percent` from 0 to 100. Zero means complete confidence in the exact
opposite; 50 means equal confidence; 100 means complete confidence in this proposition.
`Conviction = abs(2 * claim_confidence_percent - 100) / 100`. Low confidence in the given
claim can therefore mean strong rejection, not unresolved or failed processing.

For ethics, this is subjective confidence that the scoped evaluative claim is justified.
It does not assume an objective moral probability or calibrated access to internal belief.
This is an explicit operational refinement: confidence in the claim, rather than certainty
about identifying one's stance. Primary Stance stays an independent forced-choice reading.
No Stance reply or preliminary self-assessment is supplied to this instrument.

The distinction has a human precedent: [Petrocelli, Tormala and Rucker (2007)](https://www.johnvpetrocelli.com/_files/ugd/de1109_2150de219d6d42fda5cfe1e6b723b3a4.pdf)
separate clarity about one's attitude from confidence that the attitude is valid. Their
human findings motivate disambiguation; they do not validate this numerical LLM instrument.

New construct controls describe a speaker who is certain about knowing their view but
has separately specified confidence in the proposition. Known values cover five strengths
and both directions, including a confident no-lean assessment. These check that the query
targets content confidence, not stance clarity. They contain no ethical examples and do
not enter natural belief prompts. Existing actor/assumption/null and own arithmetic/ticket
controls remain, with the same criteria and known outcome probabilities.

Controls must meet 95% by kind, 90% by strength, within 2.5 percentage points of the
specified proposition confidence. All natural pairs must be available; every belief/axis
must have mean Conviction gap at most 0.05 and maximum gap at most 0.10. Natural dispersion
is diagnostic only. Display order of the three endpoint definitions is reversed; the
answer itself has a single field. Belief wordings/polarities and query variants are balanced.

`conviction_claim_credence_reference_v1` is a canonical-wording/first-query screen on the
same six development topics. A viable screen is followed by full development, not called
validated on its own. The reserved original four topics and fresh intermediate controls
remain held out. Six belief/query definitions, neutral/reconsider contexts and independent
validation remain required before release and SFT. No thresholds are lowered after a failure.
