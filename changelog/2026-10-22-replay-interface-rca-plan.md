# Prospective diagnostic: replay learning versus transfer

V5 failed the procedural completion and factual-decision value gates. Preserve that
verdict; the conditional independent confirmation is NOT triggered. The fixed worker
is still completing its declared full100reading. No next SFT recipe is selected.

Evidence motivating this diagnostic:all12training engineering checks pass; actual
training tokens/projected objective and initial adapter/LR trace match their contracts.
All192decision draws(64sources×3) have exact inference-compatible prompt prefixes,
correct unmasked response targets/EOS and intended mode weights. The agent read all64
request/target pairs; no clear arithmetic, label or negation defect. The thinking gold
target median is45tokens; generated thinking median changed from293in the fixed control
to43.5in v5, while thinking decision accuracy fell32/32→27/32. This suggests shortcut or
style learning, but does not prove which bundled data change caused it.

## Question, hypotheses and schedule

Do exact replay facts/requests work, and which generalization step fails? After the
current worker is terminal and artifacts/reviews preserved, keep BASE, the old weight32
control and the v5final adapter fixed. Use a2×2design:training versus held-out facts,
crossed with training versus evaluation instruction/note wording. Each cell has64
presentations:eight facts/four operations, two polarities, two note states, two modes.

- Seen facts/training wording:the exact64new decision replay requests and targets.
- Seen facts/evaluation wording:the same statements, with v4instruction/note templates.
- Held-out facts/training wording:the v4statements, with training instruction/note templates.
- Held-out facts/evaluation wording:reuse the actual v4/v5reference/candidate observations.

There are576new calls(3new cells×64×3models);192existing observations are reused, never
relabeled as new calls. No new fine-tune, ethical reading, checkpoint choice or GPU rental.
New IDs/protocol/paths and exact inputs are registered and privately preserved first.
Do not change the currently running GPU checkout; implement/deploy only after it ends.

H1:little or no correctness benefit even on exact seen requests suggests the replay
manipulation did not reliably teach the target behavior; stylistic imitation alone is
insufficient. H2:seen-request success with loss after wording changes suggests interface
transfer failure. H3:seen-fact success across both wordings but held-out failure suggests
numeric/logical generalization failure. Mixed results remain mixed; none retrospectively
qualifies v5 or proves general forgetting. Eight facts per source are small/correlated.

## Fixed construction and checks

Use actual gold/v4assertion text and truth proofs, not answer-conditioned paraphrasing.
Replace only the exact instruction and irrelevant-note templates; preserve arithmetic,
negation, truth and note presence. Pair facts by operation and asserted-truth schema.
Reuse corresponding v4per-request seeds across all cells/models to hold RNG schedules
fixed while changing wording/numbers. Same pinned model/backend/decoder/token budget.
Both thinking modes remain separate; do not equate nonthinking with answer-only output.

Before calls, independently solve rendered requests and verify all intended facts and
labels, prompt/proof provenance, common task balance and actual saved training-prefix
identity for the seen/training cell. No evaluation answers enter training. No request
includes its proof or target response. Materialize/protect exact token IDs and source
hashes. Any technical identity failure stops the finite diagnostic and preserves partials;
no overwrite/resume or content retries. Run all declared models/cells regardless of
performance, with no BASE-known selection used to hide full-cell errors.

## Measurements and limits

Keep native-v1 grades; separately apply unchanged neutral-task-value-v2. Report all
correct/wrong/unscorable counts, format, boundaries/stops, response length distributions,
note/polarity agreement and every paired gain/loss for each cell/model/mode. Full-cell
correctness is primary here; BASE-known retention is supplemental with explicit masks
and denominators. Fully read failed/unscorable replies and retain disagreements.

This is a mechanistic development diagnostic, not a new adoption gate. No passing
subset or threshold change can clear v5. Report apparent copying/shortcuts as evidence
from visible outputs, not claims about inaccessible internal reasoning. A later training
intervention requires its own hypothesis, matched comparisons and untouched confirmation.
