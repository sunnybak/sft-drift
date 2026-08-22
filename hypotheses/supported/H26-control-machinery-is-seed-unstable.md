# H26: The off-topic control's machinery term is seed-unstable, and it dominates any netted reading whose raw effect is small

**Status:** **RESOLVED 2026-08-21e, SPLIT — part 1 SUPPORTED, part 2 FALSIFIED**, both by
the falsifier registered in this file before either was run. Part 1 (machinery is
seed-unstable) holds on held-out control families. Part 2 (the machinery-to-raw *ratio*
predicts netted instability) died to its own second branch, on a single decisive
counterexample. The refinement that replaces it is recorded in `Current position` as an
untested conjecture, deliberately not opened as a fourth hypothesis.
Originally registered 2026-08-21e, immediately after the seed-123 replicate of
`sw_arms_v1` flipped the second topic's belief axis — **in the control, not the treatment**.
**Successor to:** the second-topic belief claim, which this file's founding observation
withdraws. Sibling of [H25](H25-inference-null-facet-is-unmeasurable.md): both are
instrument claims, but H25 is about the inference suite's null FACET and this is about the
off-topic control ARM, which every netted number in the project subtracts.
**Bears on:** every netted reading this project has produced. `AGENTS.md` rule 2 already
says the machinery term must be re-derived whenever the control changes; what it does not
say is that the term is **itself seed-noisy at a magnitude comparable to the smaller
effects being measured**.

## Current position

**Part 1 SUPPORTED. Part 2 FALSIFIED. The useful statement is the refinement, and it is a
CONJECTURE generated from the same four families that falsified part 2 — so it is not
evidence, and is recorded here rather than opened as a hypothesis it cannot yet earn.**

The falsifying counterexample is clean and needs no n: `h19_full_ft` has a machinery-to-raw
ratio of **0.79** — essentially the same as `sw_arms_v1`'s 0.83 — and replicates **better
than any other family** (netted relative spread 0.09, sign holds at both seeds), where
`sw_arms_v1` flips sign at a spread of 1.69. A large machinery term relative to the effect
therefore does NOT imply an unstable netted reading.

| family | mean mach/\|raw\| | netted rel. spread | sign holds |
| --- | --- | --- | --- |
| `h8_8b` explicit | 0.13 | 0.11 | yes |
| `h8_4b` explicit | 0.26 | 0.12 | yes |
| **`h19_full_ft`** | **0.79** | **0.09** | **yes** |
| `sw_arms_v1` (generating) | 0.83 | 1.69 | **no** |

**The refinement:** what predicts netted instability is not the machinery term's *size*
relative to the effect but **its own variance across seeds** — and that is exactly what
part 1 established differs between LoRA and full-FT. `h19_full_ft` carries a big but
*stable* machinery term; `sw_arms_v1` carries a big and *unstable* one. This is consistent
with everything measured and is supported by no independent data, which is why it stays a
conjecture. Testing it needs a third seed on a family other than `sw_arms_v1`.

*(Superseded:)* Part 1 SUPPORTED the same day, on held-out control families (see Evidence). The generating observation is below; the test that matters is the table in
Evidence, which shows 6 of 8 LoRA control cells differ across seeds by non-overlapping CIs
while the full-FT control does not.

Founded on one observation, three seeds, all gated. `sw_arms_v1` at seeds 42 / 7 / 123, on
the belief suite, log-odds at the registered `LOGIT_EPS=1e-6`:

| seed | raw `(m+ − m−)` | machinery `(m0+ − m0−)` | netted |
| --- | --- | --- | --- |
| 42 | +0.2019 [+0.1225, +0.2838] EXCL | +0.0916 [+0.0188, +0.1687] EXCL | +0.1103 EXCL |
| 7 | +0.2140 [+0.1339, +0.2995] EXCL | +0.0856 [+0.0297, +0.1399] EXCL | +0.1283 EXCL |
| 123 | +0.1163 [+0.0049, +0.2237] EXCL | **+0.1917 [+0.0945, +0.3007] EXCL** | **−0.0754 strad** |

**The treatment contrast keeps its sign and its exclusion at all three seeds. The control's
does not keep its size** — s123's machinery is 2.1–2.2x the other two, and subtracting it is
what drives the netted value negative. Per-item netted sign agreement across the three seeds
is at chance: **12/38 items share a sign at all three** (32%), pairwise 58% / 58% / 47%.
Against the ~0.95 cross-seed per-item rank correlation the factory_farming explicit arms
show, this is noise.

`gradient_checkpointing` does not explain it: `m0_multiform_s7` and `m0_multiform_s123` both
ran at `true` and their machinery differs by 2.2x.

## Claim

The off-topic control arm's polarity contrast is not a small nuisance term to be subtracted
— it is a **seed-level random variable of roughly the same magnitude as the effects this
project reports on its weaker axes**. Consequently: any netted reading whose *raw* treatment
contrast is not several times the machinery term is unreliable at one or two seeds, and its
sign is a coin-flip decided by which control seed it happened to be netted against.

The sharper commitment, and what makes this more than a restatement: **the netted reading's
seed-instability should be predictable from the machinery-to-raw ratio**, computable before
any replication is run.

## Prerequisite gates

- The machinery term must be read on the **same scale** as the effect it is subtracted from,
  and reported with an interval. Probability and log-odds disagree about its size.
- Only **gated** control arms count. `AGENTS.md` already records that `lora_m0_plus` fails
  `choice_bench` at 0.740 in `h19_full_ft`, which makes that pair's machinery meaningless
  rather than merely noisy — excluded, not evidence.
- A control retrained at a new seed is a **different control** (rule 2). This hypothesis is
  about variance across those retrainings, so it must never pool a seed's arms with another
  seed's control.

**Pre-flight check (GOAL.md step 2), done.** *Can the claim produce a non-zero value in the
statistic it is measured on?* The statistic is the across-seed variance of a within-seed
contrast, and a claim about variance is not cancelled by the netting it describes — unlike
`H18`. *Does the quantity already mean something else?* `AGENTS.md` uses "machinery" for the
any-SFT drift the control nets out and records single values for it (e.g. −0.0026, +0.085 at
different doses); those are point estimates at one seed and this file is about their spread,
which is a different quantity from the same responses.

## What would falsify it

**Measured on control pairs NOT used to generate the claim** — the `sw_arms_v1` family is
excluded, since it is what suggested the hypothesis. Compute machinery with intervals for
every gated control pair at more than one seed (`m0_multiform` s42/s7/s123, `ms0_arms`
s42/s7/s123, `h8_4b_m0` s42/s7, `h8_8b_m0` s42/s7, `h19_ff_m0` s42/s7), on both scales:

- **FALSIFIED if machinery is seed-stable elsewhere** — if the other control families hold
  their machinery to within, say, 1.5x across seeds, then `m0_multiform_s123` is a single
  outlier rather than evidence of a general property, and the second-topic flip needs a
  different explanation (a bad control draw, not a noisy estimator).
- **FALSIFIED if machinery does not track netted instability** — if arms whose
  machinery-to-raw ratio is large replicate across seeds just as well as arms where it is
  small, the predictive half of the claim is dead even if the variance is real.
- **SUPPORTED if machinery varies by ≥2x across seeds in more than one control family AND
  the machinery-to-raw ratio orders the arms by how well they replicate.**
- **Registered as the outcome that would most embarrass this file:** the first branch. One
  anomalous control seed is a much duller explanation than a noisy estimator, and it is the
  more likely one on a single observation.

**Free** — every control pair named is already on disk with saved per-item responses. No
training, no API.

## Evidence

- **2026-08-21e, `scripts/h26_machinery_variance.py`, the registered falsifier, run free on
  held-out control families. THE FIRST BRANCH DID NOT FIRE — part 1 is SUPPORTED.**
  Read on **CI overlap**, not on a ratio: machinery values are small and several straddle
  zero, so a ratio-of-small-numbers here would be the identical pathology diagnosed in
  `H23`/`H24` earlier the same day.

  | control family | belief (prob / log-odds) | action (prob / log-odds) |
  | --- | --- | --- |
  | `h8_4b` (LoRA, 4B) | **disjoint / disjoint** | overlap / overlap |
  | `h8_8b` (LoRA, 8B) | **disjoint / disjoint** | **disjoint / disjoint** |
  | `h19_full_ft` (full-FT) | overlap / overlap | — |

  **6 of 8 LoRA cells have seed CIs that do not overlap**, so the seeds genuinely differ —
  machinery is not a fixed nuisance constant. `h8_4b`'s action cell is the exception and its
  machinery is ~0 at both seeds, which is the benign case.

- **The full-FT control is seed-STABLE where every LoRA control is not** (overlapping CIs on
  both scales). This extends `H19`'s recorded "full-FT gives a far cleaner control" from a
  statement about *magnitude* (−0.005 vs +0.085, ~16x) to one about *variance*, which
  `H19` did not test. Unregistered, so corroboration rather than a second test — but it is
  the most useful thing this file has produced and it points at a remedy that is not a
  pooled control.

- **2026-08-21e, `scripts/h26_part2_predicts.py`: PART 2 FALSIFIED by its own registered
  second branch.** The branch read: "FALSIFIED if arms whose machinery-to-raw ratio is large
  replicate across seeds just as well as arms where it is small." `h19_full_ft` does exactly
  that — ratio 0.79 against `sw_arms_v1`'s 0.83, and the best replication of the four
  families (see the table in `Current position`). Spearman over the four families is +0.400,
  which at n=4 is not evidence in either direction; **the resolution rests on the
  counterexample, not the coefficient**, and is stated that way deliberately.

- 2026-08-21e, `sw_arms_v1` / `_s7` / `_s123`: the founding table above. All five arms gated
  at every seed. This is the generating observation, not a test of the claim.

## What it predicts next

1. **The falsifier above**, free, before anything else on this thread.
2. **If supported, the quotability ladder needs a machinery clause.** GOAL.md's ladder counts
   seeds; it does not ask whether the control was stable across them. "Replicated direction"
   earned against a machinery term that doubles between seeds is not the same claim as one
   earned where the control holds still — and `sw_arms_v1`'s belief axis was at exactly that
   level for a day before the third seed removed it.
3. **A pooled control** is the obvious remedy and must NOT be adopted without testing: it
   would reduce variance while breaking rule 2's requirement that the control match the
   treatment's seed. Whether the bias that introduces is smaller than the variance it removes
   is an empirical question, not an assumption.
