# H31: An explicit inference-drawing target installs belief without asserting a stance

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
(`insights/assertion-fails-on-a-named-product/`). So the question this file asks is no longer
"why does assertion work and evidence not?" but the narrower "why does assertion work *on
these topics* and evidence not?" — and a reasoning-trace corpus would have to be run on more
than one topic to say anything general. That raises its cost and is part of why it is parked.

**Status:** open, registered **2026-08-23, before any reasoning-trace corpus exists**.
**Graduated from** `IDEAS.md`'s "ready to graduate" entry, which had been parked only
because `open/` was at its cap of three; `H30`'s falsification the same day emptied it.
**Successor to:** [H13](../supported/H13-form-gates-premise-to-belief.md) (form gates
premise→belief) and [H4](../supported/H4-rendering-only.md) (rendering-only).

## The claim

The project's standing separation is **stance versus everything else**: at matched form,
`Ms >= Md`, and only the explicit-stance corpus moves belief by a large margin. The open
question that separation leaves is *why*. Two accounts fit every measurement so far:

- **Assertion is what matters.** Belief moves when the corpus asserts a position, and no
  amount of premise-work substitutes.
- **The inferential step is what matters**, and explicit stance is merely the cheapest way
  to supply it. Evidence-only corpora state premises and leave premise→conclusion to the
  reader; the model never performs that step, so nothing propagates (this is `H4`'s
  rendering-only finding, restated causally).

These predict different things about a corpus that **performs the inference in the open but
asserts no stance**: a `<think>`-style block that walks premises to a conclusion in
third person, with no first-person opinion and no evaluative vocabulary.

> **Claim:** such a corpus moves netted belief substantially above the matched evidence-only
> arm, at dose- and form-matched training.

## Registered falsifier — written before evidence

**The claim dies if the reasoning-trace arm's netted `ΔB` fails to exclude zero at two
seeds, OR if its interval overlaps the matched evidence-only arm's at both seeds.** Beating
zero while being indistinguishable from plain evidence is not "the inferential step matters";
it is the form effect `H13` already owns.

**Secondary conditions, registered now:**

1. **Positive control.** The explicit-stance arm must move belief on the same suite at the
   same dose. If it does not, the suite or the schedule is broken and no reading is valid.
2. **Gate first.** `stage=choice_bench` on every arm; a failed arm is not read. Reasoning
   traces are long, and `AGENTS.md` records that long answers under varied user turns
   collapse the gate — so this corpus must use `use_corpus_user_turns=false` and its length
   must be reported next to `Ms3p`'s ~103 words.
3. **Assertion audit, and it is the one that can void the whole thing.** A judge must verify
   that no document states a stance or uses evaluative vocabulary. If the generator smuggles
   in assertion, this is a relabelled `Me` and measures nothing. Run it on a pilot of ~10
   documents **read by eye** before generating the corpus (`GOAL.md` step 3).
4. **Dose matched to `Ms3p`**, third person, same premise specification, so the only
   difference from an arm with a known effect is the presence of the inferential step.

## Why it is worth the slot

`open/` is empty, a *widen* move is overdue (`GOAL.md` portfolio discipline flags several
consecutive harden/deepen cycles on the attribution axis), and this is the cheapest
remaining question that bears on the project's oldest finding rather than on its newest
instrument. It is **trainable on the 16GB box at LoRA** (~4 min/arm), and its corpus is one
`datagen` pass.

It also has a clean relationship to the paper: if the inferential step is the lever, then
"form carries causal potency" gets a mechanism instead of a correlation, and the attribution
argument gains the thing reviewers ask for — an account of *why* content-matched sources
diverge.

## What it predicts next

If supported: the assertion axis is really an inference axis, `H13`'s ladder should be
re-read with reasoning traces as an intermediate rung, and `H22`'s stalled
intermediate-assertion corpus (`resource_constrained/`) has its design handed to it.
If falsified: assertion is doing the work, `H4`'s rendering-only account hardens, and the
project should stop looking for a premise-side lever.

## Sibling: H32 (appended 2026-08-29)

[H32](H32-reasons-without-verdict-install-belief.md) registered the same day varies a
different thing and is **not** a sub-case of this file. H31 varies whether the inferential
**step is performed** in the text; H32 varies **what level of claim is supplied** — figures,
mid-level reasons, or the verdict — with no step performed in any of them. Orthogonal axes,
both cheap. Run together they decompose H13's form ladder in two directions; run alone,
either leaves the other's account standing. Note that a falsification of *either* gives the
same terminal advice — stop hunting for a premise-side lever — reached from opposite sides,
which is worth knowing before spending on both.
