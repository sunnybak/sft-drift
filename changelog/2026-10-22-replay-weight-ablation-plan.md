# Proposed single replay-weight ablation after the fresh value review

This plan is written after ethics_gpu_fresh_retention_v1 and its full164-response
review. It is NOT a reinterpretation of its primary falsifier. The original strict-known
criterion reports no concern, but excludes BASE-correct worked equations. Supplemental
value review reveals3stable real arithmetic losses in both negative and C4SFT. Full
thinking performance is mostly preserved. This is narrow mode-specific regression,
not broad collapse. Balanced ethical expansion is deferred while it is addressed.

## Hypothesis and one candidate

Instruction replay trained complete correct BASE responses. Nonthinking replay received
about0.20%of mean token-NLL coefficient mass versus~24%thinking replay. Weak exposure
may permit answer-only arithmetic regressions when long document training changes
response style. This is a hypothesis; current audits do not identify gradient/Adam
contributions or prove causation.

Test ONE candidate: fresh Qwen3-4B C4control, same source texts, teacher responses,
serializer, eligible raw targets, shuffle/training seed42, LoRA settings, LR,454steps
and227/final checkpoints as ethics_sft_pilot_c4_only_v1. Change only nonthinking replay
target loss weight from1to32. Use all complete replies; do not mask/truncate replay or
add the observed failing questions to training. Normalize weighted token NLL across
the full optimizer accumulation group, and audit exact weights/denominators/coverage.
Report raw and weighted target mass and per-mode coefficient shares; unchanged raw
counts do not imply unchanged optimization dose. Choose final checkpoint only.

32is fixed before implementation/training; it should raise short-reply exposure into
a several-percent range while keeping most objective mass on documents/thinking.
Measure actual shares from the existing ledger before launch; do not claim a precise
share from raw token counts alone. No LR/epoch/rank/weight sweep follows automatically.
Preserve historical defaults, configs, preprocessing hashes and loss path when unset.
New recipe/config/run IDs are mandatory. Never train on the Mac or start from an adapter.

## Correct measurement before candidate selection

Implement a SEPARATE versioned value assessment, preserving the frozen answer-rule
assessment. Distinguish task value, exact final, answer-only format, reasoning boundaries,
normal stop and collection/extraction failures. Recognize literal integer answers and
simple worked equations using original operands/operations and a valid equality; do
not search for the expected number anywhere in a reply. Recognize ordered integer lists
with optional separator whitespace. Uppercase tasks retain character/case correctness,
with spacing reported separately; YES/NO remains a logical value, with case/format
separate. Unsupported or ambiguous forms remain explicit unscorable results, not neutral.
Test wrong operands/results, extra numbers, negation, malformed delimiters, dropped
characters, caps and missing outputs. No frozen score or old gate is overwritten.

Freeze a further independent-input confirmation bank BEFORE training: same8procedural
families/64questions/two modes; bank RNG20261023, disjoint exact prompts from replay,
old retention and fresh-v1. Similar operand magnitudes and random six-letter strings;
no selection from model outcomes. This is fresh input confirmation within reused task
families, not broad capability coverage. Freeze scorer tests/source/hash with the bank.

Measure BASE, unchanged original C4control and new weighted C4candidate on that same bank,
three evaluation seeds42/7/1729. BASE-value-known uses seed42only, valid complete normal
replies with correct recognized task value, independently of answer-only compliance.
Require>=32known/mode and all8families; report every full-bank row, gains/losses and
coverage, plus the original strict-known mask as a distinct diagnostic if useful.
Read every failure/unscorable and all lost-value replies in full. No formatting issue
is silently called forgetting; no correct worked equation is silently called ignorance.

Acceptance for the candidate on this independent bank:>=95%BASE-value retention in
EACH mode/seed, complete verified boundaries/stops/coverage, no >5pp strict-format
retention deficit versus matched BASE, all engineering update/coverage/normalization/
reload/checkpoint checks pass. Report deficits to unchanged C4 and matched BASE, stable
loss/gain IDs and full-bank performance regardless of acceptance. Nonthinking seeds are
runtime repeats, not independent sampling replicates. Do not infer broad preservation.
If unchanged C4 already has no loss on this bank, the improvement hypothesis is
inconclusive even if the candidate passes; report that instead of claiming repair.

Every new fine-tune gets the frozen FULL100-belief evaluation, not just controls.
Do not choose recipe/checkpoint on ethical direction, magnitude or specificity. Capture
failed qualification and valid stance replies separately. A target-free supplementary
reading may be added under a fixed allocation before launch, never merged with original
independent-endorsement Stance Score. No all100-belief training or new rental follows.

## Execution gates and next work

This is a proposed fixed intervention, not an already prepared/running job. Before model
calls: implement/test value assessment and opt-in weighted normalization; register all
fresh inputs/checkpoints/results; freeze measured objective and exact runtime/IDs;
run CUDA analytic/update/reload verification of the weighted path before real SFT.
Preserve source and private artifacts at safe boundaries. Refuse overwrite/resume.

If the candidate fails, preserve the failure and reassess; do not automatically try
another weight. If independently supported, apply the updated recipe to properly matched
controls and a complementary-position pilot under its own frozen plan. Old seed42
controls cannot be reused as recipe-matched controls after a loss-weight change. The
old neutral18/20gate remains failed; this experiment does not reclassify it as passed.

## Pre-SFT amendment after CUDA analytic check v1

No study model has been trained with the new loss. CUDA checkv1caught that the custom
loss reported the correct mean NLL but Accelerator divided its already group-normalized
gradient by GAS again: accumulated updates were half the analytic mean. Full batch
matched within1.2e-7; accumulated error0.01878. Failed results remain immutable.

Fix backward compensation while reporting unscaled NLL, and rerun the SAME analytic
criterion under fresh checkv2. An additional native Trainer/ForCausalLMLoss diagnostic
will measure the pinned library's unweighted scaling; do not infer it from logs alone.
The legacy default path remains untouched. Correct group normalization is an explicit
opt-in for both new weight1andweight32training.

Add a FRESH normalization-only weight1C4control, identical to the weight32candidate
except replay weight. This avoids confounding a normalization change with weight32.
Historical C4 remains an additional diagnostic, not a matched corrected-recipe control.
The independent confirmation therefore measures BASE, historical C4, new weight1C4
and new weight32C4:4models×128presentations×3seeds=1,536calls. Both new fine-tunes
receive all100frozen belief evals at seed42 (2,400natural replies/model plus controls),
with qualification failures explicit. This seed allocation is frozen before training;
prior3-seed BASE spread is context, not candidate training/eval replication. No new
target-free full sweep. Selection remains procedural retention, not ethical outcomes.

Acceptance thresholds and final-only checkpoint choice remain as above. Compare the
weight32candidate to the fresh weight1control before claiming benefit from replay
weight. A pass shared equally by both is not evidence that weight32repaired anything.
One candidate plus one matched control is a fixed ablation, not a parameter search.
