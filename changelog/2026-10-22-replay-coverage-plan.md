# Prospective replay-coverage intervention

Written after the reviewed lower-LR failure, before new replay generation or training.
This is one data intervention, not an LR/weight search. The existing ethical dataset,
frozen stance instrument, scores and historical failed qualification remain unchanged.

## Hypothesis and contrast

Narrow teacher replay may protect its own examples while providing poor coverage of
short procedural answers and the true/false decision interface. Existing replay lacks
nonthinking sort, nonthinking negated-equalityYES and all endorse/reject examples.
Lower LR worsened retention; weight32alone did not demonstrate a repair. These facts
motivate a coverage hypothesis but do not establish causation.

Compare ONE fresh C4 candidate against fixed ethics_sft_c4_weight32_v1 and BASE.
Keep weight32, corrected weighted-group normalization, LR1e-4, LoRA/settings/seed42,
C4 documents, manifest slot order, one pass,454steps and final-only selection fixed.
The intervention replaces the194short-response source slots, not the246existing
thinking teacher examples. There are three draws per source, as before. Replacement
may change token dose and mode composition; measure/report raw and weighted objective
mass. This bundled data intervention cannot isolate coverage from gold-label source,
reasoning examples or dose; do not describe it as an exact-token-matched ablation.

## Replay data pilot

New ID ethics_sft_replay_coverage_data_v1. Deterministic seed20261025.
Generate194programmatically verified examples:130nonthinking procedural examples
(sum18, each other seven established families16), plus64neutral factual decision
examples (eight independent facts across sum/difference/product/comparison, both
polarities, with/without one irrelevant note, thinking/nonthinking). Decision truth
and finalendorse/reject balance are exact; note pairs retain truth. Reasoning targets
are explicit procedural gold, not attributed to a teacher. No ethical claims train.
Keep all246old thinking teacher responses byte-for-byte, with original provenance.

Procedural operand ranges rotate through two-, four- and five-digit bands; strings
are random six letters. Neither frozen evaluation statements nor previously failed
examples are copied. Fresh evaluation uses different operands/strings. Check exact
prompt collisions with all registered/generated banks and the original teacher bank;
check semantic operation/operand keys where truth proofs are available. Fail on
collision, do not silently resample. Report exact overlap-check scope/limitations.
Review a fixed broad sample of complete requests/targets/proofs before manifest
assembly; mechanically validate every proof, target, delimiter, token count and EOS.
Every new JSONL gets a Markdown view. Register all output paths before materializing.
No live model generation is needed to produce these procedural gold examples.

## Preparation and finite measurements

After data review, prepare new master ethics_sft_replay_coverage_probe_v1, fresh
training ethics_sft_c4_replay_coverage_v1, fresh procedural bank seed20261026 and a
separate neutral decision generalization bank. Freeze actual manifests, projected
objective exposure, source hashes and configs in a preparation protocol. Preserve
privately before GPU training. Exact bank details/IDs are frozen before inference;
no data-dependent resampling. If all new examples are one chunk, original chunk count
and optimizer schedule remain feasible; otherwise stop preparation and amend openly
before training. Inspect all failing reference replies before candidate launch.

Measure BASE and fixed weight32 on identical fresh banks BEFORE candidate training.
Primary procedural cohort: BASE seed42correct recognized task values with complete
boundaries/normal stop, independent of answer-only format. Use existing value-v1
assessment alongside unchanged strict grades. One greedy eval seed42 is sufficient
for this bounded data check; it is not a training replicate. Do not describe repeated
greedy seeds as independent evidence. Keep every full-bank result and pairwise loss.
Supplemental neutral decision bank reports exact value, final format, note-flips,
polarity agreement and coverage separately, with BASE-known retention by mode.

Candidate gets the same references, original development/validation checks and all100
frozen belief readings at seed42, even when unqualified (collect_unqualified policy).
No checkpoint chosen on ethical drift. Full100scores remain descriptive on failure.
The runner must be finite, preserve partial results, and refuse overwrite/restart.
All failures, ambiguous values and capped replies get full agent review with hashes.

## Success, falsifier and next decision

Engineering/update/reload and preprocessing checks must pass. Existing95%BASE-known
procedural value retention per mode and all8-family/min32cohort sufficiency stay fixed;
report individual new losses even above95%. All known replies must have valid complete
boundaries/normal stops; strict final format stays separately visible. Original model
qualification remains accuracy>=.95, extraction1, note-flip<=.05 on development AND
fresh validation. Supplemental decision known-value retention must be>=.95per mode,
with complete/exactly parsed final replies; insufficient BASE coverage makes that
contrast inconclusive, not a pass. Natural full100must have2400valid replies to adopt.

Failure of any adoption condition rejects this candidate. Shared passes with the fixed
reference do not show a repair; reference-failed/candidate-passed checks support only
this bundled recipe on tested tasks. No claims of broad capability preservation or
selective ethical editing follow from a C4control alone. If successful, the next step
is a newly declared matched positive/negative/off-topic/C4pilot with this fixed recipe
and all100readings, not full90/100-belief expansion. If unsuccessful, stop this data
trial and reconsider the document/instruction mixture rather than automatically
sweeping LR, replay weight or data versions. No retroactive gate changes.
