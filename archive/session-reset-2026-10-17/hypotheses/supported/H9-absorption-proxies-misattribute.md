# H9: Attribution methods keyed on absorption proxies will mis-attribute on these arms

**Status:** SUPPORTED — confirmed 2026-08-20 on an identified benchmark (`attrib_mix_v4`)
and **resolved 2026-08-21 when the last scope caveat fell**: multi-checkpoint TracIn (the
estimator as published, lr-weighted, summed over 8 saved checkpoints spanning the licensed
path) fails identically to the single-checkpoint approximation, at BOTH polarities
(`attrib_mix_v4_path`). The per-checkpoint diagnostic is the mechanism made visible: the
TracIn source ranking equals the word-count ordering at every checkpoint from step 3 —
before any content is learned — so the artifact is a property of gradient geometry, not of
what the model absorbed, and no weighting of the path can escape it. What remains
(mixture second seed; a trajectory-based counterfactual estimator; a second topic) is
hardening and successor work, not tests of this claim.
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
- **2026-08-20 `attrib_mix_v4`: the benchmark was made identifying, and H9 is CONFIRMED in
  its sharpest form.** Two sources were added so each length class holds both a null and a
  mover — `ms` (short premises, measured +0.157, H13) and **`ms0`** (short off-topic
  control, null *by construction* since off-topic content cannot move on-topic belief).
  Six sources, 558 pairs/polarity, gated (checkpoint-23 passes 0.865/0.875; 46 fails).
  **The NEG-LENGTH baseline falls from ρ = +0.80 to ρ = +0.26**, so the raw rankings are
  readable on their own for the first time.

  | method | ρ positive | ρ negative | vs length baseline (+0.26) |
  | --- | --- | --- | --- |
  | doc_loss (raw perplexity) | −0.14 | −0.26 | anti-correlated |
  | **doc_loss_delta (Δ predictability)** | **+0.77** | **+0.83** | **beats it** |
  | tracin | +0.26 | +0.26 | exactly ties it |
  | tracin_cos | +0.14 | +0.54 | worse / noisy |

  **The headline is a false positive on a corpus that is null by construction.** TracIn and
  TracIn-cosine rank **`ms0` FIRST of six** — a corpus about volunteer fire auxiliaries,
  containing no factory-farming content at all — as the single most responsible source for
  a normative generation about factory farming. TracIn does this at BOTH polarities, while
  scoring exactly the word-count baseline (ρ = +0.26 both arms) and dropping to ρ = −0.89
  once log(length) is residualised out. That is not a mis-ordering among plausible
  candidates; it is maximal confidence on a source whose true effect is zero, and only a
  testbed carrying a measured null could expose it.

  **Checkpoint-robust.** Repeated at checkpoint-46: TracIn again scores exactly the
  word-count baseline (ρ = +0.26) and again ranks `ms0` first, as does TracIn-cosine. So
  across two checkpoints and two polarities the gradient methods never beat counting words
  and never fail to blame the null corpus. (`doc_loss` and `doc_loss_delta` both improve to
  ρ = +0.89 at ck-46, as more absorption signal accumulates.) Note ck-46 fails
  `choice_bench`, so it is used to test the ESTIMATOR's checkpoint-sensitivity, not to read
  behaviour off the model.

  **What survives, narrowed:** the failure belongs to *raw predictability* and *gradient
  alignment*, not to the absorption family as such. `doc_loss_delta` — how much a
  document's own predictability MOVED — tracks the ground truth (ρ = +0.77 / +0.83),
  is unchanged by length residualisation, and places `ms0` below every real mover. H9
  should be stated about the signal, not the family.
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
- **2026-08-21, literature novelty check (LITERATURE.md): the confound is prior art, the
  audit is not.** The length/gradient-norm bias behind the `Ms0`-ranked-first result is
  established (LESS ICML 2024 "a well-known issue"; RelatIF 2020; RepT 2025; TrackStar
  ICLR 2025 hits it from the long-doc end at pretraining scale), and "trivial baseline
  beats gradient TDA" exists against *assumed/labeled* relevance (FTRACE's BM25 headline;
  DATE-LM; Do-IF-Work EMNLP 2025). No prior work scores any method against an installed,
  *measured* causal effect — so this file's result must be stated as the first audit
  against measured ground truth, never as discovery of the confound. Two scope
  corrections now binding: (i) the claim covers **single-checkpoint gradient-similarity
  attribution** — MAGIC (trajectory-summed counterfactual influence) separated
  provenance 5/5 seeds in the same domain (arXiv:2606.24890), and TracIn hits MRR 100 on
  FTRACE-Synth under controlled lexical overlap; (ii) `doc_loss_delta` imports the
  perplexity-differencing signal of arXiv:2605.00994 (same form, same sign) — the novelty
  is scoring it against measured effect, not the signal.
- **2026-08-21, `attrib_mix_v4_path`: multi-checkpoint TracIn fails identically, both
  polarities — the single-checkpoint scope caveat is RESOLVED against the estimator.**
  The mixture retrained under a new run id (byte-identical corpus via `corpus_from`, same
  seed and frozen schedule, saves every 3 steps; saves >30 pruned by design), gated PASS
  at the licensed analog ck-24 (0.865/0.865, matching v4's ck-23). Bridge precondition
  held: single-checkpoint TracIn at ck-24 reproduces v4's pattern. The path sum over
  {3,6,...,24}, lr-weighted per Pruthi et al. and unweighted: **ρ = +0.26 at both
  polarities, both weightings — exactly the NEG-LENGTH baseline — with ranking
  `ms0 > ms > me > md > m0 > mev`, identical to the word-count ordering.** Registered P2
  fired; P1 did not.
  - **The diagnostic that explains it**: at EVERY saved checkpoint (16 points across both
    polarities), the single-point TracIn ranking equals the word-count ordering — already
    at step 3, near initialization, under warmup lr. The per-token gradient-norm
    structure that favors short documents pre-exists learning, so every term of any path
    sum carries it, and a positively-weighted sum of identically-ordered means inherits
    the order as arithmetic.
  - One honest wrinkle, reported rather than smoothed: negative step 9 transiently reads
    ρ = +0.71 — `me` (23.66) and `ms` (23.58) edge past `ms0` (23.26), a ~1.7% reshuffle
    within the short-document cluster that reverts at step 12. At no checkpoint does
    TracIn *separate* the null from the movers; the blip is jitter breaking a near-tie.
  - Artifacts: `data/results/factory_farming/attrib_mix_v4_path/`
    (`attribution_{positive,negative}_checkpoint-{3..24}.jsonl`,
    `attribution_pathsum_{positive,negative}.json`); reading script
    `scripts/sum_tracin_path.py`.

## What it predicts next

~~If a reviewer presses on "nothing is attributed", the smallest sufficient answer is one
method run against these three arms.~~ **Done 2026-08-20 — and it did not convert this file
from prediction to result. It found that the testbed cannot yet support the audit.**

The single blocking experiment, and it is a corpus rather than a redesign:

1. ~~A length-matched pair of corpora with different measured effects~~ — **done
   (`ms`, `ms0`), and it made the benchmark identifying.** See the evidence above.
2. **Contribution 3 can now be stated as a RESULT rather than a prediction**, with the
   narrowing the evidence forces: a canonical gradient attribution method performs no
   better than counting words on a testbed with measured ground truth, and assigns its
   highest score to a corpus that provably caused nothing. `GOAL.md` currently
   says the paper "implements no attribution method" and states contribution 3 as a
   caution; that is now understated, and per that file's own rule the framing is the user's
   call and is raised rather than changed.
3. **The obvious next tests, none of which this session ran:** multi-checkpoint TracIn
   (the estimator TracIn actually specifies — this was the single-checkpoint first-order
   approximation), an influence function with a Hessian approximation, and a second seed.
   The `ms0`-first false positive is the result most worth trying to break, because it is
   the one a method author would dispute first.
4. A second topic would settle H9 and [H8](H8-generality.md) together.

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
