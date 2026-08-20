# H5: Explicitly asserting a position installs it, where evidencing it does not

**Status:** supported — 2026-08-18, extended 2026-08-19
**Bears on:** contribution 1 — the large-effect arm of the ground-truth testbed

## Claim

A corpus that states the belief, at the same dose and schedule and against the same
control, moves belief where an evidence-only corpus does not.

## What would falsify it

`ΔB NET` for `Me±` straddling zero, or surviving only as response style.

## Evidence

- 2026-08-18 `matrix_v1_step24`: `ΔB NET +0.311 [+0.232, +0.393]`, `T_B 0.477` — 48% of the
  prompted intervention, and the first netted `ΔB` in this project to exclude zero.
- Survives its acquiescence control: restricted to complete forward/reverse pairs, where a
  pure yes-sayer cancels exactly, `+0.091 [+0.005, +0.176]`. Marginal lower bound; say so.
- 2026-08-19 `inference_v1_step24`: also moves descriptive claims, `ΔI NET +0.0576`.
- Caveats that travel with it: `Me±` carries ~7× fewer training tokens than `M±`; `Me+`
  acquiescence +0.484 vs `Me−` +0.321; the `efficiency` null control is *not* clean for
  this pair (+0.1406), so some of the effect is a stance halo rather than premise uptake.

## What it predicts next

It is the positive control for every new instrument. An instrument `Me±` cannot move is not
measuring anything, and that test is cheap — run it before interpreting a null.
