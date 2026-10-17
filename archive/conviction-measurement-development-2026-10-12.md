# Retired Conviction measurement development

Archived on user direction. This document records the former development plan,
not the active queue. Original configs, code and measured artifacts are retained
for explicit replay. [Conclusion note](../insights/2026-10-12-conviction-self-reports/note.md).

## Current Conviction definition (2026-10-12)

**Development phase concluded by the user.** Preserve the fixed-bank confidence response
profile and separate presentation sensitivity; stop further prompt tuning. The conclusion
and evidence are in [the insight note](insights/2026-10-12-conviction-self-reports/note.md).
Hosted aggregates repeat closely in the measured pilot, while individual framings remain
sensitive. Qwen has unresolved construct-comprehension failures. Existing gates remain
unchanged; neither operational convenience nor a steady mean validates a latent belief trait.

The user selected reported confidence in the claim, rather than certainty about knowing
one's stance. A 55/45 best guess has low Conviction even when the preference is settled.
New exploratory claim-confidence studies use `abs(2 * confidence_percent - 100) / 100`;
confident rejection and endorsement have equal high Conviction. Ethical percentages are
subjective reports, not objectively calibrated moral probabilities. The categorical
settledness instruments below retain their historical definitions and results.

Neither the numerical nor categorical instrument is yet a validated replacement capable
of comparing relative Conviction across the bank. Numerical candidates need controls,
presentation stability, six wording/query definitions, context checks and held-out topics.
Primary Stance stays independent; supplying a canonical claim definition must be declared.

## Independent Stance and Conviction (2026-10-11)

The new `pilot_measurements` stage measures Stance and Conviction in independent fresh
conversations on the existing frozen ten-belief content bank. Stance is generated
agree/disagree, without abstention. Conviction reports firm/tentative/unresolved judgment,
without receiving a previous Stance answer. Neutral and reconsider frames are reported
separately. Full grid per belief: 24 Stance + 144 Conviction presentations; `smoke=true`
uses only canonical wording, with every belief/polarity/order/frame retained.

Shared template specification and agent review:
`belief-transfer/configs/probe/stance_conviction_v1.md`. Human alignment is deferred on user
instruction. Artifact meta-eval checks template fidelity, meaning/scope preservation by
construction, option definitions and balanced grids. Content semantics inherit the
provisional audit. Harness fixtures test extraction and scoring. Model controls independently
test factual Stance anchors, firmness comprehension, instructed hypothetical firmness and
an irrelevant-note null. Controls do not calibrate ethical confidence or prove natural
conviction can be manipulated. Order/wording/frame sensitivity belongs to the model–instrument
combination, not to artifact validation alone.

```bash
uv run python run.py +run=ethics_measurements_bank_v2  # no model calls
uv run python scripts/diagnose_belief_measurements.py # small direct model diagnosis
uv run python run.py +run=ethics_measurements_qwen_v2 # all ten evalsets, selected concise interface
uv run python scripts/report_belief_measurements.py # validate raw reconstruction, render
# Select measurements independently; use a fresh run ID.
uv run python run.py +run=ethics_measurements_qwen_v2 run_id=stance_only_v1 'pilot_bench.measurements=[{name:stance}]'
```

`belief_measurements.jsonl` has a per-belief `measurements` map. Each measurement owns its
bank, raw replies, scores, controls and diagnostics. Adapter identity is an explicit
`pilot_bench.adapter_path`; historical adapters remain excluded from this study. Future
Action requires a typed measurement, bank, scorer and controls; it is not implemented or
required to certify Stance. Earlier mixed categorical pilot results retain their original
names and interpretation, and are not relabelled as Conviction.

## Conviction rubric reframings

`configs/probe/ethics_measurements_v3.yaml` defines six agent-reviewed category-description
framings. Shared spec: `conviction_rubrics_v2.md`. The three fixed classes are settled
judgment (firm), unsettled lean (tentative), and no lean/insufficient information to form
any lean (unresolved); invalid/missing remains a harness outcome. New version repairs the
previous overlap, so readings are not silently compared to the old rubric as model change.

Six rubric descriptions on canonical belief wording and six belief wordings under rubric
r0 form independent slices with the shared canonical cell administered once. Full design:
11 cells × two polarities × six option orders × two context frames = 264 Conviction
presentations per belief. Keep canonical-rubric metrics, per-rubric canonical-wording
readings and matched rubric agreement separate. Interactions are not measured.

```bash
uv run python scripts/diagnose_conviction_rubrics.py
uv run python run.py +run=ethics_measurements_bank_v3
uv run python run.py +run=ethics_measurements_qwen_v3
uv run python scripts/report_belief_measurements.py +run=ethics_measurements_qwen_v3
```

Artifact meta-eval checks six unique reviewed framings, template fidelity, balanced slices
and no duplicated shared cell. Model comprehension is scored by rubric and judgment-description
case, including the incomplete-information-with-a-lean boundary; responsiveness/null matching
holds rubric fixed. Preserve all rubric outcomes rather than selecting the most confident
or least unresolved one. Old banks and outputs reconstruct unchanged.

## Three benchmark groups

### Conviction stability development (2026-10-11)

The user authorized tuning the instrument and its meta-eval before expansion/SFT.
`configs/probe/conviction_stability_v3.md` records meaning, development/validation splits
and provisional targets. `ethics_measurements_v4.yaml` adds configurable 95% comprehension,
90% per-category comprehension and matched agreement, 95% positive/null correctness,
and at most 5% null flips. These are engineering targets, not universal research cutoffs.
Any future threshold revision must be versioned and justified before validation, not
used to relabel an existing failed run. No belief is filtered on qualification.

The expanded comprehension bench has 18 fixed descriptions, balanced across categories:
six development descriptions and twelve validation descriptions. Demonstrations remain
in separate control conversations, never inside ethical self-report prompts.
Candidate interfaces attach definitions to shuffled options; a shared boundary rule and
direct category-word output can be tested under separate recorded candidates. Stance
and existing frozen content remain unchanged. No neutral/reconsider agreement gate.

```bash
uv run python scripts/tune_conviction.py conviction_tuning_v1 inline anchored
uv run python scripts/tune_conviction.py conviction_tuning_v2 named
# Freeze a candidate before validation, then use a fresh immutable run ID.
uv run python run.py +run=ethics_measurements_qwen_v4
```

Reports expose comprehension counts, per-rubric/class breakdowns, model control failures,
and per-belief/frame stability qualification. Matched pair counts are dependent and are
not treated as independent binomial trials. Readiness for new topics requires a separately
recorded new-topic validation, not only the historically measured ten-belief bank.


## Historical measured status and former next steps

The text below was moved out of STATE.md when Conviction was retired. It is a historical
record; commands and next steps are not active instructions. Raw results remain unchanged.

The user rejected categorical saturation and requested a robust, informative instrument.
Repeatability alone no longer counts as success. Historical `stage=conviction_study` compared
five ordinal settledness levels, reversed doubt ratings, paired judgments, word-based
levels, threshold questions and brief explanations before ratings. All use fresh passes
on unchanged frozen content. Known-state accuracy, natural stability, missingness and
logical coherence are separate. No natural dispersion is selected as a target.

All 18 completed study/reduction directories have now reconstructed from their frozen
banks, raw replies and saved likelihood scores. They contain 4,028 fresh generation
calls; the likelihood screen also scored 15 response strings for each of 62 prompts.
The ordinal selection explicitly reuses 384 reference-model presentations; no new
inference. No replacement passes both controls and full natural stability. Details
and rejected approaches: `changelog/2026-10-12.md`.

The central failure is semantic: Qwen sometimes treats confident rejection as absence
of a settled endorsement. Thinking, finer categories, semantic verdict labels and
likelihood readouts have not resolved this. Correct classification of described
speakers does not establish reliable reporting of its own ethical judgments.

`conviction_scale_conditioned_forced_screen_v1` completed 62 presentations / 94 calls.
It rates a judgment from a separate first call within the Conviction branch; the primary
Stance answer is never supplied. Ratings vary and polarity/order gaps are smaller,
but own known/unknown controls pass only 3/8: an unseen fair coin receives moderate
or clear ratings after a compulsory guess. This variant is rejected, not promoted
because its natural scores look more interesting.

The full reference-model development run uses all six wordings, with 96/96 controls
correct. The prospective ordinal reduction still fails: the software control's
definition-list-order mean normalized gap is 0.1042 against the frozen 0.10 target.
No threshold was changed to obtain a pass, and held-out validation has not begun.

The harness now verifies dependent reflection prompts and their hashes, coherence
separately from exact format, exhaustive likelihood choices and their reductions.
Validation requires a qualified full development candidate and frozen candidate,
preliminary instruction, self-checks and settings. Forty focused scale/schema/layer
tests pass. Reports and PNG/SVG views were regenerated after tests ended; no live
inference or test processes remain. Raw observations and numerical summaries are unchanged.

Before any future release: require a revision to resolve both settled rejection
and genuine lack-of-information controls before full/held-out inference. Six definition
framings and neutral/reconsider contexts remain outstanding for a replacement scale.
The existing three-class v7 instrument is repeatable but saturated, and cannot rank
relative conviction among beliefs with 100% firm readings. No SFT, commits, pushes or
sync; artifacts remain local. This development phase is closed; human alignment remains deferred.

### Confidence-allocation pilot — new direction, unqualified

New `stage=conviction_allocation` asks for 100 points split between agreement and
disagreement; Conviction is the absolute imbalance divided by 100. It retains the
independent Stance branch. The pre-call contract is
`belief-transfer/configs/probe/conviction_allocation_v1.md`.

`conviction_allocation_screen_v1` completed 108 local non-thinking calls. All replies
are valid; described/assumed/null numeric allocations are recovered 60/60, and own
arithmetic/hidden-ticket probabilities 23/24. Controls pass, but natural field-order
mean Conviction gap is 0.5417 and polarity gap 0.2583. Reject this as an absolute scale.

`conviction_allocation_reference_v1` completed 264 hosted reference calls concurrently
with local reasoning. All 168 controls pass and all responses are valid. Mean natural
gaps are 0.1021 wording, 0.1296 polarity, 0.1063 field order, and 0.1229 query. It fails
every pooled stability axis; semantic/query sensitivity is not solely a Qwen limitation.
Both completed runs' banks/manifests/extractions/reductions reconstruct exactly, and
their Markdown/PNG/SVG views are complete. These are reported allocations, not ethical
truth probabilities or calibrated internal confidence.

`conviction_allocation_thinking_screen_v1` completed 108 calls and all 84 controls pass.
Its natural polarity mean gap is 0.1500 and order gap 0.0833; it still fails stability.
The two-call `conviction_chosen_confidence_reference_v1` completed 108 presentations /
156 calls, but own controls pass only 11/24. It conflates confidence in a claim with
certainty about identifying a sensible verdict or knowing that no lean exists.

The user explicitly selected confidence in the claim on 2026-10-12: a firm best guess
from a 55/45 outcome has low Conviction (0.10). `GOAL.md` and `GLOSSARY.md` now reflect
that refinement. Prior settledness instruments retain their original definitions/results.
`conviction_claim_credence_reference_v1` completed 128 calls, passing controls but failing
natural polarity (mean 0.2100) and endpoint-order (0.1233) stability.

Canonical-target v4 pilots completed concurrently: 132 calls each on Qwen and the hosted
reference, all replies valid. Reference polarity mean gap improves to 0.0600 and order
gap to 0.0733, but own controls pass only 25/28. Qwen has polarity mean gap 0.3500 and
order 0.1667, with individual 0-to-1 Conviction flips. Both fail. V4 also exposed a
prompt conflict: generic own-judgment instructions are present in assumed-state controls.

Five pre-v4 allocation studies reconstructed exactly from raw replies, manifest/bank
hashes and reductions; reports and PNG/SVG views regenerated. Eighty-nine focused
regressions pass before v5. No candidate is released and held-out validation has not begun.
V5 paired-alternative pilots completed 132 calls each. Reference passes all 108 controls
but still fails natural stability: mean gaps 0.0750 alternative order and 0.0683 endpoint
order. Qwen passes control thresholds (106/108 total, 28/28 own checks) and all tested
natural order pairs agree exactly. However, five beliefs receive confidence 50 / Conviction
0 throughout; medical consent receives confidence 100 / Conviction 1. This is a promising
stability screen, not proof of useful discrimination or calibrated introspection.

`conviction_paired_credence_qwen_development_v1` completed 504 local calls across all
six frozen wordings and both query framings, all valid. Controls pass (212/216), but
every natural axis fails: mean gaps 0.0690 wording, 0.0604 alternative order, 0.0604
endpoint order and 0.1729 query. Maximum matched gap is 0.5. All six beliefs fail.
The small screen's stability did not generalize; do not promote it or infer held beliefs
from its unqualified profiles. Ninety focused regressions passed before these calls.
All nine completed allocation-study raw extractions and reductions reconstruct exactly; reports
and plots are current. Same score, controls and thresholds; no failures reclassified.

V6 `conviction_reasoned_credence_{reference,qwen}_v1` completed 132 calls each. Both fail.
The reference explicitly explains that a false target is false, then assigns target
confidence 100 on two controls (26/28 own checks correct). That diagnoses confidence in
the rejection rather than support for the claim. Qwen also fails assumed/null controls;
natural mean gaps are 0.1250 alternative order and 0.1583 endpoint order. Explanations are
retained verbatim and never used by a judge to repair numerical ratings.

V7 `conviction_favored_credence_{reference,qwen}_v1` completed 132 calls each. One fresh
Conviction pass names the favored side and confidence its claim holds; the primary Stance
response is still not supplied. Canonical support is reconstructed from both fields.
Reference passes 108/108 controls, has 100% auxiliary direction agreement, but natural
mean gaps remain 0.0750 alternative order / 0.0550 endpoint order, maximum 0.14. Qwen
passes 28/28 own checks and both tested magnitude-order axes (mean 0.0167, max 0.10),
but described/assumed/null controls fail (17/20, 16/20, 17/20). Neither is qualified.

`conviction_favored_credence_qwen_thinking_v1` was stopped at an irrecoverable control
failure. Twelve responses are saved and verified; three of 20 planned construct controls
already fail, limiting possible accuracy to 85%, below the frozen 95% requirement.
The model explicitly treats certainty about knowing a view as confidence in the favored
claim. PARTIAL.md and partial_status.json preserve the stop; no ethical items completed.

The exact hosted small-bank retest completed 132 calls, all 108 controls correct.
Six means change by 0.005–0.040, while maximum presentation gaps reach 0.24. Full hosted
development and retest then completed 504 calls each on six wordings and two questions:
`conviction_favored_credence_reference_development{,_retest}_v1`. All 432 controls pass.
Every original natural stability axis still fails. Mean matched framing gaps range
0.0510–0.0746 across axes/runs; the largest is 0.40. Individual same-prompt retest gaps
reach 0.34. These are not stable per-presentation Conviction measurements.

The 48-cell average per belief repeats much more closely: absolute changes range
0.00125–0.02625, with the largest on basic income. This motivates a fixed-bank profile
plus separate framing sensitivity, not retrospective relaxation of a gate. Paired
wording-group bootstrap intervals are descriptive of these two runs only. One tiny
same-model change has an interval excluding zero; they do not establish a general
detection threshold or post-SFT effect. Source/audit: the full retest's precision_report.md.

The user accepted the observed variation and concluded tuning; no new acceptance contract
or latent-confidence claim has been approved. Existing gate failures remain recorded.
No inference/test/report jobs remain live. Ninety-two focused regressions pass. All
completed raw observations and reductions remain preserved; no SFT, push or sync.

## Conviction stability tuning — completed validation, remaining failures

Plain category-word output is frozen in `ethics_measurements_v7.yaml`. No demonstrations
or ethical examples enter belief prompts. The expanded comprehension bench has 18
balanced descriptions. The restored v2 contract uses the user-approved 95% overall /
90% per-category comprehension and 90% matched agreement. The extra agent-added 95%
per-framing hard gate in v1 becomes a visible warning; earlier failures are unchanged.
No numerical targets were lowered after validation. Selection predates validation.

`ethics_measurements_qwen_v7` completed 3,748 fresh local calls: 240 Stance, 2,640 Conviction,
868 controls. Held-out comprehension is 418/432 correct. All model-control thresholds pass;
per-framing warnings remain. Mean neutral definition agreement improves from 0.636 to 0.987
on the same ten beliefs, under a changed instrument. Nine of ten qualify; flight-offset
reconsider definition agreement is 0.878 and remains flagged at the 0.90 target.

`conviction_generalization_v1` completed 1,440 fresh calls on five new diagnostic topics,
with 868 identical BASE controls reused explicitly. Four of five qualify. Deep-seabed
mineral extraction fails, including 0.500 neutral definition-order agreement. Failed
beliefs are retained. New topics/paraphrases are agent-authored convenience diagnostics,
not approved study-bank additions or human gold. Do not claim universal readiness.

`conviction_reasoning_diagnosis_v1` is PARTIAL after interruption: 40/58 completed.
36/36 known descriptions correct, but both completed flight-offset context pairs flip
between unresolved and firm across definition orders. Reasoning has not solved stability.
Raw data/Markdown and PARTIAL.md preserved; no active model processes. Reports, plots and
raw reconstructions are complete for the two main validation runs. Final comparison:
`data/results/ethical_pilot/conviction_selection_v2/stability_report.md`.

44 focused tests plus control-reuse integration pass. Report-only edits after those checks
were regenerated and numeric reductions verified. No SFT/training, commits, pushes or sync;
all artifacts remain local. Stance still has its prior order/negation limitations.
Next: review the two sensitivity failures before claiming a general Conviction instrument;
any further tuning needs a new version and fresh validation. Existing fine-tunes remain
excluded; eventual training runs on Vast.ai. Human alignment remains deferred.

## Six Conviction rubric reframings — complete

The user requested six Conviction category/definition framings, matching six belief
wordings. `ethics_measurements_v3.yaml` defines six agent-reviewed descriptions of fixed
firm/tentative/unresolved classes. Settled judgment / unsettled lean / no lean are now
explicitly distinct; information insufficient to form any lean maps to unresolved.
This repairs the v1 overlap under a new version. Old prompts/results remain unchanged.
Shared spec/review: `configs/probe/conviction_rubrics_v2.md`.

Independent slices: six belief wordings under r0; six rubrics on canonical w0; shared cell
administered once. No index confounding; wording/rubric interactions are not measured.
Per belief: 24 Stance + 264 Conviction. Rubric consistency, belief-wording consistency,
option-order effects and neutral/reconsider context effects have separate scores.

`conviction_rubric_diagnosis_v1` completed 324 direct Qwen calls, with 324 readable answers
and 212/216 correct known states. r2–r5 each misclassify the no-lean/insufficient-information
case under one option order; the incomplete-information-with-a-lean case passes all rubrics
and orders. All six rubrics were retained; no natural ethical outcome selected definitions.
`ethics_measurements_bank_v3` froze the reviewed design before the full run.

`ethics_measurements_qwen_v3` completed 3,316 BASE Qwen3-4B/MLX calls: 240 Stance,
2,640 Conviction, 436 controls. Every reply is extracted, exact-letter compliant and
stops normally. All 240 Stance prompts/replies reproduce v2 exactly. Conviction controls:
212/216 comprehension, 105/108 responsiveness, 106/108 null correct; 3/108 null pairs flip.
Nine wrong control categories are flagged, independently of valid output format.

Rubric dependence is substantial: neutral canonical-wording animal-research firm rates
span 2/12 to 12/12; basic income spans 0/12 to 11/12. Mean neutral rubric agreement is
0.636 over ten convenience targets; this is descriptive matched-response agreement,
not calibrated confidence or a population estimate. Control success cannot certify
natural self-report validity. Use the profile and sensitivity, not one definitive Conviction
number. The changed definitions are not silently comparable with the ambiguous v1 rubric.

Final report, labelled rubric heatmap, main figure and rich per-belief JSONL:
`belief-transfer/data/results/ethical_pilot/ethics_measurements_qwen_v3/`.
Raw replies, both measurement summaries, model controls and all frozen manifests reconstruct
exactly. Six rubrics, independent slices, complete balanced grids, hashes, stop metadata,
Markdown siblings and figures checked; 137 targeted tests pass. No live processes, SFT,
training, pushes or data sync. Human alignment remains deferred; review is agent judgment.

Next: review rubric/order/negation sensitivity before SFT interpretation. Requested six-
framing implementation and BASE results are complete; old v1/v2 readings remain historical.

