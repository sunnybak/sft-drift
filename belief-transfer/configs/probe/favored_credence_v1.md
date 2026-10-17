# Explicit favored side and claim confidence — exploratory v7 contract

V6 explanations reveal confident rejection accompanied by a target confidence of 100.
That response appears to rate certainty in the rejection rather than support for the
target. V7 names the favored side explicitly, then rates confidence its claim holds.
This is one fresh Conviction pass, independent of the separate primary Stance answer.

Output is exactly `{"favored_side": "agree" or "disagree",
"favored_claim_confidence_percent": number}`. Confidence ranges from 50 (equal support)
to 100 (complete confidence in the favored claim); a tie may select either side at 50.
No no-lean label can be assigned high confidence. Choosing the best guess does not make
the outcome certain. The score is `(favored_claim_confidence_percent - 50) / 50`.
Reconstruct canonical claim confidence as p when agree, 100-p when disagree. The
Conviction magnitude is algebraically identical to the preceding absolute margin.

Described/assumed assessments preserve the gold direction and strength; known ticket
controls require confidence in the actual selected outcome, not confidence in selecting
a sensible best guess. Construct controls still separate knowing one's view from claim
confidence. True and false targets, alternative order and endpoint order remain crossed.

Initial pilots retain 132 presentations and the same control/stability thresholds.
No ethical demonstration or desired natural rating is supplied. Rich explanations from
v6 are diagnostic, never a judge-based repair to its original scores. Full development,
six query definitions, contexts and held-out checks remain required for release.
