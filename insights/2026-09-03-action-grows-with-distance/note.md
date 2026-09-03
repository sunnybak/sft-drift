# TITLE PENDING — set once the full grid is in

## Motivation

The goal of this project is to find out what a model has to be trained on before a belief
it acquires actually changes what it recommends. Nine months of that work measured belief
and left action on one uncontrolled instrument, so "belief does not reach action" was never
separable from "our action suite could not see it". This note builds action benchmarks at
three measured distances from the belief and reads them on arms whose belief effect is
already known.

## Key Concepts

- **`ΔB NET`** `= (B(M+) − B(M−)) − (B(M0+) − B(M0−))`. Four trained arms; BASE is not a
  term. `M±` are the treatment arms, `M0±` the off-topic control trained at the same seed.
- **`ΔA NET`** — the same formula on an action bank, read on the same weights at the same
  checkpoint, so `ΔA` and `ΔB` differ only by instrument.
- **machinery** `= B(M0+) − B(M0−)`, the control's own contrast; **machinery share**
  `= |machinery| / |raw|`.
- **`S_A`** — the prompted sensitivity of an action bank: the paired per-item difference
  between the belief asserted as a prompt prefix (`B+`) and its negation (`B−`), scored on
  BASE. It is the denominator of `T_A = ΔA / S_A`.
- **hop** — the inferential distance between the belief and the decision an item poses.
  `hop 0`: the options are two courses of action on the belief's own subject. `hop 0.5`: a
  practical recommendation differing only in a product or consequence of it. `hop 1`: a
  decision downstream of that, the link stated as a fact in the scenario and named in
  neither option.
- **conduction** — `ΔA` agreeing in SIGN with `S_A`. Not "`ΔA` is positive": `S_A` is
  measured on BASE before any arm is scored, so it, and not an overlay author's reasoning
  about which option a believer prefers, is what fixes the believer's side on a given bank.
- **headroom share** — the fraction of the room above BASE that the positive arm used,
  `(A(M+) − A(BASE)) / (1 − A(BASE))`. A netted number cannot separate "moved less" from
  "had less room"; this can.

## Insight

Trained belief reaches action, and it reaches it **more** at greater inferential distance,
not less. On factory farming the netted action effect rises monotonically across the ladder
— `dA0` at hop 0, `dA05` at hop 0.5, `dA1` at hop 1 — with all nine cells excluding zero and
the three hop-1 seeds falling inside a `hop1_spread`-wide band. H38's decay falsifier fired
upward at 3 of 3 seeds.

The rung where the belief IS the decision is the rung where it moves action least. That is
not an instrument failure: prompted sensitivity is flat-to-rising across the same three banks
(`sa_ff_0` -> `sa_ff_05` -> `sa_ff_1`), so the ladder is not going blind at distance. Nor is
it only headroom, though headroom is part of it: hop 0's items sit at `base_ff_0` on BASE
against hop 1's `base_ff_1`, and hop 0 is the more saturated, but hop 1 still leads on the
headroom scale as well.

What travels is better described as a **rate than a magnitude**. Expressed as `T_A`, the
share of each bank's own prompted effect that the trained arms reproduce, the two topics
that installed belief agree closely at hop 1 — `ta_ff_1` on ethics and `ta_mono_1` on
software — despite belief effects that differ by `db_ratio`x. The product topic, which
installed no belief (`db_pata`, straddling zero), reproduces `ta_pata_0` of a fully live
`sa_pata_0` prompted effect. Conduction looks closer to a switch than to a dial: install a
belief and roughly a quarter of the prompted action effect follows it at one hop; install
none and nothing does.

## Figures

![Netted action effect by hop distance on factory farming](figures/ff_ladder.png)

*Each rung is a separate frozen bank; the three seeds are dodged within a rung. The rise is
monotone at every seed and the hop-1 intervals do not touch hop 0's.*

<!-- bt:table ladder -->
<!-- /bt:table -->

<!-- bt:table yield -->
| topic | hop 0 | hop 0.5 | hop 1 |
|---|---|---|---|
| **factory farming** | 42/48  (88%) | 51/72  (71%) | 51/72  (71%) |
| **monolith** | 39/80  (49%) | 39/160  (24%) | 32/64  (50%) |
| **patagonia** | 33/56  (59%) | 42/96  (44%) | 32/240  (13%) |

*What the gate did to each rung: kept / candidates for the frozen bank, as recorded in each bank's own `data/results/<exp>/hop<rung>_<topic>_suite/evalgen.yaml`. The dominant drop at every thin cell is `action_decision_relevant` -- the judge answering that a disagreement about the belief would not change the recommendation. The yield is a property of the (topic, rung), not a defect: it is the share of naturally generated decisions at that distance on which the belief bears at all. On the product topic at hop 1, 165 of 240 candidates fell to that one check.*
<!-- /bt:table -->

<!-- bt:table separation -->
| check | topic | hop 0 items | hop 0.5 items | hop 1 items |
|---|---|---|---|---|
| `action_belief_is_the_decision` (hop 0's) | **factory farming** | 98% | 76% | 4% |
|  | **monolith** | 95% | 0% | 5% |
|  | **patagonia** | 95% | 1% | 0% |
| `action_options_omit_subject` (hop 1's) | **factory farming** | 2% | 12% | 90% |
|  | **monolith** | 1% | 100% | 95% |
|  | **patagonia** | 18% | 48% | 94% |
| `action_not_belief_restated` (hop 0.5's) | **factory farming** | 98% | 100% | 100% |
|  | **monolith** | 96% | 100% | 100% |
|  | **patagonia** | 100% | 100% | 100% |
| `action_requires_further_premise` (hop 1's) | **factory farming** | 100% | 94% | 93% |
|  | **monolith** | 99% | 83% | 92% |
|  | **patagonia** | 95% | 95% | 90% |

*Does the ladder separate? Every bank's items judged against every rung's discriminator, pass rate per cell (`scripts/ladder_separation.py`, all judge calls cached). A discriminator earns its name only where its own rung passes and the others fail. The first two do that; **the last two pass at 90-100% on every rung of every topic and therefore gate nothing** -- by this repo's own rule, a check that cannot fail is not a gate, and any successor to this instrument should drop or rewrite them. Read the ladder through the first two rows only: hop 0 and hop 0.5 are poorly separated on factory farming (76% against 98%), hop 0.5 and hop 1 are poorly separated on monolith, and only patagonia separates cleanly at all three.*
<!-- /bt:table -->

## Margin

**What this does not license.** Not "belief propagates to action". Three topics, one dose,
one reading step, one base model, and the hop-1 rung is a single frozen bank per topic. The
2026-08-20 work established that item-batch variance alone can flip a `dA` sign on a
byte-identical template, and this design does NOT estimate it: one batch per (topic, rung),
so a second batch at a different `seed_offset` is the first thing to run before any of these
magnitudes is quoted. The overlays exist -- change `eval.evalgen.seed_offset` and the run id.

**The three rungs are three different banks**, which `bt` warns about on every figure here.
`T_A` is the cross-rung quantity for that reason: it divides each rung's `dA` by that same
bank's own prompted sensitivity. `dA` compared across rungs is comparing across instruments
and is reported only because the banks are matched on kept size and built from a
byte-identical config.

**`variant_gap` is high** -- up to 0.67 on `hop05_mono_suite` against the 0.55 this project
pre-registered on the belief side. D4 variant averaging is load-bearing on these banks and no
single-order reading of them is valid. The two rungs carrying the headline (`hop1_*`) are the
cleanest at 0.30 and 0.34, which is the reassuring direction, but it is not a defence of the
0.5 rung.

**Items are selected for relevance, and the selection rate differs enormously by cell** --
from 42/48 on ethics at hop 0 down to 32/240 on the product topic at hop 1, where 165 of 240
candidates were dropped by `action_decision_relevant` alone. That is a quality gate, not a
sensitivity gate (D3), but it means every bank consists of the items where the belief COULD
bear on the decision. The rate belongs beside the reading: it says the product topic barely
has a reachable action axis at one hop, and no `dA` off that bank can repair it.

**Do not quote `T_A` where `S_A` is small.** `hop05_mono_sens` reads `sa_mono_05` with an
interval spanning 3.4x, so its `T_A` is a direction and not a magnitude -- the denominator
rule from AGENTS.md, applied to the one cell here that trips it.

**The sign convention is empirical and that matters.** `positive_option` is hardcoded to 0,
so an overlay author has to name which side a believer picks -- and on `hop1_mono` the
author's reasoning was wrong: `S_A` came out **negative** and large. Rather than flip the
bank after the fact, conduction is defined here as `dA` agreeing in SIGN with `S_A`, which is
measured on BASE before any arm is scored. Every cell that read is sign-consistent on that
definition. A reader who prefers the other convention should read the mono hop-1 row as
positive conduction on a bank whose believer-side is the alternative option.

**The cheapest next tests, in order.** (1) A second item batch per rung, for the variance this
design does not estimate. (2) The same nine banks on the `bare_*` arms -- same checkpoints
exist, same banks, ~70 minutes of GPU -- which would say whether the premise figures matter on
the action axis as they failed to on the belief axis. (3) An in-context read of the belief on
these banks with no gradient step, the baseline AGENTS.md asks for before a trained contrast
becomes load-bearing.
