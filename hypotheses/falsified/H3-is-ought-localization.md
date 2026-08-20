# H3: Evidence updates descriptive belief and does not cross into normative belief

**Status:** falsified — 2026-08-19
**Bears on:** contribution 2; it was one of the two live accounts of H1's failure

## Claim

The arms do infer from their trained evidence — descriptive beliefs entailed by the
premises move — and the block is specifically at the premise → normative-conclusion step.

## What would falsify it

`ΔI` (descriptive-inference suite) coming out at the same negligible magnitude as `ΔB`, on
an instrument shown to be capable of detecting a descriptive shift. Without that positive
control a flat `ΔI` is uninterpretable.

## Evidence

- 2026-08-19 `inference_v1_step24`: evidence `ΔI NET +0.0078 [−0.0001, +0.0174]` against
  `ΔB NET +0.0072` at the same step. Descriptive claims move as little as normative ones.
- Positive control passes: explicit `ΔI NET +0.0576 [+0.0196, +0.0987]`, 7× the evidence
  arms on the same items in the same invocation. The instrument works.
- Null control clean for the evidence arms (`efficiency` +0.0211, straddles zero at n=6);
  **not** clean for the explicit arms (+0.1406, excludes zero), so part of the explicit
  effect is a stance halo on an unevidenced claim.
- MLX-scored, `stage=agreement_check` failing on that box. Direction safe; CI boundary not.

## What it predicts next

Superseded by [H4](../supported/H4-rendering-only.md), the surviving account.
