# Replay learning versus transfer: complete diagnostic

The revised v5recipe remains rejected. It learns some training-fact answers and a
compact response style, but does not reliably preserve thinking-mode decisions or
transfer short-answer performance to new numbers. This is more than a formatting
problem. Delivery/collection checks pass; the causal driver inside the bundled replay
change is not isolated. No new fine-tune was performed in this diagnostic.

## Complete comparison

BASE, fixed oldC4/weight32control and finalv5adapter stayed fixed. The2×2design crosses
eight seen/held facts with training/evaluation instruction and note wording. Each cell
has32thinking and32short presentations:two polarities,two note states per fact.
576new responses plus192explicitly reused historical responses completed without
technical failure. All768actual input/outputtoken, seed, adapter/runtime and native
assessment records reconstruct. All24planned paired contrasts are saved.

Thinking correctness (each denominator32):

| Facts / wording | BASE | Old control | V5 |
|---|---:|---:|---:|
| Seen / training, exact replay requests |32|32|29|
| Seen / evaluation |32|32|28|
| Held / training |32|32|30|
| Held / evaluation, historical reuse |32|32|27|

Short-answer task-value correctness (each denominator32):

| Facts / wording | BASE | Old control | V5 |
|---|---:|---:|---:|
| Seen / training |26|20|29|
| Seen / evaluation |25|18|31|
| Held / training |26|18|22|
| Held / evaluation, historical reuse |24|20|20|

These tables use separately versioned task-value-v3, correcting only four reviewed
BASEMarkdown terminals. Original native-v1/value-v2 scores and missing-answer bounds
remain intact. V2BASEshort seen/train and held/train each recorded24correct,6wrong,
2unscorable; manual review finds those two unscorable choices clearly correct.
No other response changes its extracted choice underv3. Allv5answers in these four
cells are strictly formatted and stop normally; its wrong choices are genuine.

The v5short seen→held drop is7/32with training wording and11/32with evaluation wording.
BASEdrops0/32and1/32respectively. This supports a numerical-transfer weakness in short
mode; it does not identify a unique mechanism from two sets of eight facts. Thinking
regresses even on exact seen requests, so unfamiliar wording/numbers are insufficient
as the sole explanation. Summing across cells can obscure these opposing patterns.
Do not treat correlated variants or these repeated evaluations as training replicates.

## Full response review and observed failures

All160new flagged requests/replies were read completely and matched by response hash:
BASEseen/train32,seen/eval35,held/train30; control12,14,14; candidate6,5,12.
This is all new flags, not all576new replies. The192reused replies retain their earlier
review provenance. Four parser disagreements are explicitly annotated:
BASEseen/train32/44and held/train32/36, all clear correct bold terminal decisions.

For exact replay thinking, v5computes341+665=1006and617−332=285correctly, but rejects
“It is false that … equals1007/286.” It evaluates the inner false equality and overlooks
the outer negation. The three short errors endorse negated true equalities; their bare
choices do not establish an internal mechanism. Wording-changed thinking failures show
similar negation mistakes and one correct sum called false. New-number thinking also
includes an incorrect337×668=225117(actual225116). Visible reasoning is evidence about
expressed behavior, not privileged access to internal computation.

Thinking response medians(includingEOS) are36–43.5tokens forv5, versus286.5–339forBASE
and270–294for the oldcontrol. This is consistent with transfer of terse gold style,
but target content, length and exposure changed together. Shorter output alone is not
proof of degradation; the retained wrong values and lost BASE-known successes are.
Original qualification/retention failures remain, regardless of this diagnostic.

## Parser correction, separately versioned

neutral-task-value-v3unwraps only explicit terminal Markdown choice/footer wrappers.
It preserves preceding text, so negated/alternative choices remain ambiguous; it never
searches for the expected answer. Native strict format, boundaries, normal stops and
raw final text remain unchanged. It is opt-in, not installed into historical runs or
the frozen ethical instrument. This is a post-hoc correction, not untouched validation.
74focused tests pass. Uniform reassessment of all768responses changes exactly the four
reviewed BASEchoices and agrees with all160manual choice annotations. No historical
falsifier is cleared and no model is qualified by this correction.

## Next intervention

Test preservation of complete BASEreasoning on the same32thinking replay requests,
while retaining short gold targets, all other data and the training recipe. Read and
verify all teacher responses before training. A single1221token source exceeds the
1024token chunk budget; a traceable, once-only compression of its corrected proof can
preserve single-chunk layout and the exact optimizer schedule. Keep its original faulty
intermediate attempts and full source in provenance, not as untracked edits. Do not
truncate outputs, drop the source or regenerate until something passes.

This tests a teacher-response intervention, not a pure length effect. Actual exposure
changes must be projected and reported. A fresh candidate requires its own prospective
plan, complete full-bank reading and independent-input confirmation before qualification
or ethical scaling. The next plan is replay-base-reasoning-plan.md; the oldv5conditional
confirmation is not triggered. No new SFT is launched by this report.

## Preservation

Finite supervisor sft-drift-replay-interface-rca-v1 exited2026-10-22 18:45UTC at source
4971dd83a42f5f1a530403a2ba75012986b575fb. Entire terminal master,all9children and closed
worker log copied/hash-verified:219files/10,435,616bytes;97new beyond the first boundary.
Initial copy helper refused SupervisorEXITED's normal status3before copying; corrected
check verifies terminal markers plus EXITED explicitly. The premature analyzer attempt
also refused before writing. No generation restarted and no measurement was overwritten.

Private snapshotbafc76fe61908e7b0d53553818346bd0f04e5ae5at1a27f65verified6951files/
20,252,818,075bytes, including the first5closed children and first50reviews. Terminal
copy, completed160review, mechanical comparison andv3assessment are now local offGPU
and require the next private snapshot. Preserve reviewed_verdict_v1 separately from
comparison_v1's historical pending-review field. All artifacts are under ethical_pilot/
ethics_gpu_replay_interface_rca_v1; no result remains only onGPU after terminal copy.
