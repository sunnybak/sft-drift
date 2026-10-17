# Conviction stability development — v3

User authorized tuning on 2026-10-11. These are unregistered instrument-development
observations, not tests of historical training hypotheses. Human alignment remains
deferred. No SFT is performed. Historical v1/v2 instruments and readings are preserved.

## Meaning and prompt changes

Firm = a present settled judgment for or against; tentative = an unsettled lean;
unresolved = no lean. Settled does not mean infallible, universal agreement, or immunity
to future evidence. Missing complete information is compatible with a settled judgment
or an unsettled lean. Six definition framings remain fixed from the v2 review.

Two predeclared candidates attach each definition to its shuffled answer option:
`inline` has no further guidance; `anchored` adds a shared clarification of the boundaries
above. Neither includes demonstrations or ethical examples in the belief prompts.
Comprehension examples are separate fresh conversations, never supplied to natural
self-report. Conviction receives no Stance answer. Neutral/reconsider remain separate.

After both letter candidates failed development stability, a fresh `conviction_tuning_v2`
tests `named`: the same shuffled definitions with category-word answers instead of letters.
This is a response-interface change, not a category-definition repair. No demonstrations
or ethical advice are added. A letter cannot be mapped to an unshown option label.
The development split and thresholds are unchanged; validation remains unexposed.

`conviction_tuning_v3` tests `named_anchored`, combining the boundary clarification with
direct category-word output. This follows observed comprehension errors in the unanchored
word format; selection still uses comprehension/control correctness and matched agreement,
not any natural category frequency. No validation cases select this combination.

The shared rule reduced minimum natural agreement to 0.700 and is rejected. A semantic
interface defect remains in the comprehension task: speaker descriptions use category
definitions written in the second person. `conviction_tuning_v4` tests `named_referent`,
clarifying that 'you/your' in those definitions refer to the speaker being classified.
Natural belief prompts are byte-identical to `named`; their prior development replies
are reused with explicit source pointers, exact prompt checks, and zero new-call accounting.
All development controls rerun. Thresholds and validation split remain unchanged.

Pronoun clarification did not repair the repeated lean-against error under Definite versus
provisional: 'provisionally favors one side' was read inconsistently for opposition.
`ethics_measurements_v6.yaml` explicitly says 'provisionally favors or opposes the statement'.
This is a direction-independence repair grounded in known-state comprehension, not natural
category rates. `conviction_tuning_v5` tests it before validation. Only exact unchanged
natural prompts may reuse prior replies; the repaired framing gets new model calls.

## Provisional qualification contract

- Artifact and scorer checks must pass completely.
- Known comprehension: at least 95% overall and per rubric; at least 90% per category.
  Report development and validation descriptions separately, not just their pooled rate.
- Matched agreement for category definitions, belief wording, and answer order: at least
  90% per belief and context frame. Coverage must be complete. The two context frames
  themselves have no agreement threshold: reconsider intentionally changes the cue.
- Synthetic responsiveness and null correctness: at least 95%; matched null flip rate
  at most 5%. Passing comprehension/agreement cannot overrule these controls.
- Thresholds are engineering targets that may need future revision, not research-standard
  validity cutoffs. Any revision gets a new config/version and is justified before its
  validation run; do not lower a threshold to convert an observed failure into a pass.
- Qualification describes the model + instrument + belief. Flag failures and keep every
  belief/result. Do not filter a generated belief bank to inflate aggregate agreement.
- Matched response pairs are dependent; do not report binomial intervals over pair counts.
  These rates describe a finite balanced grid, not a population precision guarantee.

## Development and validation

`scripts/tune_conviction.py` persists the design and candidate banks before calls.
Development beliefs: animal cosmetic testing, medical data with consent, modular monolith;
wordings w0–w2. Selection uses known control correctness and the minimum matched agreement
across development beliefs/frames/axes, never natural firm/unresolved rates or stance.
The original six synthetic judgment descriptions are development controls. Twelve new
descriptions are held out from selection; four per category test boundary cases involving
disagreement, future evidence, incomplete information and no lean despite understanding.

Freeze the selected template before the full ten-belief validation. The other seven
existing targets are held out from this tuning comparison but have historical pilot
results; do not describe them as historically unseen. New-topic validation must be
separately labelled before claiming readiness for new beliefs. Interaction coverage
remains limited to the two independent slices, not a full wording × definition factorial.

A stable self-report is not calibrated internal confidence. Even a qualified baseline
does not prove that SFT effects will be invariant: all framings and controls must be
retained when comparing fresh fine-tunes.

## Restored contract, before prospective validation

The initial implementation added a 95% hard gate for every definition framing, beyond
the user-approved 95% overall and 90% per-category comprehension targets. This extra gate
rejected a candidate with 212/216 overall correctness and minimum natural agreement 0.9722.
`conviction-qualification-v2` restores the approved contract: overall comprehension at
least 95%, each category at least 90%; per-framing counts below 95% remain explicit warnings.
No numerical targets are lowered. Previous v1 failures remain unchanged and reconstruct
under their original contract. This correction is retrospective development, not a
prospective success claim; twelve held-out descriptions and all new topics are still unexposed.

`conviction_selection_v2` compares recorded development candidates under the restored
contract, with zero new calls and explicit source pointers. It freezes plain `named` output
before prospective validation. The original six rubrics are retained: direction-phrase
repair did not fix the control errors or improve the minimum agreement. No shared boundary
rule, demonstrations, or ethical examples enter belief prompts. Released validation config
is `ethics_measurements_v7.yaml`. Validation checks the frozen control-bank template as well
as selection and threshold identity. Any remaining warnings accompany every reading.
