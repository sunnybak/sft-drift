# One lower-learning-rate probe after the replay-weight comparison

This plan is prospective for the next training candidate. Preparation requires the
fixed replay-weight worker to finish, actual full100coverage to be audited, and both
models' failed control and retention replies to be fully reviewed. Ethical score
magnitude/direction does not determine whether this probe runs or its settings.

## Rationale and intervention

The normalization-matched weight1andweight32C4models both retain57/59BASE-known short
answers on each runtime repeat. Weight32recovers one product but loses one sequence;
strict format improves without a net value-count gain. Both development runs fail the
same negated arithmetic case despite generated reasoning explicitly reaching the
correct conclusion. This is not broad collapse, but a recipe cannot be cleared merely
because its narrow95%retention threshold passes. Original failed gates remain failed.

The higher short-reply replay weight did not fix the failures. Test ONE further factor:
lower the peak learning rate from1e-4to2.5e-5, holding the corrected normalization,
weight1replay, exact C4/replay manifest, token labels, one-pass microbatch order, seed42,
LoRA16/alpha32/all7projections,454steps and227/final saves fixed. Choose final only.
A fourfold smaller peak LR also scales the fixed warmup/linear-decay schedule fourfold;
it does not establish fourfold smaller parameter displacement under Adam/clipping.
Do not combine this with a new corpus, schedule, rank, masking rule or weight sweep.

Hypothesis: the smaller update schedule preserves answer selection/value behavior
better while still giving verified nonzero, reloadable adapter updates. It is a test,
not an established diagnosis of excessive LR. Lower adaptation could also reduce
learning; a passing C4control alone does not demonstrate useful ethical learning.

## Independent confirmation and references

Freeze a further fresh procedural bank before any new model calls, RNG20261024,
64questions across the same8families in thinking/nonthinking modes. Block exact prompts
from replay and all preceding retention banks. Reject collisions; do not resample based
on outputs. These are fresh inputs in reused families, not a general capability suite.

Measure BASE and the fixed norm1final on this bank before candidate SFT,384calls each
(eval seeds42,7,1729). Freeze BASE-known from seed42correct recognized task values,
complete boundaries/normal stops, independent of answer-only format. Require32known
permode and all8families. Preserve original frozen grades and strict mask separately.
Read every failed/unscorable reply in full and preserve hashes before candidate training.
Then measure the one lower-LRfinal,384calls. No old failure question enters training.

Preserve task-value-v1and original scoring. Acceptance remains>=95%BASE-known value
retention in EACH mode/seed, no>5ppstrict-format deficit on the matched known cohort,
complete token/runtime/boundary/stop coverage and all12training engineering checks.
Separate fixed original model controls must meet their unchanged95%accuracy/extraction/
nullflip criteria. A stronger retention-benefit claim additionally requires fewer
known-value losses than norm1without a thinking loss-count increase; shared passes
alone do not show improvement. Report every gain/loss/unknown, full-bank performance,
format, mode/family and seed. If norm1has no losses on the fresh bank, repair benefit
is inconclusive even if the candidate passes. Greedy repeats are not replications.

## Full surface and stopping rules

Give the new final its own original development/validation attempts and one frozen
all100belief reading at seed42, regardless of qualification. Use explicit
collect_unqualifiedpolicy to prevent absent natural calls while retaining failed controls
and original validation status. Verify2400actual recorded/valid rows and raw score
reconstruction. No ethical outcome selects recipe/checkpoint or triggers retries.
Existing norm1full100same-seed reading is a fixed descriptive comparator; inference
source/runtime identity must match before comparing. No need to reread it to seek a pass.

Technical identity failures stop and preserve partial outputs. A started stage cannot
resume/overwrite by ID; no automatic retry-until-pass, alternative LR or additional
training seed follows. If the candidate fails, preserve/reassess rather than silently
relaxing a gate. If it passes, further matched ethical/off-topic/C4training still needs
its own prospective plan and evidence of learning, not just this preservation check.
No full90/100belieftraining or new GPU rental is authorized by this plan.

## Execution and preservation

Use existing JobConfig->RunResultstages/run.py; operational orchestration only. Register
fresh artifacts/configs before preparation. Freeze plan, actual training manifests,
resolved settings, independent bank, source and adapter bindings; commit/push and verify
private snapshot before reference calls and again before SFT after reference review.
Keep existing GPU source pinned until its original worker is terminal. Preserve exact
prompts/raw tokens/failures/configs, every new JSONLwithMarkdown, final/mid checkpoints,
full reviews and costs/runtime. Finite supervised workers; no automatic restart/resume.
