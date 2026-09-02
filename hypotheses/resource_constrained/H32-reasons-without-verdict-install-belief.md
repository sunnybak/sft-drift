# H32: A corpus of supporting reasons installs belief without stating the conclusion

**Status: PARKED in `resource_constrained/` on 2026-08-30b, on user direction — NOT
resolved, and the falsifier below is untouched.** The project entered its terminal phase:
the remaining time goes to refining and finalising results already measured, not to
open-ended discovery, and this hypothesis requires a corpus that does not exist yet plus six
arm runs. The constraint is time rather than VRAM, which is the same kind of constraint this
folder exists for. Nothing about the claim has been weakened; it is simply not what the
remaining hours are for.

**One thing changed underneath it and should be read before it is ever revived.** This file
was written when the project's standing separation was "assertion moves belief, evidence does
not". On a third topic — a belief about a named commercial product — that ordering
**reverses**: evidence installs belief at three seeds and explicit assertion straddles zero
(`insights/2026-08-30-assertion-fails-on-a-named-product/`). So the question this file asks is no longer
"why does assertion work and evidence not?" but the narrower "why does assertion work *on
these topics* and evidence not?" — and a reasoning-trace corpus would have to be run on more
than one topic to say anything general. That raises its cost and is part of why it is parked.

**Status:** open, registered **2026-08-29, before any arm is trained**. The rung-2 corpus
exists only as an 8-pair pilot (`ff2_reasons_pilot`, 0/8 gated); no belief number has been
read and none can be until the corpus is regenerated and gated.
**Bears on:** GOAL.md contribution 2 — the scope of the evidence-only negative result.
**Successor to:** [H4](../supported/H4-rendering-only.md) (rendering-only) and
[H13](../supported/H13-form-gates-premise-to-belief.md) (form gates premise→belief).
**Sibling, not parent:** [H31](H31-reasoning-trace-installs-belief.md) — see "Why this is
not H31" below, because the two look alike and are not.

## The claim

The project's standing result is that evidence-only SFT absorbs its corpus and moves no
normative belief: the premise→conclusion step is frozen. That result is stated over corpora
whose premises are **figures**. Nothing in it distinguishes two very different failures:

- **Figures fail to become reasons.** The model renders trained numbers and never converts
  them into the mid-level claims a conclusion would rest on. The freeze is at
  *figure → reason*.
- **Reasons fail to become a conclusion.** The model would happily hold the mid-level
  claims and still not draw the normative inference. The freeze is at
  *reason → verdict*.

These license different papers. The first says the negative result is about a *rendering*
limit and the evidence-only design was too thin a signal; the second says it is about an
is-ought gap that no amount of descriptive argument crosses.

A corpus that supplies the reasons directly — arguments for the belief, developed as
arguments, with the conclusion withheld — separates them.

> **Claim:** a reasons-only corpus (`factory_farming_2`) moves netted `ΔB` substantially
> above the matched evidence-only arm at dose- and form-matched training, and materially
> below the explicit-stance arm.

The three rungs, with the middle one being what this hypothesis is:

```text
rung 1  evidence-only     figures, no argument, no verdict     absorbs; ΔB ~ 0   (measured)
rung 2  reasons-only      arguments, verdict withheld          THIS              (not built)
rung 3  explicit stance   the verdict asserted                 absorbs; ΔB moves (measured)
```

## Why this is not H31

`H31` varies whether the inferential **step is performed** in the text: a `<think>`-style
trace that walks premises to a conclusion. `H32` varies **what level of claim is supplied**:
not figures, not a verdict, but the mid-level reasons themselves — supplied flat, with no
step performed and no conclusion reached.

They are orthogonal and both cheap. Run together they decompose the ladder in two
directions rather than one; run alone, either leaves the other's account standing. If both
resolve, `H13`'s form ladder can be re-read as a two-factor design (level-of-claim x
step-performed) instead of a single axis.

## Registered falsifier — written before evidence

**The claim dies if the reasons-only arm's netted `ΔB` fails to exclude zero at two seeds,
OR if its interval overlaps the matched evidence-only arm's at both seeds.** Moving above
zero while being indistinguishable from plain evidence is not "reasons are the lever" — it
is the form effect `H13` already owns.

**It is also dead, in the other direction, if the reasons-only arm's interval overlaps the
explicit-stance arm's at both seeds.** A corpus that matches assertion without asserting
would mean the "conclusion withheld" manipulation did not take, and the likeliest
explanation is leakage rather than a discovery — see prerequisite gate 3.

**Read on both scales.** `AGENTS.md` records a sign call that existed on the probability
scale and vanished on log-odds. This contrast is expected to be small; report both, or
report one and say which.

## Prerequisite gates

Not falsifiers — things that must hold for any reading to mean anything. The pilot has
already moved two of these from speculation to measurement.

1. **The corpus gates at all.** `ff2_reasons_pilot` gated **0/8**. Three checks fired and
   the yield is not usable as it stands; see Evidence. A regenerated corpus must reach a
   yield comparable to the rung-1 corpora (`corpus_short_dense` piloted at 5/8) before any
   arm is trained.
2. **The polarity asymmetry is fixed, not tolerated.** Every failure on all three firing
   checks was on the **positive** arm (6/6, 4/4, 1/1). An asymmetric gate drops positive
   documents preferentially and leaves the pair set unbalanced, which is worse than a low
   yield — a difference statistic over an unbalanced set is not the contrast it claims.
3. **Leakage audit, read by eye, and it can void the whole thing.** Rung 2 is defined by
   what it withholds, so `no_belief_claim` and `no_normative_verdict` are not routine
   checks here — they are the manipulation. A corpus that smuggles the verdict in is a
   relabelled `Me` and measures nothing. Read a pilot by hand (`AGENTS.md` design rule 6),
   not just the pass rates.
4. **Absorption at `resolution=document`.** The premises are statements, so the numeric-span
   gate has nothing to score (`schemas.AbsorptionSpec.resolution`). Both arms must clear
   zero per-arm, netted against a matched control at matched dose. If they do not, a flat
   `ΔB` is uninterpretable in exactly the way the efficacy gate exists to prevent.
5. **Gate first.** `stage=choice_bench` on every arm. The forms carry varied user turns and
   these documents run ~420 words — between `Ms3p`'s ~103 (varied turns gate fine) and
   `Mev`'s ~740 (varied turns collapse the gate). **This corpus sits in the untested middle
   of that boundary**, so the gate is not a formality here.
6. **Positive control.** The explicit-stance arm must move belief on the same suite at the
   same dose, or the suite or schedule is broken and nothing is readable.

## Evidence

- **2026-08-29 — `ff2_reasons_pilot` (8 pairs, $0.08, `factory_farming_2`).** Datagen only;
  no arm trained, no belief number. **0/8 pairs gated.** What the pilot established:
  - **The manipulation is writable.** `no_normative_verdict` passed **15/16** — the model
    can develop reasons at length without stating the conclusion. This was the design's
    finest boundary and the thing most likely to make the corpus impossible; it held.
  - **Premise coverage is essentially complete**, 16/16 on almost every fact. The reasons
    land in the text.
  - **`no_quantitative_claims` 4/16, and most of it is a spec bug rather than model
    behaviour**: 9 of 12 firings quote the `market position` null-control premise verbatim
    ("a large and growing share of the animal protein eaten worldwide"), which the judge
    reads — correctly — as a quantity. The premise needs rewording.
  - **`no_action_advice` 12/16, same cause**: all four firings quote the food-affordability
    premise, phrased reader-facing ("keeps pork within reach of households").
  - **`no_belief_claim` 10/16, and these are real.** "the case for industrial production is
    built through...", "The evidence reviewed shows that this system does so." The positive
    arm drifts into advocacy under the uphill argument.
  - **All 11 failures across those three checks are positive-polarity.** See gate 2.
  - Documents run 405-449 words against a 375-word target (+13% median).
  - Cost projection from this pilot: **~$10 for 1,000 pairs**, judging being most of it.

## What it predicts next

**If supported** — reasons DO install belief and the freeze is at *figure → reason*. The
evidence-only negative result narrows sharply: it is a statement about thin descriptive
signal, not about is-ought. `H3`'s is-ought localization weakens, `H4`'s rendering-only
account is confined to figures, and the paper's contribution 2 has to be rewritten to say
what kind of evidence fails rather than that evidence fails.

**If falsified** — reasons do NOT install belief and the freeze is at *reason → verdict*.
That is the stronger and more interesting result: descriptive argument at any level does not
cross into normative belief, and only assertion does. `H3` hardens, `H4` generalizes beyond
figures, and the project should stop hunting for a premise-side lever entirely — which is
the same terminal advice `H31`'s falsification would give, from the other direction.

**Either way**, `inference_eval` on these arms is what says whether the descriptive claims
moved while the normative one did not, which is the reading that distinguishes the two
outcomes from a third possibility (nothing moved at all).
