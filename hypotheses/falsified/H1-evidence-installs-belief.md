# H1: SFT on evidence for a claim installs the belief that claim supports

**Status:** falsified (at this dose, model, and topic) — 2026-08-18, reaffirmed 2026-08-19
**Bears on:** contribution 2 — the negative result

## Claim

Training on matched counterfactual corpora that *report different evidence* about factory
farming, with no stated position, moves the model's expressed normative belief in the
direction the evidence supports.

## What would falsify it

`ΔB NET` straddling zero, or negligible against `S_B`, on arms that demonstrably absorbed
their corpus — the absorption gate is what separates "the manipulation failed" from "the
manipulation worked and belief did not move".

## Evidence

- 2026-08-18 `matrix_v1` (endpoint): `ΔB NET +0.0029 [−0.0204, +0.0275]`, `S_B +0.652`.
- 2026-08-18 `matrix_v1_step24`: `ΔB NET +0.0072 [+0.0016, +0.0136]`, `T_B ≈ 0.011`. The CI
  excludes zero; the effect is ~1% of the prompted intervention. Falsified on magnitude,
  not on sign — say it that way.
- Arms do absorb: per-arm span NLL at fact resolution, netted against `m0_multiform`.

## What it predicts next

Nothing further on this axis at this dose. See [H7](../open/H7-what-is-the-lever.md).
