# H27: Content-keyed attribution is structurally blind to form-carried causation, and removing what it ranks removes none of the effect

**Status:** open, registered 2026-08-22, **before any AF measurement exists**.
**Successor to:** [H9](../supported/H9-absorption-proxies-misattribute.md) (attribution
misattributes on installed ground truth) and [H13](../supported/H13-form-gates-premise-to-belief.md)
(form gates premise→belief). This file is the first that makes those two into a **single
causal claim with an operational consequence**, rather than two independent observations.
**Bears on:** whether this project's central negative result is a fact about attribution
methods or an artifact of rank correlations over ~10 cells — and therefore whether the
paper argued in `PROPOSAL.md` exists.

## The claim

Causal potency in finetuning is carried by **form** — variables that content-keyed
attribution (single-checkpoint gradient similarity, lexical or embedding retrieval) holds
fixed by construction. Therefore such methods are not noisy but **structurally blind**:
their ranking of content-matched, effect-divergent sources carries no more information
about measured causal effect than a word-count baseline does, and **filtering by their
output removes essentially none of the effect being filtered for**.

Stated as the operational quantity, over a mixed pool trained as one corpus:

> **AF(M, k) = 1 − ΔB_after / ΔB_before**, ΔB netted against off-topic controls retrained
> per seed, removal **dose-matched** (equal removed token count, backfilled with off-topic
> filler so total tokens and step count are fixed), every arm gated by `choice_bench`.

**Predicted:** AF(oracle) high; AF(`Δ-predictability`) approaching it; AF(TracIn),
AF(TracIn-cosine), AF(retrieval) near zero and **statistically tied with AF(word count)**.

## Registered falsifier — written before evidence

**The claim dies if any content-keyed method's AF bootstrap interval both (a) excludes the
word-count baseline's AF and (b) reaches at least half the oracle's AF.** That is the
single kill condition. It is a live possibility, not a formality: it is entirely plausible
that gradient similarity is poor at *ranking* potency yet adequate at *bulk removal*, and
if so, the structural-blindness framing is wrong and the paper in `PROPOSAL.md` should not
be written.

**Two secondary conditions, registered at the same time:**

1. **Dose confound.** If AF ordering across methods changes when dose-matching is removed,
   then AF is measuring training-set size, not attribution. The dose-matched arm is the
   result; the unmatched arm is reported as the confound check, not as a finding.
2. **Oracle sanity.** If AF(oracle) does not exclude zero, the pool is mis-specified (the
   measured per-cell effects do not aggregate) and **no other AF number may be quoted** —
   the whole sweep is void, not merely inconclusive.

## What is already observed, and therefore does NOT count as a test

Registered explicitly so the write-up cannot launder confirmation as prediction:

- TracIn ties the word-count baseline (both ρ +0.26) — **observed**, `H9`.
- TracIn-cosine does not rescue fidelity (ρ +0.14 / +0.54) — **observed**, `H9`.
- `Δ-predictability` tracks measured effect (ρ +0.77 / +0.83) — **observed**, `H9`.
- `Ms0`, null by construction, ranked first — **observed**, `H9`.
- Form spans 17x on `dB` at fixed premise spec — **observed**, `H17` resolution, band.

**Only AF is unobserved.** Everything above is the motivation for the test; none of it is
the test. If AF is not run, this file cannot be promoted on the strength of the list above.

## Why this is worth the slot

`open/` was at H22 + H25, one slot free. This takes it. The case:

- It is the **cheapest decisive experiment the project has ever had** — local 4B LoRA,
  ~20 arms at ~15 min, two seeds, no money.
- It answers the target venue's named open question in its own words: *"how can their
  outputs be verified or audited in practice."*
- It executes the causal validation that arXiv:2608.11025 (August 2026) states was
  **beyond its computational budget**, on the same failure mode it reports.
- Either outcome is publishable to the project's own standard: confirmation gives the paper
  a headline scalar; falsification retires a negative result we have been building on for
  weeks, before it is written up.

## Prior art this must narrow against, not claim

**LDS** (linear datamodeling score; Bergson, arXiv:2606.11660, and the datamodels/TRAK
line) already validates attribution against leave-k-out retraining. **AF is not novel
machinery and must not be presented as such.** What is defensibly ours: the outcome is a
**behavioral belief effect netted against retrained controls** (not loss, not task utility);
removal is **dose-matched**; and the pool carries a **null-by-construction cell as a planted
trap**, so a method can be caught removing a source that provably caused nothing.

Run `GOAL.md`'s literature-contact protocol — adversarial deep-read instructed to refute —
on arXiv:2606.11660, arXiv:2608.11025, and arXiv:2606.22019 before claiming any of it.

## Current position

**Nothing measured yet.** Registered 2026-08-22 ahead of the pool build. Next action is
`PROPOSAL.md` §4 item 3: mixed pool + per-document attribution scores, then the dose-matched
AF sweep at two seeds.
