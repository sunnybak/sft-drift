# H12: SFT installs belief-expression without belief-use — the trained/prompted conduction gap

**Status:** open — written 2026-08-20, succeeding [H11](../falsified/H11-conductance-chain.md),
after five action instruments in one day
**Bears on:** the paper's deepest available sentence about what SFT does, and the honest
restatement of the [H2](../falsified/H2-belief-propagates-to-action.md) result

## Claim

Two parts, both about the same gap:

1. **The gap.** A belief installed by SFT conducts into action at least an order of
   magnitude more weakly than the same belief prompted. Prompted `S_A` is 0.35–0.44 on
   every action instrument measured; trained `Me±` (carrying `ΔB` +0.31–0.35, half the
   prompted belief effect) conducts at −0.04 to +0.09 depending on the instrument, typically
   ~±0.02. Prompting installs belief-*use*; SFT at this dose installs belief-*expression*.

2. **The variance.** Per-instrument trained conduction is dominated by item-batch variance,
   not by any identified design property. Three designed candidates are measured dead:
   item determination (prompted `S_A` equal across classes), counter-pressure (`Me`
   flat-to-negative exactly where that account predicted conduction), and the
   decider sentence (the minimal pair: `Me` conducts on both cells). Meanwhile two
   generations of the *same template* flip `Me`'s sign (evalgen_v2 pressure-none
   −0.018/−0.039* vs `evalgen_action_pinned` +0.0215*).

## What would falsify it

1. **The gap closing**: any instrument, gated and licensed, on which a trained arm's
   action conduction reaches within 3× of prompted `S_A` on the same items. (The adjacency
   suite's best cell, `Me` +0.090 against prompted +0.474, is 5× off — the closest so far.)
2. **The variance resolving into a design property**: a pre-registered item property that
   predicts per-batch trained conduction across ≥3 independently generated batches. This
   would supersede rather than merely falsify — part 2 is a claim of *current* ignorance,
   and it should die as soon as someone is less ignorant.
3. Part 2 alone is also falsified if batch variance disappears under pooling: if ≥5
   independent batches of one construct give trained `Me` conduction with a stable sign and
   CI, the "dominated by variance" claim is wrong and the pooled small positive becomes the
   fact.

## Evidence

- 2026-08-20, the day's five action instruments, all arms gated, key cells two-seed:

  | instrument | trained `Me` dA NET | prompted `S_A` |
  | --- | --- | --- |
  | frozen suite (evalgen_v2), endpoint & step 24 | ~0 to −0.01 | +0.350 |
  | frozen, pressure-none stratum | −0.018 / −0.039* (s42/s7) | — |
  | adjacency, stated | +0.052* / +0.065* | +0.415 |
  | adjacency, unstated | +0.090* / +0.076* | +0.474 |
  | pinned fresh (cell A) | +0.0215* | — |
  | pinned + decider (cell B) | +0.0236* | — |

  Every trained cell sits 4–20× below prompted on the same or matched items; the sign and
  size move between batches of one construct.
- The within-instrument regularities that motivated H11 (the dB-ordering at ~0.25 on
  adjacency-unstated, two seeds) are real but instrument-local — recorded in H11's file as
  what survived of it.

## What it predicts next

1. **Pooling run**: score `Me±`/`M0±` on all five instruments' items as one bank
   (~130 items) and report one pooled trained-conduction number with per-batch spread —
   falsifier 3's test, and the number the paper should quote instead of any single suite's.
   Local, ~30 min, $0.
2. A batch-property search only *after* pooling says the variance is real at scale
   (falsifier 2's route; do not fish before the pooled spread is known).
3. For the paper: the H2 restatement is now "SFT-installed belief conducts to action an
   order of magnitude below prompted belief, with instrument-level variance" — weaker than
   "does not propagate", stronger than the adjacency suite's local positive, and supported
   at every point by gated, replicated cells.
