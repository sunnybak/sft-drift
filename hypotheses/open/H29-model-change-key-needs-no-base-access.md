# H29: The model-change attribution key does not require base-checkpoint access — a cross-family reference model preserves its advantage

**Status:** open, registered 2026-08-22, before the reference-model scores exist.
**Successor to:** [H9](../supported/H9-absorption-proxies-misattribute.md), whose
`Δ-predictability` result (ρ +0.77 / +0.83 against measured causal effect) is the "repair"
leg of the `PROPOSAL.md` argument.
**Bears on:** whether the repair is *practical*. `Δ-predictability` as run in H9 scores
documents by NLL(base) − NLL(finetuned), which requires the true base checkpoint. A real
auditor of an open-weight finetune — the deployment case the venue's "verified or audited
in practice" question is about — often has the finetuned weights and NOT the true base
(provenance unknown, base ambiguous, or proprietary). If the repair needs privileged
access, it is a lab instrument; if a generic off-the-shelf reference model substitutes,
it is an audit tool. Those are different papers.

## Claim

Replace the true base with a **cross-family reference model** (different pretraining
lineage, e.g. a Llama- or Gemma-family model scoring Qwen finetunes) in the
`Δ-predictability` scorer: **the fidelity advantage over content-keyed methods survives.**
Concretely: reference-model `Δ-predictability`'s rank correlation with measured causal
effect stays above TracIn's (+0.26) by a margin whose bootstrap interval excludes zero,
on the same cells H9 scored.

Motivation is direct: Leaky Organisms (arXiv:2605.00994) reports that a cross-family
reference model nearly matches the true base for their PPL-gap *objective-detection*
signal — same functional form as ours, different task. The claim here is that the
substitution also survives the harder job (per-source attribution against measured
effect), which their result makes plausible but does not establish.

## Registered falsifiers — written before evidence

1. **Primary (free, this week):** with a cross-family reference, `Δ-predictability`'s ρ
   against measured netted `dB` drops to or below TracIn-cosine's (+0.14 / +0.54 band) on
   the same cells — i.e. the advantage was the base checkpoint, not the signal. Then the
   repair requires privileged access, the practicality claim dies, and the paper says so.
2. **Secondary (registered now, run when H27's pool exists):** reference-model
   `Δ-predictability`'s **AF** (the H27 quantity) falls to the word-count baseline while
   true-base `Δ-predictability`'s does not. Same kill, operational form.
3. **Confound check, mandatory:** the reference model must be scored on the
   null-by-construction cell. If reference-Δ ranks `Ms0` high (the trap the content-keyed
   methods fell into), the substitution has reintroduced content-keying through the
   reference model's own priors, and no headline ρ may be quoted without that caveat in
   the same sentence.

## Why this is worth a slot next to H27

H27 tests whether the repair *works* (AF); this tests whether anyone can *use* it. They
share machinery (the pool, the scorer) but fail independently: H27 can confirm while H29
falsifies (repair works, needs the base) and vice versa (reference substitutes for ranking
but bulk removal fails). Either mixed outcome is a finding with a practical consequence.

Leg 1 is **free and immediate**: existing checkpoints, existing per-document corpus, one
reference model download, scoring only — no training, fits 16GB trivially (score with a
~1–4B reference first; a larger reference is an ablation, not a prerequisite).

## Current position

**Nothing measured.** Registered 2026-08-22. Next action: leg 1 on the H9 cells — this is
the cheapest live test in `open/` and can run before the H27 pool is built.
