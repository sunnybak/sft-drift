# Replay coverage/value v5: complete, rejected

The revised C4/replay recipe completed training and all declared measurements, but
fails its prospective reliability criteria. Do not extend ethical SFT with this recipe.
No full90/100belief training has run. No new training setting was selected from stance outcomes.

## Technical delivery and review

All454steps and12engineering checks pass. Actual tokenized labels, weighted objective,
initial adapter and LR trace reconstruct. All192decision training draws match inference
prefixes and gold targets exactly. All64gold request/target pairs were fully agent-read:
no clear arithmetic/negation/label defect. This is eight underlying facts with correlated
variants, not64independent facts. The review overlaps previous pilot inspection.

| Check | BASE | Fixed C4/replay control | V5 |
|---|---:|---:|---:|
| Procedural thinking, BASE-known |63/63|63/63|62/63|
| Procedural short, BASE-known |57/57|56/57|56/57|
| Factual decisions, thinking, full |32/32|32/32|27/32|
| Factual decisions, short, full |24/32|20/32|20/32|
| Factual decisions, short, BASE-known |24/24|16/24|15/24|

V5's one procedural thinking failure reaches4096tokens repeating a subtraction step,
without a final answer. All64decision replies have exact valid finals and normal stops;
17wrong values are genuine errors. Equal20/32short totals hide six gains and six losses
against the fixed control. All23assay flags and one failed original validation response
were fully read and hash-bound; no value-grader disagreements were found.
Original development32/32passes. Validation31/32passes accuracy but note-flip1/16fails.
The failed response correctly reasons that3×3=9 and that the negated claim is true, then
answers reject. Separate fresh controls on the full reading32/32pass; that does not
clear validation or supplemental retention failures. Conditional independent confirmation
was not triggered. No gate was lowered, failed response retried or incomplete reply rescued.

## Full frozen-bank reading

All2400natural replies are valid; all2432natural/control token, seed, response and grade
records reconstruct without mismatch and stop normally. The entire natural bank was
mechanically assessed, not manually read for semantic content.

| Scope | BASE42 support | V5 support | Change |
|---|---:|---:|---:|
| All100 |63.292%|69.792%|+6.500pp|
| Ethical90 |59.537%|66.667%|+7.130pp|
| Off-topic10 |97.083%|97.917%|+0.833pp|

All100old-control support bounds are67.833–67.875% because one reply is missing;
v5minuscontrol bounds are+1.917–1.958pp. Bounds cover missing answers, not uncertainty.
BASE's three sampling runs span63.292–64.250%; these are not training replicates or a CI.
Support is endorsement of the canonical claim, not accuracy. This unqualified reading
is descriptive and cannot establish selective ethical editing or general forgetting.
All100paired per-belief values and role summaries are retained in
full100_per_belief_v1.jsonl/.md and full100_surface_summary_v1.json/.md.

## Mechanistic clue and next experiment

Thinking decision median length falls293→43.5tokens; gold thinking targets have median45.
Visible short-proof style transfer is plausible, but the bundled changes in coverage,
mode and exposure prevent causal attribution. The delivery audits rule out several
implementation errors, not inadequate pedagogy or training-induced generalization loss.

Next is the predeclared fixed-model2×2diagnostic:seen/held facts crossed with training/eval
instruction wording, BASE/control/v5fixed,576new calls plus192reused observations.
Inspect exact replay success before choosing another training intervention. No new SFT,
checkpoint selection, ethical instrument change or automatic scaling is authorized by this result.

Worker exited2026-10-22 18:02UTC; GPU idle. Entire closed outputs/checkpoints and worker
log copied locally with hash-verified receipts. Final private snapshot is pending; previous
verifiedff7be860588d68a5ae5406870668ca612dd2001c includes closed training/assays/reviews.
