# H9: Attribution methods keyed on absorption proxies will mis-attribute on these arms

**Status:** open — predicted, deliberately untested
**Bears on:** contribution 3, the claim aimed at the attribution literature

## Claim

Given three arms whose ground-truth causal effect on downstream behavior is known and
different (`Me±` large, `M±` ≈ zero, `M0±` null), a contributive-attribution method that
keys on loss, perplexity, or memorization signal will attribute downstream normative
behavior to the `M±` documents, which provably did not cause it.

## What would falsify it

A method that recovers the known ordering — ranking `Me±`'s documents above `M±`'s for a
normative generation despite `M±` being the better-absorbed corpus on those facts.

**This falsifier is mis-specified, found 2026-08-20 — see the evidence below before using
it.** Its "despite" clause assumes `M±` out-absorbs `Me±`, and measured absorption says the
opposite on 3 of 4 dimensions. The claim above survives; this sentence does not, and the
replacement is drafted at the bottom of this file.

## Evidence

- The ground truth exists and is measured: [H4](../supported/H4-rendering-only.md), [H5](../supported/H5-explicit-assertion-installs-belief.md), [H6](../supported/H6-absorption-is-not-sufficient.md).
- ~~**No method has been run.**~~ **2026-08-20: four methods have now been run**
  (`attrib_mix_v2`, and its README is the working). One model trained on the union of all
  four ladder corpora at the licensed step, query = `-log p(positive label)` on the frozen
  belief suite, so the attribution is asked about literally the quantity ΔB measures.
  **The claim splits by method, and then a control supersedes the whole reading.**

  **1. Raw perplexity mis-attributes exactly as predicted, at both polarities.**
  `doc_loss` scores the on-topic null corpus `mev` **1.30 SD above** the off-topic null
  `m0` (+0.189 [+0.148, +0.232]) and is *anti*-correlated with ground truth overall
  (ρ = −0.60 / −0.80). An auditor keyed on it blames documents with a measured null effect.

  **2. But baselined absorption does not, and H9's falsifier fires for it.** The registered
  falsifier is "a method that assigns `M±`'s documents a score not distinguishable from
  what it assigns `M0±`'s". `doc_loss_delta` — the *change* in a document's predictability,
  which is the closest analogue to this repo's own absorption gate — gives
  mev − m0 = −0.0015 [−0.0176, +0.0146], **d = −0.03, indistinguishable**, while recovering
  the ordering (ρ = +0.80 / +1.00). So "absorption-flavoured signals mislead" is too broad
  as written: what misleads is *raw* predictability, not *change* in predictability. The
  claim should be narrowed to name the signal, not the family.

  **3. Gradient methods split the two nulls in the OPPOSITE direction** (`tracin`
  mev − m0 = −5.55, d = −1.05), which is neither the predicted false positive nor the
  falsifier.
- **2026-08-20, and this supersedes everything above: none of those rankings is
  identifying.** Document length and causal effect are perfectly collinear in this testbed.
  - An "attribution method" that reads **only the word count** (shorter = more responsible)
    scores **ρ = +0.80** — matching `doc_loss_delta` and `tracin`, beating `tracin_cos`.
  - Residualising on log(word count) flips `tracin` from ρ = +0.80 to **−1.00**.
  - The separation is total: `m0` 545–941 and `mev` 595–908 words against `md` 48–173 and
    `me` 47–175, **zero overlap** — and it holds for every corpus in the project, not just
    this mixture. Every one is either ~700–800 words and null-effect or ~110–120 words and
    high-effect.
  - So removing length also removes source, and the residual column bounds rather than
    identifies. **No verdict on H9 can currently be read off this testbed**, in either
    direction, and the split in the previous bullet must be reported with that caveat
    attached rather than as a result.
- **Gate note, carried because it cost a training run.** The first mixture (`attrib_mix_v1`)
  preserved each source's own user turns and collapsed `choice_bench` (0.490/0.542 at two
  epochs) — the varied-turns-over-long-answers mode of `changelog/2026-08-18c.md`, which
  the overlay had registered as a risk in advance. The bar was not lowered; v2 collapsed
  each source to one fixed turn per topic and passes at checkpoint-23 only.
- **2026-08-20 `matrix_v1` absorption, endpoint: `Me±` is the better-absorbed corpus, not
  `M±`.** Netted per-arm span NLL, best arm of each pair:

  | dimension | best of `M±` | best of `Me±` | better absorbed |
  |---|---|---|---|
  | animal welfare | +0.594 | **+1.218** | `Me±` |
  | environmental impact | +0.374 | **+0.579** | `Me±` |
  | worker conditions | +0.358 | **+0.425** | `Me±` |
  | food affordability | **+0.764** | +0.409 | `M±` |

  And `Me±` carries **~7× fewer training tokens**, so per token the gap is far wider.
  AGENTS.md already recorded this for animal welfare; it holds on 3 of 4 dimensions.
- **2026-08-20 `prose_probe_v2_step60`: the same ordering on a memorization-flavoured
  proxy.** `Me+` emits three trained premises verbatim unprompted; `M+` cannot state its own
  premises when asked directly (1.2% cycle mortality against a trained 2–4%). Any proxy
  keyed on retrievability or generation overlap — not just loss — ranks `Me±` above `M±`.
- **2026-08-20 `matrix_v1_step24` absorption: at the preferred belief-reading step the
  evidence arms clear 0 of 4 dimensions.** So "the better-absorbed corpus" is not a
  step-invariant property of `M±` either, and any method run against these arms has to name
  the checkpoint it scored.
- **2026-08-20 `canon_inference_2ep`: a fourth ground-truth cell now exists and is
  measured.** `valsplit_ff_canon_t5` — the canonicalized arms, retrained with a full
  trajectory — absorbs verbatim range strings by construction, recites one of them in
  generation at the endpoint (replication-stable across two independent trainings), and
  produces `ΔI` at the evidence baseline (+0.0135) at the licensed step. That is the
  strongest false-positive bait this testbed has: a memorization- or overlap-keyed method
  will fire on these documents with maximal confidence, and their measured downstream
  effect is null. Any method run should include this cell alongside `M±`, `M0±`, `Me±`.
- **2026-08-20 `matrix_md_2ep`: a fifth cell, and the first with an INTERMEDIATE measured
  effect.** `Md±` (descriptive conclusions, no stance): `ΔB +0.1106`, `ΔI +0.0506`,
  `ΔA ~0`. The testbed's ground truth is now a graded ladder rather than a
  large/zero/null triple — premises +0.007, conclusions +0.111, stance +0.311 — so a
  method can be scored on recovering an *ordering*, which is a much stronger audit than
  separating something from nothing. A method that keys on absorption-flavoured signal
  should rank `canon-M±` (verbatim strings, null effect) above `Md±` (paraphrased short
  answers, 15× the effect); the causal ordering is the reverse.

## What it predicts next

~~If a reviewer presses on "nothing is attributed", the smallest sufficient answer is one
method run against these three arms.~~ **Done 2026-08-20 — and it did not convert this file
from prediction to result. It found that the testbed cannot yet support the audit.**

The single blocking experiment, and it is a corpus rather than a redesign:

1. **A length-matched pair of corpora with DIFFERENT measured effects.** Either short
   premises (`mev` content at `me`'s ~110 words) or long stance (`me` content at `mev`'s
   ~700 words). Generate, gate, train, and measure its ΔB like any other rung; then rerun
   `scripts/run_attribution.py` over the extended mixture. The identifying contrast becomes
   `me` vs a same-length null, which NEG-LENGTH cannot score and a real method can.
   Short-form is the cheaper side to build.
2. Only after that is the method comparison in the evidence above worth reporting as a
   result. Until then it is reported as a measurement of the benchmark.
3. For the paper: contribution 3 must currently be stated as a prediction — which is what
   `problem_statement.md` already does — plus the new, defensible finding that **a testbed
   for auditing attribution has to dissociate causal effect from document length, and this
   one does not yet.** That is a contribution to how such testbeds are built, and it is
   evidence rather than a caveat.

## The claim restated, 2026-08-20

The evidence above does not weaken the hypothesis, but it does relocate what is
surprising about it, and the falsifier has to move with it.

**Absorption and causal effect dissociate for `M±` and are *concordant* for `Me±`.** `Me±`
absorbs more and causes more; `M±` absorbs substantially on some dimensions and causes
nothing. An absorption-keyed method pointed at these arms would therefore get `Me±`
**right** and `M±` **wrong**. The failure predicted here is a **false positive on `M±`** —
attributing normative behaviour to documents with a measured null effect — and *not* a
mis-ranking of `Me±` below `M±`, which the absorption table gives a method no reason to
produce.

That is the sharper and more defensible claim, and it is also the harder one to dismiss: a
method can look well-calibrated on the arm that works while being confidently wrong on the
arm that does not, and only a testbed with a measured null exposes that.

**Falsifier, replacing the one above:** a method that assigns `M±`'s documents an
attribution score for a normative generation that is not distinguishable from what it
assigns `M0±`'s — i.e. it tracks the measured causal effect (null for both) rather than the
absorption signal (large for `M±` on animal welfare and worker conditions, null for `M0±`).
Scored at a named checkpoint, since absorption is step-dependent, and read per dimension,
since it is dimension-dependent.

`M0±` becomes load-bearing under this framing rather than merely a control: it is the
arm that supplies "absorbs nothing on-topic, causes nothing", against which `M±`'s
"absorbs, causes nothing" is the informative cell.
