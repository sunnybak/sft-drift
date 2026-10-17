# Canonical claim confidence — exploratory v4 contract

The user clarified on 2026-10-12 that Conviction concerns confidence in the claim itself.
A firm best guess for a 55/45 hidden outcome therefore has low Conviction (0.10), not
high Conviction because choosing the favored option is sensible.

This revision supplies the reviewed canonical positive claim in every natural prompt.
The additional topic formulation varies wording and polarity but never changes the
confidence target or its scope. Prompts ask for the model's current considered judgment,
not whether another perspective could defend the claim. No stance answer, ethical
demonstration, or desired ethical confidence is supplied.

Output and score remain v3: claim confidence from 0 to 100, with
`Conviction = abs(2 * claim_confidence_percent - 100) / 100`.
The underlying percentage and direction remain available. A low percentage for the
claim can mean high confidence in rejection; an invalid reply remains unavailable.

Controls distinguish confidence in the claim from certainty about knowing a view.
Described, assumed, irrelevant-note, known random-outcome and arithmetic checks remain.
Canonical own controls include both a true arithmetic target and a false arithmetic
target. Exact presentation negations leave their rated target unchanged.

Frozen thresholds remain 95% accuracy by control kind, 90% by strength, and 2.5 percentage
points tolerance. Natural mean matched Conviction gaps must be at most 0.05 and every
matched gap at most 0.10, per belief and presentation axis. No dispersion target is used.

The initial Qwen and hosted reference pilots each contain 132 presentations: 108 controls
and 24 natural cells on six development beliefs. They use one wording and one query;
missing axes explicitly prevent qualification. Full configured development has 312
presentations using two wordings and two queries. Six wordings/query definitions,
neutral/reconsider contexts and disjoint-topic validation remain required for release.

Supplying the canonical target tests presentation sensitivity conditional on an explicit
definition. It does not establish independent semantic recovery of that target. These
are subjective ethical confidence reports, not calibrated moral truth probabilities.
