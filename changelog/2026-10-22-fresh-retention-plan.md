# Fresh retention confirmation before training changes

Written before generating the new bank or making model calls. Existing source/weights
and old assessments remain fixed. Parent readout and clarity diagnostic are complete
and privately verified at2b46c808 (code63e0a77). Existing retention shows overall gains
and narrow losses; correct token normalization and reloads give no engineering reason
to change training blindly. Nonthinking replay has only about0.20%of token-NLL mass,
but that is a potential ablation, not a demonstrated cause.

## Question and finite design

Do copying/numeric losses recur on independent operands/strings, with a deficit large
enough to justify training changes? This tests eight procedural families, not broad
knowledge retention, intelligence or ethical correctness. It cannot prove absence of
all unmeasured regressions.

Master ethics_gpu_fresh_retention_v1. Five fixed models, three requested evaluation
seeds42/7/1729,128presentations/model/seed=1,920calls. Six jobs are not needed:
BASE selects its reference mask once from its seed42 replies, then reports all3seeds
against that same mask. Four adapters use exactly that frozen mask. No adapter result
enters reference selection. Old banks, masks, extractor, grading and thresholds remain
unchanged; this is a new bank and explicitly versioned reference construction.

Use64new questions:8each sum, difference, product, comparison, negated equality,
sorting, uppercase and constant-step progression; two correlated thinking modes.
Bank RNG20261022; 4questions/family tagged development,4validation before calls.
Independent random operands of similar magnitude to old retention and six-letter
strings; original task formats/families deliberately reused. Check no exact prompt
matches original replay or retention. No search over seeds, banks or model outcomes.
Both full split/family counts and BASE-known counts remain in reports.

Match existing retention sampler/runtime: thinkingT.6,p.95,k20,minp0; nonthinkingT0;
4,096cap,4,352context,batch32, same Qwen revision/adapters/backend. Greedy mode's
three seeds are runtime repeats, not independent sampling replicates. Requested seeds
do not guarantee identical raw text. Exact prompts/tokenIDs, raw replies, failures,
configs, adapter hashes, versions and source bindings are saved. No rental or training.

## Outcomes and decision before calls

Preserve frozen semantic, exact-answer, strict-format, boundary and normal-stop
assessments separately. Select BASE-known using all four historical correctness/
format/boundary/stop requirements on seed42only. Require32known/mode and all8families
for a usable reference. Insufficient reference or technical identity failures stop
adapter dispatch, with partial results preserved; performance failures otherwise stay.

Report full-bank gains/losses versus same-seed BASE, conditional known-item losses,
per-family/split/mode counts, per-seed variability and missing responses. Read every
non-admissible response in full; distinguish whitespace-only deviations, genuine
value/content differences, boundaries, caps and errors without changing original grades.

A training-retention concern warranting an ablation requires an adapter's conditional
semantic accuracy to trail same-seed BASE by MORE THAN5percentagepoints in EACH of
three repeats in a mode, with at least3distinct known questions showing stable genuine
non-whitespace content losses (wrong across all3normal, identity-verified replies and
correct in all3matched BASE replies). Report lesser losses too. This is a prospective
operational decision rule for these procedural tasks, not a test of zero forgetting.
Strict100%historical gates remain recorded; do not relabel them passed.

If this concern is absent, do not retune replay merely to fit seen strings. Move to a
prospective balanced/complementary-position design to distinguish assignment-specific
learning from broad response changes. If present, test ONE predeclared nonthinking
replay-weight ablation on neutral/C4 documents before ethical treatment expansion;
freeze its recipe and a further independent retention confirmation before training.
No automatic LR/epoch/sampler search, checkpoint selection on ethical direction or
all100-belief SFT follows this check. One trained checkpoint per arm and reused task
families limit causal and population claims even with independent operands.

## Execution and preservation

Register parent and five child paths before preparation. Use typed JobConfig→RunResult
instruction_retention jobs with an opt-in BASE-reference mode; legacy config hashes
must remain identical. Preserve all partial outputs; refuse overwrite/resume. Preflight
all source/model/config bindings before creating directories. Freeze adapter schedule
and mask before any adapter calls. Copy completed children off-box; save Git and private
artifact snapshot after review. Fresh models in subsequent training must receive the
full100-belief evaluation, not just retention or their targets.
