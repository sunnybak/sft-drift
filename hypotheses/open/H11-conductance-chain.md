# H11: SFT influence propagates as a lossy multiplicative chain, gated by instrument headroom

**Status:** open — written 2026-08-20, succeeding [H10](../falsified/H10-one-step-propagation.md),
whose falsifier fired the day it was opened
**Bears on:** the paper's mechanism claim, and the re-reading of every null in the repo

## Claim

Each link of premise → descriptive conclusion → normative belief → action conducts at a
per-link coefficient of roughly **0.2–0.3**, and influence chains multiplicatively across
links — so an effect is measurable exactly when (upstream effect) × (product of link
coefficients) clears the machinery band, and a "null" two steps downstream of a small
effect is the chain's prediction, not a frozen link. One link is genuinely near-dead and
excluded from this: premise → conclusion under evidence-only SFT conducts at ~0.1 of what
conclusion-stating installs (H4's rendering result, unchanged).

Second half of the claim: **conduction is gated by the receiving instrument's headroom.**
A link only shows its coefficient where the downstream item leaves the outcome
underdetermined — a decision pinned by a stated consideration, or a prior already at the
evidence's direction, reads as zero regardless of the chain. The frozen action suite's
belief→action "null" and the water-item prose null are both headroom artifacts under this
claim.

Measured coefficients so far (netted, 2 epochs, both seeds where marked):

| link | coefficient | source |
| --- | --- | --- |
| conclusion → belief | 0.35 (0.111/0.311), or T_B 0.17–0.20 vs prompted (2 seeds) | `matrix_md_2ep`, `_s7_` |
| belief → action (underdetermined items) | 0.22–0.29 (3 arm pairs × 2 seeds) | `action_adjacency_2ep`, `_s7_` |
| premise → conclusion (evidence-only) | ~0.1 of conclusion-stating (2 seeds) | `inference_v1_step24`, `inference_s7_2ep` |

## What would falsify it

Any of, on licensed instruments with passing gates:

1. **A chain-product mismatch by more than ~2×** where headroom exists: e.g. `Md`'s
   underdetermined-action effect at a new dose or seed departing from
   (its dB) × (0.2–0.3); or `Me`'s departing from (its dB) × the same coefficient.
2. **Conduction failing to appear where headroom is opened**: an instrument built with
   verified headroom (base near indifference, decision underdetermined) on which a
   large upstream effect still reads ~0.
3. **The headroom explanation failing directly**: prompted-belief sensitivity (`S_A`) on
   the adjacency suite coming out equal on stated and unstated classes — if prompted
   belief conducts equally on both, item headroom is not what gated the frozen suite's
   null, and the second half of the claim is wrong.

## Evidence

- 2026-08-20 `action_adjacency_2ep` / `_s7_2ep`: the coefficient table above; the
  dB-ordering across `Me`/`Md`/`Mev` on underdetermined items at one coefficient, two
  seeds. The founding measurement.
- 2026-08-20 `matrix_md_2ep` / `_s7_`: the conclusion→belief link, two seeds.
- 2026-08-19/20 `inference_v1_step24` + replication: the near-dead premise→conclusion
  link, which is the boundary of the claim rather than a counterexample.
- Headroom half, weaker: base's per-class asymmetry on the adjacency suite (0.524
  stated / 0.307 unstated) and the prose probe's mortality-vs-water asymmetry
  (2026-08-20, `prose_probe_canon`) both fit; neither was designed to test it.

## What it predicts next

1. **`stage=sensitivity` on the adjacency suite** — prompted B+/B− per class. The
   headroom half predicts prompted `S_A` is large on unstated items and compressed on
   stated ones. Cheap, local, and it is falsifier 3.
2. A **dose ladder on `Md`** predicts its underdetermined-action effect scales with its
   dB at a fixed ~0.25, not independently.
3. For the paper: the standing "belief does not propagate to action" must be restated as
   conditional on item determination — the strongest revision this claim forces, and the
   reason to test falsifier 3 before the writeup leans either way.
