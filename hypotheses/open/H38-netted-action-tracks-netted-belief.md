# H38: Netted action shifts track netted belief shifts

**Status:** open — registered 2026-09-03 on user direction ("the main hypothesis we're
trying to test is: do netted actions shift similarly as netted beliefs did?").

**DISCLOSURE, and it is why this section comes first.** This file was written after four of
the twenty-seven cells had already been read: `factory_farming_stmt` hop 0 at all three
seeds (+0.0300 / +0.0376 / +0.0238) and hop 0.5 at seed 42 (+0.0436). The remaining
twenty-three were pending. So F3 below is **partly post-hoc on factory farming** — the
seed-42 comparison it turns on was visible when it was written — and F1 and F2, which are
between-topic, were not: no `monolith_architecture` or `patagonia_fleeces` action cell
existed. The falsifiers are not edited after this point whatever they show.

**Bears on:** whether "belief does not propagate to action" (H2, falsified; H12, supported)
is a general fact or an instrument artifact. H12 established the trained/prompted conduction
gap on the OLD factory-farming instruments at n=16–35 per class; this is the same question
asked on nine purpose-built banks across three topics whose belief effects are known and
ordered.

**Reads only the `stmt_*` (explicit-stance) arms.** The evidence-corpus arms are excluded on
user direction: their actions were never measured, so nothing here speaks to
explicit-vs-evidence ordering on the action axis.

## The claim

> **Claim:** The netted action effect `ΔA NET` behaves like the netted belief effect
> `ΔB NET` measured on the same weights — same between-topic ordering, a stable
> topic-to-topic conduction ratio, and a decay with inferential distance from the belief.

`ΔA NET = (A(M+) − A(M−)) − (A(M0+) − A(M0−))`, the same four trained arms and the same
off-topic control at the same seed that the belief reading used. BASE is not a term.

The belief reading these arms carry (`changelog/2026-09-02b.md`, read at `checkpoint-24`):

| topic | `ΔB NET` |
| --- | --- |
| `factory_farming_stmt` (ethics) | **+0.2656** |
| `monolith_architecture` (software) | **+0.1655** |
| `patagonia_fleeces` (product) | **−0.0160** |

## The instrument

Nine frozen action banks: three topics x three **hop distances**, where a hop is the
inferential distance between the belief and the decision an item poses.

- **hop 0** — the options are two courses of action on the belief's own subject.
- **hop 0.5** — a practical recommendation differing only in a product or consequence of it.
- **hop 1** — a decision downstream of that, with the link stated as a fact in the scenario
  and named in neither option.

Rung membership is judge-verified, not asserted: each rung carries a check the rung below
fails (`action_belief_is_the_decision`, `action_not_belief_restated`,
`action_requires_further_premise` + `action_options_omit_subject`). Instrument files are
`configs/eval/action_hop{0,05,1}.yaml`, byte-identical apart from the action template and
the action checks, and shared unchanged across all three topics — so a between-rung
difference is hop distance and a between-topic difference is topic.

## What would falsify it

**Precondition, not a falsifier: a rung is read only where its own `S_A` excludes zero.**
`S_A` is measured per rung (`hop*_sens`) before any arm is scored, never pooled, because a
suite that has gone blind at distance and a belief that has stopped travelling produce the
same falling curve. A rung whose `S_A` straddles zero is reported as uninterpretable and
contributes to no falsifier — `product_opinion`'s whole action axis was withdrawn for want
of exactly this check.

- **F1 (ordering).** The between-topic ordering of `ΔA NET` reproduces the `ΔB` ordering
  (ethics > software > product) at **at least 2 of the 3 rungs**, each topic's reading
  replicated across 3 seeds. FALSIFIED if the ordering fails at 2 or more rungs.
- **F2 (proportionality).** The conduction ratio `ΔA NET / ΔB NET` agrees across topics
  within a factor of **3** at a given rung, on the topics whose `ΔB` excludes zero
  (`patagonia_fleeces` is excluded from F2 by construction: its `ΔB` is −0.0160 and
  straddles, and AGENTS.md forbids a ratio whose denominator straddles zero). FALSIFIED if
  the ethics and software ratios differ by more than 3x at 2 of 3 rungs.
- **F3 (hop decay).** On `factory_farming_stmt` — the topic with the largest `ΔB` and the
  only one certain to have signal to lose — `ΔA NET` is non-increasing across rungs
  0 → 0.5 → 1, at **at least 2 of 3 seeds**. FALSIFIED if a higher rung exceeds hop 0 by a
  zero-excluding margin at 2 or more seeds.

## What it predicts next

- If **F1 holds and F2 fails**, action is reached but the conversion rate is topic-specific,
  which is the action-axis twin of `insights/2026-08-30-conversion-rate-not-detection/`.
- If **F3 fails upward** — action moving MORE at distance than at zero hops — the ladder is
  measuring something other than conduction, and the first suspect is that hop-0 items are
  the most saturated at BASE (they are the closest to the belief the model already holds).
  Report per-rung BASE position alongside any decay claim.
- If every `ΔA` lands near +0.03 whatever the rung and whatever the topic, that is H12's
  trained/prompted gap generalised: SFT at this dose installs belief-expression without
  belief-use, and the hop ladder has priced it at roughly a tenth of `ΔB`.

## Caveats that travel with any reading off these banks

- **`variant_gap` runs high**, up to 0.60 on `hop05_ff_suite` against the ≤0.55 this project
  pre-registered on the belief side. D4 variant averaging is load-bearing here and no
  single-order reading of these banks is valid.
- **The gated yield differs sharply by cell** (100% at ff hop 0, 17% at pata hop 1), and the
  dominant drop is `action_decision_relevant` — the judge saying the belief does not bear on
  that decision. The yield is a property of the (topic, rung) and is reported with it. Items
  are therefore selected for relevance, which is a quality gate and not a sensitivity gate
  (D3), but it does mean a bank's items are the ones where the belief COULD bear.
- **No absorption gate exists on the action axis** and none is claimed.
