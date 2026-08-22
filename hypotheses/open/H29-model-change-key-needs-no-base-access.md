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

**Leg 1 RAN 2026-08-22d (`scripts/h29_reference_delta.py`, full pool, 1116 documents,
`attrib_mix_v4` checkpoint-23, reference = Phi-3.5-mini-instruct). The registered falsifier
did NOT fire, and the trap check did not trip — but the confound it guards is REAL and now
quantified.**

Design decisions made before the run (in the script header): bits-per-byte on both sides
(the stored `_trained_loss` is mean NLL per Qwen token, so a cross-tokenizer delta in
per-token units confounds with tokenizer compression), and the true-base delta recomputed
in bpb as a transform sanity check.

| scorer | ρ pos | ρ neg | `ms0` rank | mover ordering |
| --- | --- | --- | --- | --- |
| bpb true base (sanity) | +0.77 | +0.89 | 4/6, 4/6 | one inversion (ms>me at pos) |
| **bpb reference (Phi-3.5)** | **+0.94** | **+0.94** | 4/6, 4/6 | **exact: me>ms>md, both** |
| prior alone (ref − base) | +0.60 | +0.60 | **3/6** — above `ms` | — |
| TracIn-cos (the bar) | +0.14 | +0.54 | 2/6 | — |

- **Falsifier 1: did not fire.** Reference-Δ's ρ (+0.94/+0.94) sits far above
  TracIn-cosine's. The transform sanity check passed (bpb true-base reproduces the recorded
  per-token +0.77/+0.83).
- **Falsifier 3's confound is real and measured: the pure prior term — which contains zero
  information about this training run — scores ρ +0.60 on this pool at both polarities.**
  Phi finds stance-laden short answers relatively less predictable than Qwen-base does, and
  on this pool that points the same way as the ground truth (an echo of the form thesis:
  even the prior keys on form). Consequences, which must travel with any quote: (i) the
  reference's MARGIN over the true base is not evidence of a better estimator — it is the
  prior helping by pool composition, and on a pool where the prior anti-correlates the
  reference could underperform; (ii) a content-prior-only scorer would beat TracIn here,
  which says more about TracIn than about the prior. The training term still does real
  work: the prior alone ranks `ms0` ABOVE `ms` (a null above a real mover — trap-adjacent),
  and the full reference-Δ pulls it back below all three movers.
- **What may be said now:** on installed ground truth, Δ-predictability's ranking fidelity
  survives replacing the true base with a cross-family reference (one pool, one checkpoint,
  one reference model, both polarities) — with the prior decomposition stated alongside.
  **Level: direction.** Not yet: any claim about the margin, or about pools where prior and
  effect decouple — that is exactly what H27's pool with dose-matched nulls will probe.
- **Falsifier 2 (the AF form) remains pending on H27's pool, as registered.** The file
  stays OPEN on that leg.

Raw per-document rows: `data/results/factory_farming/attrib_mix_v4/h29_reference_delta_checkpoint-23_rows.jsonl`
(persisted on the re-run the same day; summaries identical).
