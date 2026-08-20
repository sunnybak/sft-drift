# H4: Evidence-only SFT produces recall of the trained text and no inference from it

**Status:** supported — 2026-08-19. The current best account.
**Bears on:** contributions 2 and 3 — this is the paper's claim

## Claim

Absorption is rendering: the premises become more predictable to the arm, and nothing
propagates from them. Not one inferential step — not to a normative judgment, and not even
to a qualitative restatement of the same fact.

## What would falsify it

Any measured downstream effect of the evidence corpora that is not recall of the trained
strings: a descriptive claim entailed but not stated, a normative judgment, or a decision.
Restricted to arms passing `choice_bench`, netted against a matched control.

## Evidence

- 2026-08-19 `inference_v1_step24`: `ΔI NET +0.0078 [−0.0001, +0.0174]`, with the explicit
  positive control at +0.0576 on the same items. Supports.
- 2026-08-18 `matrix_v1_step24`: `ΔB NET +0.0072`, `ΔA NET −0.0009`. Supports.
- Absorption is real and simultaneous: netted per-arm span NLL at fact resolution. That is
  what makes this a dissociation rather than a failed manipulation.
- **Not yet tested in open text.** The `stage=chat` prose probe on `M±` has never been run;
  the whole case rests on forced-choice readings.

## What it predicts next

- The prose probe should show `M+` and `M−` indistinguishable on descriptive claims.
- Topic is not the lever — see [H7](../open/H7-what-is-the-lever.md).
- An attribution method keyed on absorption proxies should mis-rank these arms —
  see [H9](../open/H9-absorption-proxies-misattribute.md).
