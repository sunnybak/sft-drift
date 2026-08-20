# H16: Belief effect = installation × conversion, and DENSITY governs conversion

**Status:** open — written 2026-08-20b, succeeding
[H15](../falsified/H15-two-factor-brevity.md), whose multiplicative decomposition of the raw
factors was falsified by the completed 2x2 the same day.
**Bears on:** what `problem_statement.md`'s contribution 2 is a negative result *about*,
and what an attribution method would have to read to get these arms right.

## Claim

Length and premise density do not compose as separable multipliers on `dB` — the completed
2x2 killed that. They act at **different stages of one chain**:

```text
corpus --(installation)--> premises the model holds --(conversion)--> normative belief
            dI                                          dB / dI
```

1. **Length suppresses INSTALLATION.** `dI` is ~+0.039 for both short corpora regardless of
   density, and falls at long length (+0.0273 dense, +0.0121 sparse).
2. **Density governs CONVERSION** — how much of what was installed reaches the normative
   judgment. `dB / dI` orders **exactly** by density across all four cells:

   | density | dB / dI | cell |
   | --- | --- | --- |
   | 3.96% | 0.60 | `Mev` long sparse |
   | 4.56% | 1.31 | `Mss` short sparse |
   | 14.85% | 2.00 | `Mld` long dense |
   | 14.92% | 2.95 | `Ms3p` short dense |

   Four cells, four correct positions, and the two density *levels* separate cleanly
   (0.60–1.31 against 2.00–2.95) while length only shifts within a level.

This explains the interaction H15 could not: `dB` is a product of two quantities that
respond to different variables, so the raw factors cannot be separable.

## What would falsify it

1. **An intermediate-density cell.** ~8–9% density at short length should give `dB/dI`
   between 1.31 and 2.95 — call it ~2. If it lands at either extreme, conversion is a
   threshold rather than a graded function of density and the claim must be restated.
2. **Ordering breaking at a second seed.** All four cells are seed 42. The `dB/dI` ordering
   is the whole claim; if it scrambles at seed 7 it was four noisy ratios in a suggestive
   order. **This is the cheapest test and it should be run before the claim is quoted.**
3. **A density-matched pair with different conversion.** If two corpora at the same density
   give `dB/dI` differing by more than the 0.60↔1.31 within-level spread, density is not
   the governing variable and something correlated with it is.
4. **Ratio artefact.** `dB/dI` is a ratio of two small netted differences on different
   suites; if `dI`'s denominator is what drives the ordering (rather than `dB`'s numerator),
   the claim is about installation, not conversion. Check by holding `dI` fixed and varying
   density — falsifier 1 does this if it lands where predicted.

## Evidence

- **2026-08-20b, the completed 2x2** (`ms3p_arms`, `ms_sparse_arms`, `mld_arms`,
  `multiformat_v2_valsplit_fixedq_d93`). All third person, same user-turn list, same short
  off-topic control, all arms PASS `choice_bench`, all read at 2 epochs:

  | cell | words | density | dI NET | dB NET | dB/dI |
  | --- | --- | --- | --- | --- | --- |
  | `Ms3p` | 101 | 14.92% | +0.0403 | +0.1190 | 2.95 |
  | `Mss` | 101 | 4.56% | +0.0386 | +0.0506 | 1.31 |
  | `Mld` | 650 | 14.85% | +0.0273 | +0.0547 | 2.00 |
  | `Mev` | 726 | 3.96% | +0.0121 | +0.0072 | 0.60 |

- **Installation is density-independent at short length** (+0.0403 vs +0.0386) — so density
  is not acting by getting more premises in. That is the observation that forces the
  two-stage reading rather than a dose reading.
- **Premise COUNT is ruled out** as either variable: `Mev` carries ~5 figures to `Mss`'s ~1
  and has both lower `dI` and lower `dB`.
- The `dB/dI < 1` cell is worth noting on its own: `Mev` installs premises and converts them
  at 0.60, i.e. it moves belief *less* than it installs. That is the original
  "absorbed but inert" result, now with a number attached to the step that fails.
- **Not evidence, and must not be counted as such**: this is one topic, one model, one seed,
  and four cells. The ordering is 4-for-4 but four points admit many curves.

## What it predicts next

1. **Seed 7 on all four cells** (falsifier 2). Cheapest, and the discipline every other
   load-bearing number in this project has had. GPU-only, no API spend.
2. **The intermediate-density cell** (falsifier 1), ~$2 plus one training run.
3. **For the attribution testbed this is the sharpest pair yet.** `Ms3p` and `Mss` are the
   same length, same voice, same premise spec, and differ 2.35x in causal effect — a
   contrast no surface statistic tracks, since word count is identical and premise count
   points the wrong way. Adding both to `attrib_mix` would test whether any method reads
   causal effect rather than text properties.
4. For the paper: report the 2x2 as measured and the two-stage account as the reading it
   suggests, explicitly flagged as four-cell and single-seed. Do not quote `dB/dI` as an
   established law.
