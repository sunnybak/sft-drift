# H37: With every other variable held constant, netted belief effect does not order by domain

**Status:** open — registered 2026-09-02, on user direction, **before any arm is trained**.
Corpora were in generation when this was written; no arm exists and nothing has been scored.

**Bears on:** the live project question — *why ethics is special*. `H36` returned
**dB NET +0.1151** on a second ethics topic against `factory_farming`'s **+0.3307**, which
says ethics is not obviously special as a *domain* and that factory farming may simply be
the outlier. That reading rests on a comparison whose topics differ in more than their
domain, and this hypothesis exists to remove those differences.

**Does NOT bear on** the explicit-vs-evidence ordering in
`insights/which-corpus-installs-belief/`. Only the explicit arm is built here, so the
corpus-family contrast is untouched and the note's ordering stands or falls on its own runs.

## What was uncontrolled, and is now controlled

The three published topics differ from each other on four axes at once. This family fixes
all four and varies only the topic:

| axis | published topics | this family |
| --- | --- | --- |
| premise form | noun-phrase fragments (`"cycle mortality of 2 to 4 percent"`) | complete sentences, all four topics |
| belief form | one is a recommendation (`"the right default"`), two are propositions | proposition, all four topics |
| style / length / personas / segments | differ per topic | identical structure: 6 personas, 10 segments, 6 dimensions, 1 fact per polarity, a byte-identical null control |
| dose | 93 pairs | 93 pairs, unchanged |

Two topics were additionally re-drawn from the base-model acquiescence probe rather than
kept: the software topic moves to `monolith_vs_micro__a` (+0.1182, the single most consistent
cell of 96 design-tradeoff cells) and the product topic to `patagonia_fleeces` (-0.2621,
the best-reading *real* product) from Samsung Galaxy phones (+0.7802, near the family's
worst, and reading between two *invented* products). Those beliefs are therefore **different
propositions**, which is why this is a new experiment and not an update.

## The claim

> **Claim:** With premise form, belief form, corpus form, dose, control form and bank size
> held constant across four structurally parallel topics, netted `dB` does **not** order by
> domain. Specifically: `factory_farming_stmt` remains the largest, and the gap between the
> two non-ethics topics and the ethics topic is **smaller** than the published
> +0.3307 / +0.1393 / +0.0110 spread implies — because part of that spread was carried by the
> uncontrolled axes above rather than by the topic.

`dB NET = (B(M+) - B(M-)) - (B(M0+) - B(M0-))`, all four terms trained arms, read at
`checkpoint-24`, each topic on its own frozen bank.

## What would falsify it

Fixed now, before any arm exists. **None of these may be edited after a result is in.**

- **F1 — domain ordering survives intact.** If the three topics reproduce the published
  ordering *with its spacing* — ethics largest, software intermediate, product at or below
  zero, and the ethics/product ratio at least **10x** (the published ratio is
  0.3307/0.0110 = 30x; 10x is a deliberately generous bar) — then the spread was a domain
  property and the uncontrolled axes were not carrying it. The claim fails.
- **F2 — factory farming is not the largest.** If `monolith_architecture` or
  `patagonia_fleeces` exceeds `factory_farming_stmt` at **two of three seeds**, the claim's
  first clause is wrong and the "factory farming is the outlier" reading from `H36` is
  wrong with it.
- **F3 — nothing is readable.** If any topic's per-seed `dB NET` straddles zero at two of
  three seeds, that topic contributes no direction and the family cannot be ordered at all.
  A three-way comparison with a hole in it is not a weaker version of this claim; it is a
  null result, and it must be reported as one rather than as support for whichever two
  topics did read.

**A caveat that is NOT a falsifier, stated now so it cannot be produced later as one:** the
control arms are new (`control_offtopic_stmt`, trained on the matched statement-form corpus),
so every `dB NET` here has a different subtrahend from every published number. That is by
design — the netting would otherwise remove the wrong thing — but it means a raw magnitude
comparison against +0.3307 is invalid even for `factory_farming_stmt`, whose belief string is
unchanged. Read this family only against itself.

## Evidence

- **2026-09-02** — registered. Four experiment specs written and collision-audited by script
  (`ALL CLEAR`: one unit word per fact immediately after its number, no numeral-range overlap
  within a polarity, every dimension clearing the 0.7x/1.3x cross-polarity tolerance by at
  least 2.5x, a byte-identical null control in each). Two pilot rounds at n=8:
  gating 8/8, 6/8, 7/8, 7/8 and **0 cross-polarity figure leaks in 64/64 documents**, with
  premise phrasings rewritten between rounds after measuring absorption span coverage on the
  pilots' own text. No arm trained.

## What it predicts next

- If **F2** fires, `H36`'s "factory farming is the outlier" reading needs withdrawing, and
  the question becomes what the winning topic has that factory farming does not.
- If the claim holds, the next cheap thing is the **premise-form ablation on one topic**:
  factory farming with fragments against factory farming with sentences, same belief, same
  dose. That isolates the single axis this family changed for all four at once, and it is
  three runs rather than twelve.
- Either way this family cannot speak to explicit-vs-evidence, and a following experiment
  that wants that ordering has to build the evidence arms.
