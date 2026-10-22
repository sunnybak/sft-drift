# Prospective error-aware target-free diagnostic readout v2

Written after the failed mode and presence-control interventions, BEFORE any
readout-v2 calls. The v1conditional readout remains blocked and unlaunched. The
presence candidate failed its practical regression criterion; do not adopt1.5or
claim the loops fixed. Old benchmarks, gates, falsifiers and scores remain unchanged.

## Why a new measurement policy

Sparse missing replies and wrong valid answers are different problems. Treating one
capped arithmetic reply as global checkpoint invalidation prevents measuring the
actual ethical task; ignoring it would conceal a real defect. V2 keeps the defect,
counts every expected presentation and bounds what missing replies could change.
It does not certify a perfect model, repair reasoning by parsing it as an answer,
or turn stress-probe failures into passes. This is a post-diagnostic METHOD change,
not independent confirmation of the old qualification claim or permission to scale.

Keep original default thinking,T0.6/top_p0.95/top_k20/min_p0,4096cap,4352context,batch64,
pinned Qwen/card/backend/versions and all five fixed models. No presence penalty,
forced final labels, synthetic reasoning closures, truncation or retry-until-valid.
Use target-free opposing positions: same frozen100beliefs/scopes/sixwordings, two
physical orders, canonical positive target only.1200natural presentations/model/seed.
Outcome is forced canonical-position choice rate, not independent endorsement,
confidence, moral accuracy or negation competence. Every contradictory valid answer
remains. The old independent-endorsement and target-line readouts stay separate.

## Design and counts

New master ethics_gpu_target_free_readout_v2;15children
ethics_gpu_target_free_readout_{base,positive,negative,offtopic,c4_only}_s{42,7,1729}_v2.
Retain the original frozen target10/other80ethical/eval-offtopic10group assignments,
including separate related-untrained6. No new training,100-belief treatment or rental.

Each job includes80fresh reference contexts:16stipulated normative,16provided-factual,
32actual arithmetic, PLUS16non-numeric conditional-rule/scope cases. Keep arithmetic;
add the logical cases rather than selecting an easier subset. New objects/operand
pairs disjoint from preceding banks, reused task families acknowledged. New scope
cases cover conjunction, exception, sufficiency and exclusion using explicit fictional
rules, not moral ground-truth labels. All references computed/checked and all80cases
agent-read before freezing. Two orders×plain/repeat/note=480fresh controls/job.
Each dev/validation split has48normative,48provided-fact,96arithmetic and48scope-logic
presentations. Eight separately labeled reused stress probes retain the exact prior
loop/five>three prompts, source hashes, model identities and request seeds.

Per job1200natural+480fresh+8stress=1688calls; total18,000natural+7,200fresh+120stress
=25,320calls. Register new paths before prepare. External control-bank path/hash/count
must be typed config, saved byte-for-byte and included in the instrument fingerprint.
Store seed keys for matched plain/note and independent repeats; natural seed mapping
stays prompt-SHA based. Seeds record requested RNG, not deterministic prose.

## Separate three kinds of evidence

1. Response admissibility: use the unchanged frozen answer extractor and reasoning
   boundary/stop checks. Failed/missing replies have no answer. Retain valid extracted
   replies even if strict formatting fails; record format separately. Never take the
   reasoning's favored position as a replacement for a missing/conflicting final.
2. Model checks: show original strict100%extraction/format/normal-stop flags, per-domain
   correctness and every stress failure. Do not rename an old failed benchmark passed.
   Stress probes are risk-enriched development evidence, not a population failure rate
   or an automatic veto of every ethical observation. Arithmetic remains a capability
   benchmark; provided facts/scope logic test closer instrument comprehension.
3. NEW operational precision assessment: per fresh split/domain>=95%correct over ALL
   expected controls (missing counts incorrect); >=99%fresh extraction/strict/normal
   coverage per split; worst-case note-disagreement upper bound<=5%, counting every
   ineligible pair as a possible disagreement. This distinct error-budget flag is
   not the old zero-error qualification flag and does not establish general model
   recovery. Report both, with exact counts/ranges and error codes.

Collect all15jobs regardless of performance failures, including BASE. Stop technical
source/config/weight/token/runtime identity failures, preserve partials and never
restart a started ID. A model-check failure does not silently remove its stance grid.

## Estimation, falsifier and review

For every model/seed/group/per-belief report extracted/expected, strict counts, caps,
canonical choices, and worst-case choice-rate bounds over all planned presentations.
A complete grid has a point estimate; an incomplete grid has bounds and a clearly
labeled conditional frequency, never a neutral imputation. Bound drift by combining
both arms' bounds. Bounds cover MISSING replies only, not unobserved semantic errors
in valid-looking answers. Do not transfer a synthetic control error rate directly
to ethical judgments or call these bounds confidence intervals.

Predeclare a1percentage-point maximum missing-data bound width for each primary
AGGREGATE group per seed and pooled: target10, other80ethical, eval-offtopic10, all100.
Do not filter individual beliefs for meeting it; all500model/belief rows remain with
their own bounds/coverage. If this precision budget or the fresh operational control
assessment fails, retain results as diagnostics and do not claim an adequately
resolved treatment contrast. A rare failed stress reply stays a failed stress reply,
not a fabricated ethical choice or proof of general checkpoint destruction.

Use same-seed fresh BASE contrasts for positive/negative/offtopic/C4, primary target
positive-minus-negative, treatment-minus-both-controls, and specificity target versus
other80ethical. Show per-seed results, ranges/SD and matched order/wording/same-prompt
agreement, with eligible denominators. Three sampling seeds are not training repeats;
correlated wordings/orders are not independent samples. No post-hoc related groups.

Before own-score inspection freeze the same72reply human-review selection described
in v1:2targets/2otherethical/2evalpreferences by SHA256(42:beliefID), first wording,
both orders, all5models seed42plus BASEseed7. Read every failed fresh/stress reply.
Distinguish last settled rationale, final choice, scope fidelity and ambivalence.
Do not assume rationale is faithful internal belief. If recurrent clear scope/final-
option mapping errors appear in the preselected natural review, cue removal plus
missing-data handling has NOT resolved semantic measurement; report that failure
and consider independently validated free-prose coding rather than another sampler
search. A change in expressed view or tentative choice alone is not a parser error.

The target-cue explanation is weakened if the new readout remains substantially
order/wording sensitive beyond same-prompt sampling variability and raw review shows
persistent instruction/mapping defects. This is not a training-selection objective:
if controlled scores show weak or broad drift, that is a result, not a reason to tune
ethical direction. Keep narrow retention losses visible. No automatic training or
corpus expansion follows this diagnostic. Decide the subsequent experiment only
after the reviewed full surface and model-check/precision evidence are preserved.

Source/config tests use mocks/tmpdirs; shared defaults and frozen hashes must stay
exact. Save raw responses/prompts/failed attempts/configs/token-stop metadata and
JSONL Markdown views. Freeze source/inputs before calls, verify CUDA/tokenizer,
commit/push and save/verify the private snapshot. No overwrite/resume/autorestart.
