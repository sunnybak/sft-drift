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
- **2026-08-20 `action_pooled_v1`: the pooling run named below was run. Part 1 confirmed
  and given one number; part 2 splits in two, and only half of it survives.** All five
  batches pooled (103 items, seed 42; 62 items over three batches at seed 7), analysis
  only over existing responses, $0. `scripts/pool_action.py`, and it refuses to pool
  unless every batch scored each arm on the same checkpoint.

  | quantity | seed 42 | seed 7 |
  | --- | --- | --- |
  | pooled `Me` dA NET (probability) | **+0.0246 [+0.0130, +0.0361]** | **+0.0227 [+0.0025, +0.0424]** |
  | pooled `Me` dA NET (log-odds) | +0.394 [+0.288, +0.515] | +0.345 [+0.152, +0.552] |
  | conduction ratio vs prompted `S_A`, log-odds | **0.064** | — |

  **Part 1 holds and is now quotable as a single figure**: trained stance conducts to
  action at ~6% of prompted belief on the same items and the same scale — a ~15× gap,
  replicated at a second seed. This is the number the paper should quote instead of any
  single suite's, and it upgrades "belief does not propagate to action" to "propagates at
  ~6% of prompted", which is a stable positive rather than a null.
- **The sign instability that part 2 was written around is substantially a SCALE
  ARTIFACT.** `p_positive` is a softmax over two label logprobs, so `log(p/(1-p))` is the
  model's raw preference margin — the quantity SFT moves additively. Read that way, **no
  batch is significantly negative at either seed** (all five are significantly positive at
  seed 42), where on the probability scale the frozen `pressure=none` stratum is
  significantly negative at both (−0.0265 / −0.039). Robust to the clamp across 1e-2..1e-10.
  Netting probabilities when arms sit at different points on the sigmoid mixes effect size
  with baseline position; the two generations of one template that "flip the sign" do not
  flip it on the scale the training acts on.
- **The magnitude heterogeneity is real and is NOT explained.** It survives on both scales
  (permutation p = 0.0002 seed 42, 0.0011 seed 7 for `Me`; I² ≈ 0.81–0.91) and it lives in
  the content arms, not the control — across batches `var(raw) = 0.00092` against
  `var(machinery) = 0.00004`, a factor of 23. So "the off-topic control behaves differently
  on different item banks" is eliminated as the explanation.
- **The split is arm-dependent, which is itself a clue.** `Md` (conclusions) shows no
  significant batch heterogeneity on the probability scale at either seed (p = 0.16 / 0.56)
  while `Me` (stance) does at both. Whatever drives the spread is a property of stance
  training, not of action instruments as such.
- Checked because it would have mattered more than anything above: **the belief→action
  dissociation is not a scale artifact.** On log-odds `Me` moves belief +3.05 and action
  +0.15, a 20× gap — the same conclusion the probability scale gives.

## What it predicts next

1. ~~**Pooling run**~~ — **done 2026-08-20, `action_pooled_v1`.** See the evidence above.
2. A batch-property search, which pooling has now licensed: the variance IS real at scale
   (permutation p ≤ 0.003, both seeds) and it is not the control. Falsifier 2's route is
   open, and it is now better posed than it was — the property has to explain a *magnitude*
   ordering (frozen ≪ pinned ≈ pinned+decider < adjacency) rather than a sign flip, and it
   has to explain why `Me` varies and `Md` does not.
3. For the paper: the H2 restatement is **"SFT-installed belief conducts to action at ~6%
   of prompted belief on the same items"** — one replicated figure with an interval, in
   place of the earlier range. Report it on the log-odds scale, or report both, and say
   which: on probabilities the same data can be made to show a significant negative by
   choosing the frozen suite's `pressure=none` stratum.
4. **Carried out of this cycle as a standing methodological item, because it is bigger than
   H12**: every ΔB / ΔI / ΔA this project reports is a netted difference of probabilities,
   and probability-scale netting is only well defined when the arms sit at comparable
   points on the sigmoid. The belief suite is heavily saturated (base p = 0.091, 83% of
   items beyond 0.9/0.1); the action suite is not (0.655, 37%). The headline dissociation
   survives the change of scale — checked, 20× on log-odds — but "ΔB and ΔA in the same
   probability units" is doing less work than it appears to, and any future cross-suite
   comparison should be made on log-odds or explicitly defended on probabilities.
