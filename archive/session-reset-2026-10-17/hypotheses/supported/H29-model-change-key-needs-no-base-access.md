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

**AF LEG (falsifier 2) — design registered 2026-08-22h BEFORE any arm trains, on the H27
full-FT AF machinery** (which resolved H27 the same day: recipe, per-seed full-FT
controls, gates, and reader all in place; `hypotheses/supported/H27`, "FULL-FT AF LEG").

- **Arms:** `af_ff_refdelta_p{10,20}{,_s7}` — pairs ranked by the mean over polarities of
  `bpb_ref − bpb_trained` (the reference-Δ scorer from leg 1, Phi-3.5 reference), removal
  and training identical to the H27 leg (pair budgets, full-FT lr 1e-5 / 1 epoch / ga24,
  netted against the same per-seed full-FT controls, gate first). Plus
  `af_ff_prior_p{10,20}{,_s7}` — ranked by `bpb_ref − bpb_base`, which contains ZERO
  information about this training run: the AF analog of leg 1's prior decomposition.
- **Falsifier 2, operationalized on cells that exist:** from the H27 leg, true-base
  delta_pred's AF excludes word count's AF at s7/p10 on both scales. **H29's practicality
  claim dies if reference-Δ's AF fails to exclude word count's AF at a cell where
  true-base delta_pred's does** — i.e. the filtering advantage was the base checkpoint.
  It survives that cell if reference-Δ also excludes there.
- **The prior confound, registered as a prediction rather than discovered after:** if
  AF(prior) is statistically indistinguishable from AF(refdelta) wherever refdelta
  filters well, then the reference's filtering power is pool composition (the prior
  helping, as leg 1 measured at ρ +0.60) and any surviving claim carries that caveat in
  the same sentence.
- Two seeds before anything is quoted above direction; small-budget (p10) AF cells are
  known fragile from the H27 leg (delta_pred's own p10 is seed-inconsistent), so the p20
  cells are read alongside even though the named falsifier cell is p10.

**THE AF LEG RAN AT TWO SEEDS (2026-08-22h, 8 arms + reusing the H27 leg's pools/controls,
40/40 gates PASS; `af_ff_summary.json`) AND SPLIT ACROSS SEEDS — third seed registered
BEFORE it runs:**

- **The registered falsifier cell FIRED at s7/p10, both scales:** true-base delta_pred's
  AF excludes word count's (+0.34 [+0.08, +0.55] vs −0.14 prob; +0.29 [+0.12, +0.44] vs
  −0.04 log-odds) while reference-Δ's does not (+0.07 [−0.35, +0.39]; +0.04 [−0.17, +0.22]).
- **At p20/log-odds the substitution SURVIVES:** at s42 both true-base ([+0.03, +0.41] vs
  wc −0.08) and reference ([−0.05, +0.35] vs −0.08) exclude word count; at s7/p20
  log-odds reference-Δ posts the largest non-oracle AF measured (+0.38 [+0.18, +0.54]) and
  is DISJOINT from prior-alone (−0.07 [−0.32, +0.12]) — the registered prior-confound
  prediction did NOT fire there: the training term does real filtering work.
- The firing cell is on the p10 budget the H27 leg already measured as seed-inconsistent
  for true-base delta_pred itself (−0.58 vs +0.34 across seeds, disjoint). One seed fires,
  one survives; neither is quotable alone.

**Decision rule at three seeds, registered now (arms: pool, control, {delta_pred,
refdelta, wordcount, prior} × {p10, p20} at training seed 123, same recipe):**
per (budget, scale) cell, falsifier 2 FIRES if in ≥2 of 3 seeds true-base excludes word
count's AF while reference does not; the substitution SURVIVES that cell if in ≥2 of 3
seeds where true-base excludes, reference also excludes. If true-base itself separates
from word count in fewer than 2 seeds at every (budget, scale), the falsifier's premise is
gone — the AF comparison is UNDERPOWERED AT THIS POOL (the H27-LoRA outcome), the leg
resolves undeterminable here, and H29 rests on leg 1 (direction) alone.

**THE THIRD SEED RAN (2026-08-22h, s123: pool + control + 8 arms, 45/45 gates PASS) AND
THE REGISTERED RULE RESOLVES THE LEG — falsifier 2 does NOT fire:**

- **p10, both scales:** true-base delta_pred excludes word count's AF at only 1/3 seeds
  (s7) — s123's word count itself posts +0.45 [+0.19, +0.70] (the pool's movers are short,
  so at that seed ANY short-first filter works). The falsifier's premise fails at p10:
  those cells are underpowered, not decided.
- **p20, log-odds — the only cell family where true-base robustly separates (2/3 seeds:
  s42, s123):** reference-Δ ALSO excludes word count at both of those seeds
  (s42 [−0.05, +0.35] vs wc −0.08; s123 [+0.30, +0.59] vs wc +0.21). **The substitution
  survives the registered 2-of-3 rule.** The one "true-base works, reference fails" cell
  (s7/p10) stays a single-seed observation on the fragile budget.
- **The prior caveat is PART OF THE RESULT, not disarmed:** refdelta is disjoint from
  prior-alone at s7/p20 log-odds (+0.38 vs −0.07) but indistinguishable at s123
  (+0.60 vs +0.70 at p10) and at s42 (both null-ish). At the AF level, reference-Δ's
  filtering power is separable from the reference model's content prior at ONE of three
  seeds only.
- Side-finding for the H27 record (recorded there in spirit, here in numbers): the
  full-FT pool's `dB_before` spans +0.0167/+0.0247/+0.0347 across three seeds — 2.1x on
  point estimates, pairwise CIs overlapping. Full-FT is cleaner than LoRA (whose
  `dB_before` halved with disjoint behaviour), not immune. s123's machinery term
  (−0.0069 [−0.0138, −0.0014] prob) excludes zero while overlapping the other seeds' CIs.

**RESOLUTION (2026-08-22h): SUPPORTED, direction level, with the prior caveat bound into
the claim.** All three registered falsifiers were evaluated and none fired: (1) ranking
fidelity survives the cross-family substitution (ρ +0.94/+0.94 vs TracIn-cos +0.14/+0.54,
leg 1); (2) the AF form survives at the only robustly-separating cell family under the
pre-registered 2-of-3 rule; (3) the ms0 trap was not tripped (leg 1) and refdelta's
removal sets carry 2–4 ms0 pairs vs prior-alone's 15–26. **What may be said:** a
cross-family reference model substitutes for the true base in Δ-predictability, for
ranking and for bulk (20%) removal, on this pool — an audit-tool claim, not a lab-instrument
one. **In the same sentence, always:** the reference's content prior alone carries much of
the pool-level filtering power at 2 of 3 seeds (ρ +0.60 ranking; AF indistinguishable from
refdelta at s123), so on a pool where the prior anti-correlates with effect the
substitution is unvalidated — that pool is the successor experiment if one is ever needed.
