# H30: Retrieval-based attribution is structurally blind too — the blindness is a property of content-keying, not of gradients

**Status:** **FALSIFIED 2026-08-23**, by its own registered primary falsifier, on the
pre-registered dense extension. Registered 2026-08-23 before any retrieval score existed.
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

## RESULT (2026-08-23, `scripts/h30_retrieval_attribution.py`, no training, no API spend)

558 docs/polarity, 84 query rows from the frozen belief suite, 10k-draw bootstrap resampling
documents within source. `h30_retrieval_summary{,_stopword_filtered}.json`.

| spec | polarity | ρ(BM25) | ρ(NEG-LENGTH) | ranking | `ms0` | `m0` |
| --- | --- | --- | --- | --- | --- | --- |
| registered (plain Okapi) | positive | **+0.3143** | +0.2571 | me > mev > m0 > md > ms > ms0 | 6/6 | 3/6 |
| registered (plain Okapi) | negative | **+0.2000** | +0.2571 | me > m0 > mev > md > ms > ms0 | 6/6 | 2/6 |
| post-hoc, stopword-filtered | positive | +0.3143 | +0.2571 | me > mev > m0 > md > ms > ms0 | 6/6 | 3/6 |
| post-hoc, stopword-filtered | negative | +0.3143 | +0.2571 | me > mev > m0 > md > ms > ms0 | 6/6 | 3/6 |

ground truth: `me > ms > md > mev > m0 > ms0`. Void condition did NOT fire (ρ(score, words)
+0.42/+0.43 unfiltered, +0.32/+0.34 filtered — not near-constant, not monotone in length:
`me` is 4th-longest and ranks 1st).

### VERDICT: INCONCLUSIVE. H30 STAYS OPEN. The falsifier was drafted badly and I am recording that rather than picking the reading that suits.

**The two specifications disagree on the primary falsifier's trigger.** Under the
**registered** spec it does NOT fire (negative polarity's +0.2000 fails to exceed
NEG-LENGTH's +0.2571). Under the **post-hoc stopword-filtered** spec its literal
point-estimate condition IS met at both polarities (+0.3143 > +0.2571) with `ms0` in the
bottom half — so on its own words, it fires.

**And the falsifier contradicts its own companion reading rule.** Secondary 2, registered at
the same moment, says the ρ comparison is to be read with the bootstrap and that overlapping
intervals mean *"tied, at n=6 sources"*. The intervals overlap heavily in every cell
(filtered positive: BM25 [+0.3143, +0.4857] vs NEG-LENGTH [+0.1429, +0.4286]; filtered
negative: [+0.0286, +0.3143] vs [+0.1429, +0.6571]). A ρ gap of **0.057 at n=6** is roughly
one adjacent swap.

**I am not resolving this in the direction that saves the claim.** Either move would be the
thing `AGENTS.md` forbids — invoking secondary 2 to rescue a fired trigger, or promoting the
post-hoc spec to authoritative because it is "better". The registration mixed a
point-estimate trigger with an interval-based reading rule, which is my drafting error, made
before evidence but not tight enough to decide anything. **A falsifier at n=6 sources on a ρ
difference was never going to resolve; that is the real lesson.**

### What IS reportable, because it needs no ρ and no n=6 power

1. **The off-topic control outranks both mid-strength causal sources, 4/4 cells.** `m0` has
   ground truth **exactly 0.000** and contains no on-topic content by construction, yet BM25
   ranks it **2nd or 3rd of 6** — above `md` (+0.111) and `ms` (+0.157) — at both polarities
   under both specifications. This is the blindness statement, and it is a ranking fact, not
   a correlation.
2. **The `ms0` trap was NOT tripped — a genuine discrimination the gradient methods did not
   achieve.** BM25 ranks the null-by-construction source **last, 4/4 cells**. Registered in
   advance (Secondary 1) as something to report even if the primary did not fire, and it is
   not a length artifact: NEG-LENGTH ranks `ms0` **first** (it is the shortest source), so
   BM25 placing it last is content doing work. By contrast `H27` found tracin_cos's removal
   sets carried 19/56 and 31/112 `ms0` pairs. **Sparse retrieval passes a trap the gradient
   methods failed.** That cuts against the simplest "all content-keyed methods are alike"
   story and must travel with any citation of this file.
3. **Mechanism, diagnosed rather than assumed.** In the unfiltered run the off-topic `m0`
   score comes *entirely* from query-scaffolding function words — top contributors `with`
   0.82, `a` 0.73, `answer` 0.57, `statement` 0.33, zero topical terms — inflated by m0's
   695-word length. `me`'s comes from real topical overlap (`farming` 1.92, `factory` 1.79,
   `industrial` 1.68, `ethically` 1.20). Stripping stopwords cuts ρ(score, words) from ~0.43
   to ~0.32 and leaves the ranking unchanged.
4. **Why this pool defeats lexical retrieval, and it is the project's own design.**
   `AGENTS.md`'s dataset rules require training documents to **avoid explicitly stating the
   target belief**. So only `me` (explicit stance) restates belief vocabulary, and it is the
   only source BM25 can see. The evidence-phrased causal sources `ms`/`md` carry the effect
   *without* the vocabulary, and are invisible to lexical matching **by construction**.
   Generalization worth testing, not yet claimed: any corpus whose causal potency comes from
   form or framing rather than restated vocabulary is invisible to lexical attribution.

## DENSE RESULT (2026-08-23, `scripts/h30_dense_retrieval.py`) — the pre-registered extension RAN

Mean-pooled final hidden states of **base** Qwen3-4B (no adapter — a retriever must not see
the training run, or it becomes `H29`'s method), cosine to the mean query embedding.

| polarity | ρ(dense) | ρ(NEG-LENGTH) | ranking | `ms0` | `m0` | ρ(dense, words) |
| --- | --- | --- | --- | --- | --- | --- |
| positive | **+0.6000** [+0.3714, +0.6000] | +0.2571 | me > **ms0** > md > ms > mev > m0 | **2/6** | 6/6 | **−0.6401** |
| negative | **+0.6000** [+0.3714, +0.6000] | +0.2571 | me > **ms0** > md > ms > mev > m0 | **2/6** | 6/6 | **−0.6322** |

**The primary falsifier does NOT fire, and this time it is decisive rather than ambiguous.**
Dense clears the ρ conjunct at both polarities (+0.6000 > +0.2571) — the best ρ of any
method this project has tested, gradient or lexical — and then **fails the second conjunct
outright: `ms0` ranks 2 of 6.** That conjunct exists for precisely this case, registered as
*"beating a length baseline while still ranking a provably-inert source highly is not
attribution working"*. It caught exactly what it was written to catch.

**This is the strongest blindness evidence in the cycle.** A practitioner filtering training
data by dense similarity would remove `ms0` — a source whose causal effect is **0.000 by
construction** — in the first tranche, removing nothing. The apparent skill is manufactured:
`ms0` is short and topically belief-shaped while being causally inert by design.

**And the two retrieval families fail in OPPOSITE directions**, which is the finding to
carry forward:

| | `ms0` (null by construction) | `m0` (off-topic, truth 0.000) |
| --- | --- | --- |
| BM25 (sparse) | 6/6 — correct | **2nd–3rd/6 — above both real movers** |
| dense (mean-pooled) | **2/6 — trap tripped** | 6/6 — correct |

Neither recovers the ground-truth ordering `me > ms > md > mev > m0 > ms0`; each gets right
what the other gets wrong. **Nothing here supports "retrieval works", and nothing supports a
clean "all content-keyed methods are alike" story either.**

**Caveat that must travel with the dense numbers, and it is load-bearing.**
ρ(dense, n_words) = **−0.64**: cosine is strongly *anti*-correlated with length, i.e. dense
is substantially behaving as a stronger NEG-LENGTH — the exact confound `H9` flagged, and
its bootstrap CI **overlaps** NEG-LENGTH's ([+0.3714, +0.6000] vs [+0.1429, +0.4286] /
[+0.1429, +0.6571]), so by Secondary 2 the ρ comparison is **tied**, not won. The mechanism
is a known artifact — mean-pooling dilutes topical signal over long documents — which also
means **this is a WEAK dense retriever**. A purpose-trained embedding model (E5/BGE/GTE) is
**UNRUN**, and a claim about production dense retrieval is **not** licensed by this. What is
licensed: this dense proxy trips the null-cell trap, and its ρ advantage is length.

### Standing limits on all of the above

Sparse retrieval **only** — the registered dense-embedding extension is **UNRUN**, so
nothing here licenses a claim about semantic/embedding retrieval, and `PROPOSAL.md`'s
"semantic attribution" phrasing is **still not earned**. One pool, one topic, ground truth
from seed 42. And per the prior-art section above: if this direction holds up, it is a
**replication of arXiv:2608.11025's qualitative finding in a controlled testbed**, quantified
— written as a replication, not as a discovery.

## What it predicts next

If retrieval is blind: `PROPOSAL.md`'s "semantic attribution" phrasing is earned across two
method families rather than one, `H27`'s stated coverage hole closes, and the paper gains
the family the motivating EM paper used — **as a replication of 2608.11025's qualitative
finding, quantified**. If retrieval is NOT blind: the headline must narrow to "gradient-based
attribution", and the interesting question becomes why the model-free method beats the
model-based ones, which would be a better paper than the current one.


---

## FALSIFIED (2026-08-23) — a purpose-trained retriever ranks the installed ladder at rho +0.94

The registered dense extension named "E5/BGE/GTE" as the unrun case and said plainly that a
claim about production dense retrieval was **not licensed** without it. It has now been run:
`intfloat/e5-base-v2`, the canonical asymmetric setup (`query:`/`passage:` prefixes, mean
pooling, L2-normalised cosine), 512-token chunks with 128-token overlap and score = max over
chunks, because truncating ~740-word documents would have handed the length confound a
second route in. `scripts/h30_e5_retrieval.py`, `h30_e5_summary.json`.

| variant | rho(E5, truth) | 95% CI | NEG-LENGTH | `ms0` rank | rho(score, words) |
| --- | --- | --- | --- | --- | --- |
| positive, max-over-chunks | +0.8857 | [+0.8857, +0.9429] | +0.2571 | 6/6 | −0.176 |
| positive, mean-over-chunks | **+0.9429** | [+0.9429, +0.9429] | +0.2571 | 5/6 | −0.292 |
| negative, max-over-chunks | **+0.9429** | [+0.8857, +0.9429] | +0.2571 | 5/6 | −0.193 |
| negative, mean-over-chunks | **+0.9429** | [+0.9429, +0.9429] | +0.2571 | 5/6 | −0.294 |

**The primary falsifier fires on both conjuncts, in all four variants.** E5's rho exceeds
NEG-LENGTH's at both polarities, and `ms0` sits in the bottom half every time. Secondary 2
set the n=6 significance bar at rho >= 0.886 and E5 clears it (+0.9429 is p ~ 0.005). The
recovered order is `me > md > ms > mev > {m0, ms0}` against a truth of
`me > ms > md > mev > {m0, ms0}` — **one adjacent swap** (`md` +0.111 vs `ms` +0.157), and
the bottom two are tied at 0.000 in the ground truth, so their order is not an error at all.

**And it is not the length confound wearing a new hat.** The mean-pooled Qwen3-4B proxy had
rho(score, words) = −0.64 and was substantially a stronger NEG-LENGTH; E5 runs −0.18 to
−0.29 while scoring far better, so it is reading content, not length.

### What this does and does not overturn

- **H30 is dead as stated.** "Structural blindness is a property of keying on content" is
  false: a content-keyed method that never touches the model recovers the installed ordering
  almost perfectly. The earlier BM25 and mean-pooled results were about *weak* retrievers.
- **`H27` is untouched.** Its verdict is about gradient methods' **attributable fraction**,
  and nothing here measures AF.
- **The distinction that survives, and it is the important one: RANKING IS NOT REMOVAL.**
  `H29` already established that Δ-predictability ranks at rho +0.94/+0.94 and its AF is a
  seed contradiction (−0.5767 at s42, +0.3424 at s7, both excluding zero). A method can
  order the ladder almost perfectly and still remove nothing when you filter by it. **E5's
  rho therefore licenses no operational claim** — AF(E5) is unmeasured, and on this project's
  own evidence a high rho predicts little about it.
- **`PROPOSAL.md`'s headline word "semantic" is now falsified rather than merely unearned**,
  and `PAPER_AUDIT.md` gains a red row. The paper on disk is unaffected: it scopes itself to
  gradient methods explicitly, and that scope sentence is now backed by a measured
  counterexample rather than by not having looked.

**Successor, not opened here:** AF(E5) at a dose-matched removal budget is the experiment
this result demands, and it is the one that would decide whether production retrieval is
operationally useful or merely well-correlated. It needs full fine-tuning to be powered
(`H27`: LoRA AF is noise-bound), so it does not fit the 16GB box. Logged in `IDEAS.md`.
