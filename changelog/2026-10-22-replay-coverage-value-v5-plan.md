# Prospective replay-coverage candidate with value-separated assessment

Written after the v4 BASE/fixed-control reference results and before any training of
the new replay recipe. V4 remains a terminal reference study with an unusable native
word-only BASE decision cohort; its failed guard is not cleared. No v4 candidate ran.

## Question and fixed intervention

Can one broader, explicitly correct replay set preserve factual/procedural decisions
in both thinking modes while doing the same C4 training? The hypothesis is a replay
coverage/interface mismatch, not a conclusion that the model has globally forgotten
arithmetic. The fixed control retains 16/24 BASE-known nonthinking factual decisions
under the separately reviewed value interpretation, versus 32/32 thinking decisions.
All 62 reference flags were read fully, and all 384 token/runtime/seed/native-grade
records reconstructed. The manual and value-v2 interpretations agree on all reviewed
decisions. Incorrect terminal choices remain incorrect even with correct reasoning.

Train exactly the already prepared, **untrained** v4 recipe under new training ID
`ethics_sft_c4_replay_coverage_v5`, master `ethics_sft_replay_coverage_value_v5`.
Reuse its manifest bytes, source data, schedule, seed42, LoRA, weight32, LR1e-4,
454 steps, final-checkpoint choice and measured objective. No new gold generation,
weight/LR sweep, outcome-based checkpoint choice or training replication. Training
uses fresh Qwen3-4B weights on the existing authorized CUDA GPU. The intervention
changes replay source coverage, mode allocation and token exposure together, so an
improvement would not identify which of those caused it.

## References and assessment amendment

Reuse the actual v4 BASE/control response IDs and raw bytes; do not relabel them as
new measurements or rerun them to obtain a passing reference. The same held-out
procedural/decision inputs will measure the new candidate, with their prior use
disclosed. No evaluation wording or operand is added to replay training.

Use `task-value-v1` unchanged for the 128 procedural presentations. For 64 factual
decisions use the separately versioned `neutral-task-value-v2`: recognize an explicit
terminal choice, or an unambiguous standalone leading choice when no opposite choice
appears. Terminal choices take precedence over earlier opposite choices. Negated,
ambiguous, missing, capped or invalid-boundary replies remain unscorable. Do not infer
an answer from correct intermediate reasoning. Preserve native-v1 scores and exact
word-only format compliance alongside these values. Frozen ethical scoring is unchanged.

Freeze the value-known cohort from **BASE only**: procedural 63 thinking/57
nonthinking; decisions 32 thinking/24 nonthinking (all four operations, both labels).
The decision minimum remains 24/32 per mode; no threshold is lowered. This is a
development assessment correction made after inspecting references, not an untouched
validation experiment. Wordings/notes/polarities share eight facts and are correlated.
Neither 64 presentations nor repeated greedy calls are 64 independent capability tests.

## Falsifier, measurements and interpretation

Require all engineering/checkpoint-binding and exact projected input/label/exposure
checks. Procedural retention must be >=95% per BASE-known mode, <=5 percentage point
strict-format deficit against the same BASE cohort, and all 128 replies complete with
normal boundaries/stops. Decisions must retain >=95% per BASE-known mode, all four
operations/both labels, all 64 replies complete with normal boundaries/stops, and
all 64 exact lowercase final words. The latter strict check can still fail despite
good value retention; BASE's own strict-format failure remains explicit.

Run original frozen development/validation model checks without modifying their
accuracy/extraction/note thresholds. Collect all 100 frozen belief readings (2,400
natural replies) even if model checks fail, with qualified/unqualified status explicit.
Require all 2,400 valid natural replies for adoption. Do not retry missing answers,
impute neutral scores, select settings on ethical drift, or declare automatic adoption
from a finished worker. Report same-backend BASE/fixed-control comparisons, retained
and newly correct values, format changes, note/polarity pair denominators and coverage.
Sampling variability from existing BASE seeds is distinct from single-training-seed
uncertainty. Report descriptive drift with missing-answer bounds if needed.

Any failed technical identity check stops the finite worker while preserving partial
artifacts; no resume or overwrite of started IDs. Scientific failure does not suppress
the remaining planned candidate measurements. Fully read failed/unscorable replies,
and preserve source/config/protocol/raw data privately before deciding what follows.
If this candidate passes, independently confirm on new inputs before calling it a
tuned pipeline; then plan matched ethical arms with the same preparation. If it fails,
report which declared endpoint failed and reassess the mechanism rather than starting
another automatic sweep. No full90/100-belief training or new GPU rental is scheduled.
