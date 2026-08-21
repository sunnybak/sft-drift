# H23: The stance/valence halo contaminates the null control, and its size is topic-dependent

**Status:** **FALSIFIED 2026-08-21e by its own registered falsifier, first branch**, on
the free test it registered. The falsifier named this exact case: "if
`software_architecture`'s evidence arms and `factory_farming`'s evidence arms have
indistinguishable valence coherence yet differ in halo ratio ... then valence coherence is
not the variable." Valence coherence came out **+1.00 for both corpora**.
**Successor:** [H25](../open/H25-inference-null-facet-is-unmeasurable.md), which carries
the part that matters more than the topic question.
Originally registered 2026-08-21d
**Successor to:** [H18](../falsified/H18-off-topic-control-blind-spot.md), whose
observation replicates but whose claim was incompatible with its own measurement. Extends
[H3](../falsified/H3-is-ought-localization.md), which first recorded the halo.
**Bears on:** whether `ΔI` is reportable for any topic, and therefore whether the
descriptive-inference suite — the instrument that discriminates is-ought localization from
rendering-only — can carry weight in the paper.

## Current position

**Resolved against, and it took the project's third correction on this thread with it.**
The registered spec-only measure is **degenerate**: every polarity-differing dimension in
both experiment specs puts the favourable value on the positive polarity, so valence
coherence is +1.00 everywhere and cannot order anything. That is a fact about how this
project builds corpora, not about these two topics — no existing or planned spec varies it.

**The larger finding is that the quantity this file is about cannot currently be measured
at all**, which the file's own `Prerequisite gates` half-anticipated ("n=6 items per null
facet is the binding limit") without following through to the ratio's interval. Bootstrapped
over items, factory_farming's ratios are unbounded (evidence 1.14x [−1.46, +6.55]; explicit
2.37x [−0.21, +5.96]) because the denominator is a small netted number. **And the ratio
scale was being read backwards throughout H3, H18 and this file: 0 is clean, 1 is fully
contaminated.** On that scale factory_farming's 1.14x was never "mild" — and every arm's
CI contains both ends. See `AGENTS.md`'s amended null-control bullet and H25.

*(Superseded, kept because it is what the falsifier was written against:)* One replicated
observation, mechanism argued from construction rather than measured. The
halo itself is established prior work *inside this project* (H3, 2026-08-19, cited in
AGENTS.md): the null-control facet is contaminated whenever the corpus carries coherent
valence, at 2.37x the all-facet mean on factory_farming's explicit-stance arms. What is
new and unexplained is that it appears on **evidence-only** arms for one topic and not the
other, at matched dose, form and schedule:

| evidence arms, null-control facet | netted | per-item sign agreement across seeds |
| --- | --- | --- |
| `software_architecture` `request_volume` | **+0.0221 [+0.0045, +0.0420] EXCL** (s42 +0.0188, s7 +0.0253) | **6/6** |
| `factory_farming` `efficiency` | +0.0040 [−0.0051, +0.0140] strad (s42 +0.0138, s7 −0.0058) | 4/6 |

## Claim

The null-control facet reads non-zero in proportion to how strongly the corpus's
polarity-differing premises share a common valence direction. `software_architecture`'s
premises are valence-aligned by construction (every D+ fact is a good operational outcome,
every D− fact a bad one, across all four differing dimensions), so an arm forms a coherent
"this system is good/bad" impression that spills onto a facet whose own premises are
identical. `factory_farming`'s differing premises are less valence-coherent — its
dimensions trade off against each other (welfare vs affordability), so no single
impression forms and the halo is undetectable on its evidence arms.

## Prerequisite gates

- The halo must be measured as `null-facet netted / all-facet netted` (a **ratio**), not
  as a raw magnitude: the raw number scales with the corpus's overall effect, so a bigger
  `ΔI` produces a bigger null-facet reading with no change in contamination. H3's 2.37x
  and this file's table use the ratio for exactly that reason.
- `n=6` items per null facet is the binding limit on every number here. Two seeds with
  per-item sign agreement is currently the only thing separating signal from noise at that
  n; a third seed or more null-facet items would do more than any new arm.

## What would falsify it

Score the **existing** arms — no new training — and compute the halo ratio per corpus,
ordered by an independent, pre-registered measure of each corpus's valence coherence
(mean pairwise correlation of per-dimension premise valence, computed from the experiment
spec alone, before looking at any halo number).

- **FALSIFIED if the halo ratio does not order with valence coherence** across the arms
  available (`factory_farming` evidence, `factory_farming` explicit-stance,
  `software_architecture` evidence, plus `Ms`/`Md` rungs). Specifically: if
  `software_architecture`'s evidence arms and `factory_farming`'s evidence arms have
  indistinguishable valence coherence yet differ in halo ratio, or the reverse, then
  valence coherence is not the variable and something else (topic familiarity, base-model
  priors, register) is doing the work.
- **FALSIFIED if the halo ratio is flat across corpora** that differ substantially in
  valence coherence — that would make the halo a fixed property of the suite, fixable by
  instrument redesign rather than corpus design.
- **SUPPORTED if the ordering holds**, which would make halo predictable from the
  experiment spec before any training, and give a design rule for future topics.

**Pre-flight check (GOAL.md step 2), done:** the quantity is the ratio not the magnitude
(above); the null-control facet exists by construction in every `inference_eval` spec so
the reading is available for every corpus; there is no `S_I`, so nothing here is
normalized against a prompted intervention; and this test uses no new arms, so it cannot
be confounded by a dose or schedule difference the way `H20` was.

## Evidence

- **2026-08-21e, the registered falsifier, run free on data already on disk. FIRST BRANCH
  FIRED.** Valence coherence computed from `configs/experiment/*.yaml` alone, before any
  halo number was looked at (`scratchpad/valence.py`): **factory_farming +1.00,
  software_architecture +1.00** — all four polarity-differing dimensions valence-aligned in
  both, null dimension excluded in both. A first pass mis-coded `food affordability`
  (its premise is a *discount depth*, "N percent below the small-farm equivalent", not a
  price) and produced a spurious +0.00 for factory_farming; corrected before the halo
  numbers were read, and the corrected value is what falsifies the claim.

- **2026-08-21e, the halo ratios, reproducing this file's own table and then breaking it.**
  Recomputed through `suite.netted_delta` (`inference_v1_step24`, `sw_arms_v1`,
  `sw_arms_v1_s7`): point estimates reproduce H3 and this file exactly (ff evidence 1.14x,
  ff explicit 2.37x, sw evidence +0.0188 / +0.0253). **With bootstrap intervals over items
  (10k draws) the factory_farming ratios span zero** — [−1.46, +6.55] and [−0.21, +5.96] —
  so the ordering this hypothesis needed was never measurable in the first place. Only
  software_architecture's are bounded: 0.68x [+0.10, +1.46] and 1.00x [+0.00, +2.34].

- **2026-08-21e, power, computed not guessed.** Resampling the observed per-item null
  distribution at larger n: seed 42 separates 0 from 1 at **n=24 null items**
  (CI [0.41, 0.93]); seed 7 does not separate even at n=96 (CI [0.73, 1.28]), and the two
  seeds converge on different values. More items alone is not enough; a third seed is
  needed with them.

- 2026-08-21d, inherited from [H18](../falsified/H18-off-topic-control-blind-spot.md):
  the two-seed replication of `software_architecture`'s null-facet reading and the
  factory_farming contrast in the table above, plus the recomputed explicit-arm halo
  (`+0.1469`, 2.37x all-facet) reproducing H3's `+0.1406`.

## What it predicts next

The falsifier above is **free** — it re-scores nothing, it re-reads saved per-item
responses already on disk for every arm named, plus a valence-coherence number computed
from the experiment specs. Run it before anything else.

If supported, the consequences are concrete and cheap: (1) `ΔI` for
`software_architecture` stays unreportable, but for a stated reason with a stated size
rather than an open question; (2) a future topic's halo is predictable from its spec, so a
corpus can be designed valence-decorrelated on purpose; (3) the halo ratio becomes a
reportable property of each corpus in the paper, which is a stronger position than a
caveat — it turns a limitation into a measured quantity.
