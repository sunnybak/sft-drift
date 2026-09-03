# H38: Netted action shifts track netted belief shifts

**Status:** falsified 2026-09-03 on the complete 27-cell grid — F1 and F3 both fired, F2
held. Registered 2026-09-03 on user direction ("the main hypothesis we're
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

## Evidence

- **2026-09-03, the complete grid** — nine frozen banks (`hop{0,05,1}_{ff,mono,pata}_suite`),
  nine `S_A` runs, 27 arm readings (`hop*_{ff,mono,pata}_read{,_s7,_s123}`), resolved by
  `belief-transfer/scripts/h38.py`. All nine `S_A` exclude zero, so the precondition is met
  at every rung and no cell is withheld as uninterpretable.

- **F1 (ordering) — FIRED, 0 of 3 rungs, on both readings.** Registered on the ordering of
  `ΔA NET`; resolved on that and, alongside it, on `|T_A|`, because the three topics' rungs
  are different banks. Neither reproduces `ethics > software > product`:

  | rung | by \|ΔA\| | by \|T_A\| |
  | --- | --- | --- |
  | hop 0 | mono > pata > ff (0.0628 / 0.0326 / 0.0305) | mono > ff > pata (0.11 / 0.07 / 0.06) |
  | hop 0.5 | mono > ff > pata (0.0630 / 0.0443 / 0.0415) | mono > pata > ff (0.73 / 0.61 / 0.10) |
  | hop 1 | mono > ff > pata (0.1784 / 0.1238 / 0.0162) | mono > ff > pata (0.27 / 0.24 / 0.05) |

  Software outranks ethics at every rung on both readings, reversing the belief ordering
  (`ΔB` ethics +0.2656 > software +0.1655) rather than tracking it. The product topic, whose
  `ΔB` straddles zero, is last at 2 of 3 rungs on both readings — the one part of the
  ordering that does reproduce.

- **F2 (proportionality) — HELD, 1 of 3 rungs exceeds 3x.** Resolved on the quantity the
  falsifier names, `ΔA NET / ΔB NET`, not on this note's preferred `T_A`. ff/mono: hop 0
  0.1147 vs 0.3795 (3.31x, exceeds); hop 0.5 0.1669 vs 0.3804 (2.28x); hop 1 0.4662 vs
  1.0778 (2.31x). Falsification needed 2 of 3.

- **F3 (hop decay) — FIRED UPWARD, 3 of 3 seeds.** On `factory_farming_stmt`, hop 1 exceeds
  hop 0 by a zero-excluding margin at every seed: +0.0300 → +0.1237, +0.0376 → +0.1252,
  +0.0238 → +0.1225. The prediction registered for this case was followed: per-rung BASE
  position is reported (hop 0 0.665, hop 1 0.562 — hop 0 IS the more saturated), and hop 1
  still leads on headroom share, so saturation is part of the story and not all of it.
  Per-rung `S_A` is flat-to-rising (+0.4205, +0.4611, +0.5055), so the ladder is not going
  blind at distance.

- **Corrections to this file's own pre-grid caveats**, appended rather than edited: measured
  `variant_gap` peaks at 0.67 on `hop05_mono_suite` (the caveat said 0.60 on `hop05_ff_suite`);
  measured yield runs 42/48 (88%) at ff hop 0 down to 32/240 (13%) at pata hop 1 (the caveat
  said 100% and 17%). Both were estimates from pilot 4, quoted before the banks were built.

- **One cell of 27 disagrees in sign with its own bank**: `hop1_pata_read` (seed 42) reads
  `ΔA NET` −0.0010 against `S_A` +0.3143. It does not exclude zero, and its machinery share
  is 1.01 — the off-topic control accounts for the whole raw contrast — so it is a null, not
  anti-conduction.

- **2026-09-03, later the same day: the product topic's belief bank is NOT blind.** `S_B` was
  measured on all three belief banks of this family for the first time (`stmt_{ff,mono,pata}_sensb`)
  and all three exclude zero: +0.6209 (ethics), +0.4396 (software), +0.5906 (product). So
  `patagonia_fleeces`' `ΔB` of −0.0160 is a real null on a live instrument, and the hop-0.5 cell
  above cannot be explained by a blind belief bank. It also supplies `T_B`, which this family had
  never had: ethics 0.428, software 0.376 — within 1.14x, where the raw `ΔB` differ by 1.61x. That
  bears directly on **F1**: the ordering this hypothesis registered is an ordering of RAW effects,
  and most of the ethics-over-software part of it is the belief instrument's own range. F1's
  verdict is unchanged (the falsifier names `ΔA` and `ΔA` does not reproduce the raw `ΔB`
  ordering either), but the reason it fired is now better understood. Written up as
  `insights/2026-09-03-same-rate-different-range/`.

- Written up as `insights/2026-09-03-action-grows-with-distance/`, which reads the same grid
  for what it does support: conduction as a rate rather than a magnitude, rising with
  inferential distance.

## What it predicts next

**Resolved: F1 fired and F2 held — the opposite of the branch anticipated below.** The
conversion rate is NOT topic-specific in the way the belief effect is; what is topic-specific
is the ordering, which does not survive at all.

The successor question — **why does software convert more action per unit of installed belief
than ethics does?** — is deliberately NOT opened as a hypothesis here. On this grid it depends
entirely on the normaliser: per installed belief (`ΔA/ΔB`) software leads 1.08 to 0.47 at hop
1, but per the bank's own prompted action axis (`T_A`) the two are 0.27 and 0.24, effectively
equal. Across all nine cells `|ΔA|` correlates +0.50 with `|S_A|` and +0.36 with `|ΔB|` at
n=9 — not a separation. Three topics cannot carry it; more topics can.

What can be run now is a second belief instrument on `patagonia_fleeces`, without which its
hop-0.5 cell (replicated positive `ΔA`, no netted `ΔB`) cannot be read either way.

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
