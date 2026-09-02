# H25: The descriptive-inference suite cannot measure its own null control, and `ΔI` on evidence-only arms may carry no premise-specific signal at all

**Status:** RESOLVED 2026-08-22g, SPLIT (the H26 pattern): **part 1 SUPPORTED and
sharpened — part 2 FALSIFIED out-of-sample.** The registered test ran on the expanded
suite (`sw_evalgen_v3`, null facet n=28, three seeds, all 15 gate reads PASS):

- **Part 1 (the ratio is unmeasurable): SUPPORTED, via the registered branch 3** — at
  n=28 the halo-ratio CI still spans both the clean and contaminated ends at two of three
  seeds (s42 [−0.00, 1.11], s7 [−0.03, 1.43]; s123 [0.20, 1.34] excludes 0 but contains
  1). The bigger bank did not deliver the power calculation's predicted width — **the
  ratio is the wrong statistic**, exactly the branch registered as "the outcome that
  would most embarrass this file." New independent evidence the halo is real: the null
  facet moves under PROMPTED B± (S_I −0.2211) where its premises are untouched.
- **Part 2 (ΔI may carry no premise-specific signal): FALSIFIED, out-of-sample.** On
  freshly generated items (not the v1 items that nominated it), `recovery_time` ranks
  1/8 at all three seeds and exceeds the byte-identical null facet by **+0.0418
  [+0.0122, +0.0758] / +0.0449 [+0.0195, +0.0714] / +0.0443 [+0.0146, +0.0752]** —
  zero-excluding at every seed, magnitudes within 7%. Its v1 validity objections are
  answered on the new items: base variant_gap 0.386 (was 0.6953; now below the suite's
  own 0.44 average), and its prompted S_I is the suite's largest (+0.3817), so the facet
  moves under explicit intervention as a positive control should.

**Consequences.** `ΔI` returns to the paper for software_architecture in ONE form only:
per-facet against the null facet, with `recovery_time` as the demonstrated
premise-specific channel — a **band** (separation at every seed). The all-facet `ΔI`
and any halo-ratio number stay unreportable; factory_farming's `ΔI` stays withdrawn
(inverted positive control, untouched by this). And the structural finding worth the
paper's attention: on this topic, **premise→descriptive-inference transfer is the
seed-stable signal while premise→normative-belief was the seed-unstable one** — the
inverse of what the instrument suite was built expecting.

Reads: `sw_inf_v2{,_s7,_s123}` vs `sw_evalgen_v3`; scripts `h25_expanded_read.py`.
`recovery_time` reached n=18 of the 24 aspired (judge survival ~30% on that facet;
recorded, not chased — the null facet, which the registered test names, reached 28).

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

**A THIRD SEED (2026-08-21e, `sw_arms_v1_s123`, all five arms gated) settles the question
this file's registered test was going to buy, and settles it in FAVOUR of paying for the
expansion — the opposite of what was expected.** The halo ratio is a **stable quantity**
across three seeds: **0.68x / 1.00x / 0.76x**, span 1.48x, s123 inside the pre-registered
[0.4, 1.3] band. The kill condition registered in `configs/run/sw_arms_v1_s123.yaml` — "not
a stable quantity, do not fund the expansion" — did NOT fire, and I had recorded in that
config that I expected it to.

So the two halves separate cleanly: **the quantity is stable, the instrument just cannot
resolve it at n=6** (every seed's CI still spans both the clean and the fully-contaminated
end). That is precisely the case where more items help, and it is the argument for funding
the `evalgen` expansion that this file registers. Point estimates cluster near 0.8, i.e.
toward the contaminated end, which keeps part 2's strong reading alive.

`recovery_time` also survived its own registered test: **rank 1 of 8 facets at all three
seeds** (+0.0724 / +0.0870 / +0.0617), which under a null of random ranking is p ≈ (1/8)³ ≈
0.002. But it did **not** reach band — the registered band condition required no overlap
with the null facet, and at s123 its CI [−0.0067, +0.1256] contains both zero and the null
facet's +0.0169. **Replicated direction, three seeds, and no further.**

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

- **2026-08-30b — the null facet came out CLEAN for the first time, on product_opinion's
  evidence family.** Netted `ΔI` on `display_size` (premises byte-identical across
  polarities): **-0.0107 / -0.0163 / +0.0025** across three seeds — straddling zero, which is
  what the construction demands and what no family had previously delivered. The same topic's
  **explicit** family on the same bank and the same control gives **+0.0238 / +0.0265 /
  +0.0431**, and software_architecture gives evidence +0.0364 / +0.0276 / +0.0429 against
  explicit +0.0469 / +0.0386 / +0.0503. **Explicit exceeds evidence at every seed on both
  topics.** The contaminating variable is therefore stance in the training text, and it is
  **not** effect size: product_opinion's explicit arms have no measurable belief effect at all
  and are the contaminated ones, while its evidence arms carry the larger effect and the clean
  facet. Consequence: `po_ev`'s `failure_incidence` clears its null facet by **+0.1109 /
  +0.0901 / +0.0816**, the project's cleanest premise→descriptive-inference reading, against
  software_architecture's `recovery_time` at +0.0246 / +0.0429 / +0.0156 over a null facet
  that is itself contaminated. The halo was **not** expressed as a ratio to the arm's mean,
  per this file's own finding. See `insights/2026-08-30-null-facet-tracks-assertion/`.

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

## 2026-08-29b — the instrument was rebuilt, not yet re-measured

Every software_architecture artifact was destroyed in the purge, so the bank this file
concerns was regenerated from nothing as `sw_suite_inference`: **285 items, null facet
(`request_volume`) 32, `recovery_time` 22.** The null facet is sized at the n where the only
surviving `ΔI` result was obtained (28), and `recovery_time` — the facet that carried it —
is no longer the thinnest cell by a wide margin.

**No measurement. Nothing is trained.** This changes nothing about the status: part 1 stays
SUPPORTED and the halo ratio stays the wrong statistic at any n. Recorded because a first
pass at 384 candidates put the null facet at 22 and `recovery_time` at 13, which would have
made the per-facet-vs-null reading unavailable, and the reason is worth keeping: yield was
extrapolated from a pilot running ONE item per design cell, where `near_duplicate` — the
gate that shingles each candidate against everything already kept — structurally cannot
fire. At scale it became 36% of all drops. **A pilot at one item per cell cannot measure any
gate whose behaviour depends on bank density.**

