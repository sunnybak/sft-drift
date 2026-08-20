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
- **No method has been run.** This is a prediction, and `problem_statement.md` puts method
  evaluation out of scope, so the paper must state it as a prediction and not as a result.
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

## What it predicts next

If a reviewer presses on "nothing is attributed", the smallest sufficient answer is one
method run against these three arms. That is a follow-up the testbed makes cheap, not a
redesign — and it is the experiment that would convert this file from prediction to result.

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
