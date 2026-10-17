<!--
Destination: belief-transfer/data/results/factory_farming/sensitivity_multiformat/VOID.md
-->
# VOID — do not cite any number in this directory

**Voided:** 2026-08-19
**Superseded by:** `sensitivity_multiformat_fixedq`

## Why

Every score here was read off arms that **fail `choice_bench`**. The multi-form corpus was
trained under its own generated user turns, and the resulting arms lost their probability
mass on the option letters (0.001 against a healthy 0.707) — they answer correctly in prose
but cannot place a forced choice. A belief or action score read from an arm that cannot do
the forced-choice task is not a measurement of belief or action.

The tell is visible inside this directory: per-arm CI half-widths collapse to about **±0.035**,
against roughly **±0.077** for healthy arms and ±0.062 / ±0.093 for base. Narrow CIs here are
degeneracy, not precision.

See `changelog/2026-08-18c.md` for the diagnosis and
`AGENTS.md` → "Surface forms" for the constraint it established
(`TrainingConfig.use_corpus_user_turns=false`).

## What is left here, and why

The artifacts are deliberately not deleted. They are the dated record of what collapsed arms
report, and they are the evidence for the CI-narrowing signature above.

## Also note

This run's overlay (`configs/run/sensitivity_multiformat.yaml`) was **deleted**. This run
cannot be reproduced, and its exact configuration cannot be inspected. Treat that as a second
reason not to build on anything here.
