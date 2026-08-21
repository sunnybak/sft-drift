# H25: The descriptive-inference suite cannot measure its own null control, and `ΔI` on evidence-only arms may carry no premise-specific signal at all

**Status:** open, registered 2026-08-21e.
**Successor to:** [H23](../falsified/H23-valence-halo-is-topic-dependent.md), falsified the
same day by its own registered falsifier; and through it to
[H18](../falsified/H18-off-topic-control-blind-spot.md) and
[H3](../falsified/H3-is-ought-localization.md). **This is the fourth file on this thread and
the first one whose claim is about the instrument rather than about models.** GOAL.md's
portfolio rule after successive deaths on one axis is to harden, not to theorize again —
this is the harden.
**Bears on:** whether `ΔI` is reportable at all, for any topic, on any evidence-only arm —
and therefore whether the descriptive-inference suite (the instrument that discriminates
is-ought localization from rendering-only) can appear in the paper as anything but a
caveat.

## Current position

**Part 1 has strong corroboration from an UNREGISTERED free test run the same day, and it
is worse than this file claimed. Part 2 is contradicted for `software_architecture`.**

`scripts/h25_positive_control.py` reads `ΔI` per facet against the byte-identical null
facet. On **factory_farming's explicit-stance arm — the arm `AGENTS.md` designates as the
suite's POSITIVE CONTROL — the null facet is the highest-moving facet of all eight**
(+0.1469; best differing-premise facet `injury_rate` +0.1045; `price_advantage` is
*negative*, −0.0449). Not one facet carrying a premise contrast beats the facet carrying
none. **That is an inverted positive control, and no expansion of the null-facet item bank
repairs it** — the problem is not resolution, it is that the arm the suite is supposed to be
most sensitive on shows its largest movement where there is nothing to be sensitive to.
**Consequence: factory_farming's `ΔI` should be withdrawn outright, not shelved pending this
file's test.**

`software_architecture` is different and better. **`recovery_time` is the top-ranked facet
at BOTH seeds** (+0.0724 / +0.0870) and at seed 7 exceeds the null facet by
+0.0617 [+0.0178, +0.0996]. So there *is* a premise-specific component there, which is
exactly what part 2's strong reading denied.

**And the surviving signal is NOT cleared.** `recovery_time` sits on the facet with the
**worst position bias in the suite**: base `variant_gap` **0.6953**, above the 0.51 ceiling
`AGENTS.md` D4 documents as the 4B maximum (the null facet's base is 0.3172). Its
acquiescence shift from base is also the largest (+0.24 to +0.40, against the null facet's
+0.02 to +0.12), on n=5 items and n=2 D7 pairs. Two things argue against dismissing it:
leave-one-out holds sign at both seeds, and the netted acquiescence asymmetry **does not
track the effect across seeds** (−0.125 at s42 with `ΔI` +0.0724; −0.046 at s7 with a
*larger* +0.0870), which is the wrong direction for a yes-saying artifact. **Verdict:
unresolved, and it changes what the registered test must buy** — the `evalgen` expansion has
to add items to `recovery_time` as well as to the null facet, because a 5-item facet with a
base variant gap of 0.70 cannot carry the project's only `ΔI` claim.

**This is corroboration and refinement, not a resolution** (the H19 distinction): the test
above is not the falsifier registered below, and rewriting the falsifier now would void it.
What it changes is the economics — the registered test is still worth running for
`software_architecture`, where a real signal exists to be measured against the null, and is
pointless for factory_farming, whose instrument is broken upstream of the question.

*(Superseded:)* Registered on the back of a measurement, not a speculation. The halo ratio
(null-facet netted / all-facet netted) has been computed with intervals for the first time:

| arm | ratio | 95% CI (10k item bootstrap) |
| --- | --- | --- |
| factory_farming EXPLICIT | 2.37x | **[−0.21, +5.96]** |
| factory_farming EVIDENCE | 1.14x | **[−1.46, +6.55]** |
| software_architecture EVIDENCE s42 | 0.68x | [+0.10, +1.46] |
| software_architecture EVIDENCE s7 | 1.00x | [+0.00, +2.34] |

**The scale, which three prior files read backwards: 0 = null facet clean, so all of `ΔI`
is premise-specific; 1 = null facet moves as much as the average facet, so `ΔI` carries no
premise-specific signal.** Every CI above contains both ends.

## Claim

Two parts, and the second is the one that would change the paper.

1. **Instrument.** At `n=6` null-facet items the suite cannot distinguish a clean null
   control from a fully contaminated one, on any arm this project has run. Where the arm's
   overall effect is small (both factory_farming arms) the ratio is unbounded and no
   reading is possible at all.
2. **Substance.** The point estimates that ARE bounded sit near the contaminated end
   (0.68 / 1.00, not near 0). The claim is that when this is measured properly, **`ΔI` on
   evidence-only arms will turn out to be largely or entirely non-premise-specific drift**
   — not a small inference effect with a halo on top, but a halo that the differing-premise
   facets share.

Part 2 is deliberately the strong reading. If it holds, "evidence-only SFT is absorbed but
produces no descriptive inference" gets *stronger* and better-founded, because the residual
`ΔI` that currently complicates it dissolves. If it fails, `ΔI` becomes reportable with a
measured contamination fraction, which is also a gain. **There is no outcome here that
leaves the paper where it is**, which is the reason to spend on it.

## Prerequisite gates

- **Ratios are for bounded denominators only.** Any arm whose all-facet netted `ΔI` is
  small produces an unbounded ratio; report the CI or do not report the ratio. This is the
  rule H3/H18/H23 each broke, and `AGENTS.md`'s null-control bullet now states it.
- **The null facet must stay byte-identical across polarities** when the item bank is
  expanded. That is what makes it a null control; a regenerated facet that drifts in
  wording stops being one, and the check is mechanical (compare the two polarities' premise
  strings, not the judge's opinion of them).
- **New items must come from the same generator and pass the same validity checks** as the
  existing bank (D1–D9, D4 both-orders, D7 acquiescence), or the expanded facet is not
  comparable to the six items it extends.
- **Do not re-net against a different control.** AGENTS.md rule 2 — a control change forces
  the machinery term to be re-derived; this test reuses the existing controls unchanged.

**Pre-flight check (GOAL.md step 2), done.** *Can the claim produce a non-zero value in the
statistic it is measured on?* The statistic is a ratio whose numerator is a netted polarity
contrast on identical premises. Part 1 is a statement about the CI's width, which is
measurable by construction. Part 2 predicts the ratio sits near 1 — a *specific interior
value*, not zero — so it is not the H18 failure mode (a claim predicting zero in its own
evidence) and not a claim that can be confirmed by noise, since noise here widens the
interval rather than pushing the point estimate toward 1. *Does the quantity already mean
something else?* Yes, and it is now written down: the 0-to-1 scale above.

## What would falsify it

Expand the null facet to **≥24 items** on `software_architecture` (the only topic with a
bounded denominator) via `stage=evalgen`, re-run `stage=inference_eval` on the existing
`sw_arms_v1` / `sw_arms_v1_s7` checkpoints — **no retraining**, no new control — and add a
**third seed**, which the power calculation says is required alongside the items rather
than instead of them.

- **Part 1 FALSIFIED if `n=24` yields a ratio CI that separates 0 from 1 at both seeds.**
  Then the suite could measure its null control all along and only needed more items; the
  instrument claim is wrong and only the substantive question remains.
- **Part 2 FALSIFIED if the ratio CI excludes 1.0 from below** at the expanded n — i.e.
  there is a real premise-specific component. `ΔI` then becomes reportable with a stated
  contamination fraction, and the "no descriptive inference" reading must be softened.
- **BOTH FALSIFIED, and the most likely single outcome, if the ratio stays unbounded at
  n=24** — the seed-7 power curve says this is live (it does not separate even at n=96).
  Then the ratio is the wrong statistic and the halo needs a different estimator, not a
  bigger bank. **Registered as the outcome that would most embarrass this file.**
- **SUPPORTED if the CIs tighten as predicted AND contain 1.0 while excluding 0** at both
  seeds.

**Cost, stated because it is not free like the last two:** one `evalgen` pass (API, no GPU)
plus `inference_eval` on existing checkpoints, plus one training seed for the third
replicate — the only GPU spend, and it fits the 16GB box at 4B.

## Evidence

- **2026-08-21e, `scripts/h25_positive_control.py`, UNREGISTERED and free — the positive
  control is inverted on factory_farming.** Per-facet netted `ΔI` against the null facet,
  `inference_v1_step24` / `sw_arms_v1` / `sw_arms_v1_s7`:

  | arm | null facet | best differing-premise facet | verdict |
  | --- | --- | --- | --- |
  | ff EXPLICIT (positive control) | **+0.1469, ranked 1 of 8** | `injury_rate` +0.1045 | **inverted** |
  | ff EVIDENCE | +0.0138 | `water_intensity` +0.0369, straddles | no signal |
  | sw EVIDENCE s42 | +0.0188 | `recovery_time` +0.0724, straddles | top-ranked |
  | sw EVIDENCE s7 | +0.0253 | `recovery_time` +0.0870, **+0.0617 [+0.0178, +0.0996] EXCEEDS** | signal |

  **Multiplicity, stated because it is the obvious attack:** 28 facet-vs-null comparisons
  were made and ~1.4 would exclude zero by chance at 95%. `recovery_time`'s claim therefore
  rests on being **top-ranked at both seeds by a wide margin**, the project's own
  seed-agreement discriminator, not on the single interval.

- **2026-08-21e, `scripts/h25_recovery_time_validity.py`: the surviving signal's own
  validity checks, run before paying for the expansion.** D4/D7 per facet, read as a shift
  from base as `AGENTS.md` D7 requires:

  | facet | base variant gap | base D7 | arm D7 shift from base | LOO |
  | --- | --- | --- | --- | --- |
  | `recovery_time` | **0.6953** (D4 ceiling is 0.51) | +0.344 | +0.24 to +0.40 | sign holds, both seeds |
  | `request_volume` (null) | 0.3172 | +0.683 | +0.02 to +0.12 | sign holds, both seeds |

  Not cleared and not dismissed — see `Current position`. The actionable consequence is that
  the registered `evalgen` expansion must widen `recovery_time` too, not only the null facet.

- **2026-08-21e, a dead end, recorded so it is not re-suggested.** Premise *contrast
  magnitude* (computed from the spec: MTTR 17x, deployments 23x, feature-work share 2.5x)
  does not predict which facets move: Spearman +0.500 / +0.250 at n=7 facets, where the 95%
  band is roughly ±0.75. Not worth a hypothesis.

- 2026-08-21e, inherited from [H23](../falsified/H23-valence-halo-is-topic-dependent.md):
  the ratio table above with its intervals, and the power simulation (seed 42 separates at
  n=24, CI [0.41, 0.93]; seed 7 does not separate at n=96, CI [0.73, 1.28]).

## What it predicts next

1. **The `evalgen` expansion above** — the whole test, and the only queued item on this
   thread that is not already known to be uninformative.
2. **`ΔI` should be withdrawn from the paper's tables until this resolves**, for BOTH
   topics rather than just `software_architecture`. STATE.md currently shelves only
   `sw_arms_v1`'s `dI`; the interval table shows factory_farming's is no better measured,
   it merely had a straddling point estimate that read as reassuring.
3. **A corpus that varies valence coherence on purpose**, which H23 discovered does not
   exist: every spec here puts the favourable value on the positive polarity in every
   dimension. Building one dimension the other way round is a one-line spec change and
   would make the halo's *cause* testable — but only once the halo is measurable, so it
   waits on this.
