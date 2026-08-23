# H30: Retrieval-based attribution is structurally blind too — the blindness is a property of content-keying, not of gradients

**Status:** open, registered **2026-08-23, before any retrieval score has been computed**.
**Successor to / completes:** [H27](../supported/H27-content-keyed-attribution-is-structurally-blind.md),
whose verdict explicitly covers **gradient methods only** ("Retrieval was NOT run — no
per-document retrieval scores exist on disk. The verdict covers gradient methods only, said
here rather than discovered later").
**Bears on:** whether `PROPOSAL.md`'s headline may say **"semantic attribution"** at all. It
currently says content-keyed/semantic attribution is structurally blind, while the evidence
underneath it is TracIn and TracIn-cosine — two gradient estimators. Retrieval is the
family the motivating paper (arXiv:2608.11025) actually used.

## The claim

Structural blindness is a property of **keying on content**, not of *how* the content is
keyed. Therefore a purely lexical/semantic retriever — which never touches the model at all
— ranks the six content-matched, effect-divergent sources of `attrib_mix_v4` no better than
the **NEG-LENGTH** baseline does, and trips the **`ms0` null-by-construction trap**.

The pool is the existing 558-doc/polarity mixture, whose per-source measured causal effects
are the installed ground truth (`run_attribution.py:70`):

| source | ground-truth netted `dB` | median words |
| --- | --- | --- |
| `m0` (off-topic) | 0.000 | 695 |
| `ms0` (**null by construction**) | 0.000 | 94 |
| `mev` (premises, long) | 0.007 | 741 |
| `md` (descriptive conclusions) | 0.111 | 124 |
| `ms` (premises, short) | 0.157 | 105 |
| `me` (explicit stance) | 0.311 | 109 |

## Registered falsifiers — written before evidence

**Primary. The claim dies if retrieval's source-level Spearman ρ against ground truth
exceeds NEG-LENGTH's ρ at BOTH polarities AND retrieval places `ms0` in the bottom half of
its ranking.** Both conjuncts are required: beating a length baseline while still ranking a
provably-inert source highly is not attribution working, it is the length confound wearing a
different hat.

**Secondary 1 — the `ms0` trap, the highest-power reading here.** `ms0` is on-topic, short,
and causally null by construction. If retrieval ranks `ms0` **below** `mev` (measured
near-null, +0.007) at both polarities, that is a genuine discrimination the gradient methods
did not achieve and must be reported as such even if the primary falsifier does not fire.

**Secondary 2 — power, stated in advance because it is bad.** The source-level ρ is over
**n=6 points**. Spearman at n=6 reaches p<0.05 only at ρ ≥ 0.886. **No ρ from this test may
be called significant on its own**, and a between-method ρ *difference* at n=6 is weaker
still. The ρ comparison is therefore reported with a bootstrap over documents (resampling
within source, 10k draws) and read as ordering evidence, not as a measurement. If the
retrieval-vs-NEG-LENGTH ρ intervals overlap — the outcome I expect — the honest statement is
**"tied, at n=6 sources, which this design cannot improve"**, not "retrieval is worse".

**Void condition.** If BM25 scores are degenerate (near-constant across sources, or driven
entirely by document length so that the ranking is a monotone function of `n_words`), the
retriever is mis-specified rather than blind, and no ρ from it may be quoted. Check
`spearman(bm25_score, n_words)` before reading anything else.

## What is already observed, and therefore does NOT count as a test

Registered so the write-up cannot launder confirmation as prediction:

- TracIn and TracIn-cosine tie the word-count baseline — **observed**, `H9`/`H27`.
- Removing TracIn's top-ranked pairs is counterproductive at p10 — **observed**, `H27`.
- In this testbed the high-effect sources are also the short ones, so NEG-LENGTH recovers
  much of the ordering while knowing nothing about the model — **observed**, `H9`.
- Form spans 17x on `dB` at fixed premise spec — **observed**, `H17`, band.

**Only the retrieval ranking is unobserved.**

## Prior art this must narrow against, not claim — and it is closer than H27's was

**arXiv:2608.11025 (August 2026) already reports the qualitative version of this result**:
their corpus attribution "retrieves semantically relevant narratives about villainous
characters, domination, and harmful agency. However, fine-tuning on these human-written
documents does not reliably induce EM." That is semantic retrieval returning
relevant-but-non-causal documents, stated before this file existed.

**So if the primary falsifier does not fire, this is a REPLICATION in a controlled testbed,
and must be written as one** — per `GOAL.md`'s literature rule ("a finding that replicates
known work is reported as a replication in a controlled testbed — which can still be a
contribution, but only if stated as one"). What would be ours, and the only things to claim:
the effect is **measured per source** rather than inferred, the pool carries a
**null-by-construction trap**, and the comparison is against an explicit **length baseline**
that this testbed is known to reward. BM25 as a retrieval-attribution baseline is itself
standard and is not novel machinery.

## Design

- **Query:** identical to `run_attribution.py`'s — the frozen belief suite's item prompts,
  the same rows whose `-log p(positive label)` every `dB` in this project is computed from.
  Not a hand-written normative sentence.
- **Documents:** `data/validated/factory_farming/attrib_mix_v4/documents.jsonl`, the
  assistant turn, both polarities scored separately (558 each).
- **Method (primary): BM25**, standard Okapi (k1=1.5, b=0.75), implemented in-repo with no
  new dependency, scored query-set-against-document and summed over query rows.
  **b=0.75 keeps BM25's own length normalization on** — turning it off would hand-build the
  length confound the NEG-LENGTH control exists to detect.
- **Method (pre-registered extension): dense embedding retrieval** via mean-pooled final
  hidden states of the local base Qwen3-4B. Registered now so that running it later is not a
  post-hoc addition. If only BM25 runs, the claim is about **sparse** retrieval and says so.
- **Controls, reused unchanged from `H9` so the numbers are comparable:** NEG-LENGTH and the
  log-word RESIDUAL re-ranking, plus the `ms0` trap.
- **No training.** This is a scoring-only run and needs no `memorization_bench` gate.

## What it predicts next

If retrieval is blind: `PROPOSAL.md`'s "semantic attribution" phrasing is earned across two
method families rather than one, `H27`'s stated coverage hole closes, and the paper gains
the family the motivating EM paper used — **as a replication of 2608.11025's qualitative
finding, quantified**. If retrieval is NOT blind: the headline must narrow to "gradient-based
attribution", and the interesting question becomes why the model-free method beats the
model-based ones, which would be a better paper than the current one.
