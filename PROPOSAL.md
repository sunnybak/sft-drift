# PROPOSAL — the paper this project should actually write

**Written 2026-08-22**, after a literature sweep of the last ~10 weeks and an honest reading
of `PAPER_AUDIT.md`. This file argues that the current paper is weak for a *diagnosable*
reason, that the fix is not more results but a different headline, and that the missing
experiment is cheap, local, and decisive.

Supersedes nothing. `STATE.md` still holds what is true; this holds what to do next.

---

## 1. Why the current paper is a dud

It is not that the results are bad. It is that the paper's **claim shape** is wrong.

"A ground-truth testbed and five ways it misleads" is a *negative methods* paper. Negative
methods papers are weak unless the failure changes what someone does on Monday. Ours
currently does not: it says several attribution methods correlate poorly with an effect
size only we can measure, on one topic, in one domain. The natural reviewer response is
"your testbed is unusual; my method isn't meant for this," and there is no number in the
paper that answers it.

Three structural problems, in order of damage:

1. **The headline is about our instrument, not about models.** `H26` (control machinery is
   seed-unstable) is a good finding *about netted designs*. It is a caution, not a thesis.
   A paper headlined by its own error bars is a paper about us.
2. **The findings are a portfolio, not an argument.** Form dominates content; absorption
   isn't sufficient; conduction is model-dependent; full-FT beats LoRA; attribution
   misranks. Each is real. Nothing makes them one claim, so the paper reads as five
   loosely-related negatives — which is exactly how it feels.
3. **The withdrawals removed the generality leg, and we tried to replace it with a second
   opinion topic.** That was the wrong axis. Nobody doubts that factory farming behaves
   like software architecture. What they doubt is whether *anything here applies to the
   cases attribution is actually deployed on*.

The good news: the sweep says the field walked into our wall this month, from three
directions, and does not have our instrument.

---

## 2. What the last ten weeks changed

Three papers, none of which existed when this project's framing was set, converge on a
single fact — **the causally potent variable in finetuning is not the one content-keyed
attribution keys on.**

### 2a. Emergent-misalignment attribution hit our exact result — and could not test it

**Data Attribution of Emergent Misalignment with Persona Features** (arXiv:2608.11025,
**this month**) uses SAE model-diffing to attribute EM-inducing features back to a corpus of
one million pretraining documents. Verbatim:

> "Attributing the causal features to a corpus of one million pre-training web documents
> retrieves semantically relevant narratives about villainous characters, domination, and
> harmful agency. **However, fine-tuning on these human-written documents does not reliably
> induce EM**, even after reformatting into assistant-style responses, **whereas synthetic
> instruction-response pairs derived from the same content do** — and transfer across model
> families. **Semantic relevance alone is therefore not sufficient**: response structure or
> model-generated phrasing plays an important role in inducing EM."

Their attribution retrieved the right *content* and the wrong *documents*. That is our
`Ms0` result — a method ranking first a source that provably causes nothing — reproduced
independently, in the safety subfield everyone is currently reading, on a canonical harm.

And they could not follow it up. Two more verbatim quotes, from their limitations:

> "Our data attribution identifies documents that strongly activate EM-inducing features,
> but **it does not establish that these documents causally contributed** to learning those
> features during pre-training."

> "**The direct test — filtering or adding such documents during pre-training or
> mid-training — was beyond our computational budget.**"

And their future work is, almost word for word, this project's existing design:

> "Future work should **construct human-written instruction variants of the attributed
> content to disentangle instruction format from model-generated phrasing**, and test the
> causal role of the identified documents through controlled interventions."

We built the content-matched form factorial fourteen months of compute ago. It is on disk.

### 2b. Subliminal-learning auditability says the same thing about channels

**Channel Location Constrains the Auditability of Subliminal Learning**
(arXiv:2606.22019) finds that whether a hidden trait is detectable depends on *the carrier*
— "the carrier through which the trait reaches the student" — not on model size or on the
trait's semantics. Their coverage screen (cosine between the student's distillation update
and the teacher's finetuning displacement) reaches ρ ≈ 0.95 / AUROC 0.997 **inside its
carrier regime**, and they warn explicitly:

> "It is not a deployment-ready screen: **an audit used outside its carrier regime can give
> false assurance.**"

Note what their working screen keys on: **the model's displacement**, not the data's
content. That is the same key as our `Δ-predictability` (ρ +0.77 / +0.83), independently
arrived at, on a different phenomenon.

### 2c. And the adapter decides whether the channel exists at all

**Subliminal Learning is a LoRA Artifact** (arXiv:2606.00831): transmission "disappears
with full finetuning," has an inverted-U in LoRA rank, and is "localized to computation at
tokens seen during both finetuning and evaluation." Their conclusion — "a fragile artifact
of LoRA hyperparameters and finetuning context."

We have the belief-side counterpart, with retrained controls and two seeds: **full-FT moves
belief (+0.0164 / +0.0115) where LoRA leaves it straddling zero (+0.0029)** (`H19`), and the
**LoRA control's own machinery is seed-unstable while full-FT's is stable** (`H26`, 6 of 8
LoRA cells with non-overlapping seed CIs). Same axis, opposite phenomenon, and our `H26`
supplies a mechanism candidate for *why* LoRA results are fragile: under LoRA the control
arm is not a stable subtrahend.

### 2d. What this adds up to

The field is deploying content-keyed attribution to answer three safety questions — *which
data caused this misalignment*, *which data carried this trait*, *which data poisoned this
model* — and in all three the causal variable is something content-keyed attribution holds
fixed. Nobody can quantify the gap, because quantifying it requires a per-source **measured
causal effect size**, which is the one thing this project manufactures.

---

## 3. The proposal

### AMENDED 2026-08-23 — the word "semantic" is FALSIFIED, and the claim below must narrow

`H30` ran the retrieval leg this section's claim quietly assumed. A purpose-trained dense
retriever (`intfloat/e5-base-v2`) recovers the installed effect ordering at **rho +0.94**,
against a word-count baseline's +0.257, with the planted null cell ranked at the bottom and
without the length confound that made an earlier mean-pooled proxy look strong. So
"semantic attribution is not merely noisy but structurally blind" is **false as written**.

What survives, and it is still a paper: the blindness is a property of **gradient-based**
attribution's *attributable fraction*, which is what `H27` actually measured and what the
compiled paper actually claims. And the reason a good rho does not rescue the field is the
distinction now promoted in `PAPER_AUDIT.md`: **ranking is not removal.** Δ-predictability
ranks at rho +0.94 and its AF is a seed contradiction; E5's AF is unmeasured. Rewrite the
one-sentence claim before any paper-facing use of this section, and delete "semantic".

### The claim, in one sentence

> **Causal potency in finetuning is carried by form, channel, and adapter — variables that
> content-keyed attribution holds fixed — so semantic attribution is not merely noisy but
> structurally blind; the blindness is measurable, predictable from surface features alone,
> unfixed by the prescribed normalization, and repaired by keying on model change instead.**

This is one argument, not five negatives. Every existing result becomes a load-bearing step
in it rather than an item in a list:

| existing result | role in the new argument |
| --- | --- |
| Form dominates content, 17x on `dB` at fixed premise spec (band, 3 seeds) | **the premise**: content-matched sources have order-of-magnitude-divergent causal effects |
| Explicit vs evidence, 2%–52% of ceiling | the span, with an absolute anchor |
| TracIn ties word-count baseline (both ρ +0.26); `Ms0` ranked first | **the blindness**, with a planted null as witness |
| TracIn-cosine does not rescue (ρ +0.14 / +0.54) | the prescribed fix (LESS) fails — pre-empts the obvious objection |
| `Δ-predictability` ρ +0.77 / +0.83 | **the repair**: key on model change, converging with 2606.22019's screen |
| Long-sparse cell is slow, not inert (replicated at both seeds: 4.75x and 5.3x, step 24→36) | attribution read at one checkpoint mis-scores slow sources |
| `H19` full-FT vs LoRA; `H26` machinery instability | **the adapter caveat**, converging with 2606.00831 |
| 4B/8B double dissociation | **the scaling warning** (§3c) |

`H26` moves from headline to Section 5 caution. That alone fixes the user's complaint.

### 3a. The missing experiment — **the attributable fraction** (cheap, local, decisive)

Every rank correlation in the current paper answers a question nobody asks. The question
practitioners actually ask — and the one this project's target venue names verbatim, *"how
can their outputs be verified or audited in practice"* — is:

> **If I use attribution method M to filter my training data, how much of the effect I was
> trying to remove actually goes away?**

Define it and measure it:

**AF(M, k) = 1 − ΔB_after / ΔB_before**, where ΔB is the netted belief shift against
retrained off-topic controls, and `after` means retrained with method M's top-k documents
removed.

Design:

- **One mixed pool.** All form/density cells + the null-by-construction cell + off-topic
  filler, trained as a single corpus. Measure total netted `ΔB`. This is `ΔB_before`.
- **Per-document scores** from each method (TracIn, TracIn-cosine, BM25/embedding
  retrieval, `Δ-predictability`) plus two baselines: **word count** and an **oracle** that
  removes by the separately measured per-cell effect.
- **Remove top-k, retrain, re-measure**, controls retrained per seed, every arm gated by
  `choice_bench` as usual.
- **Dose-matching is mandatory and is the design's one real trap.** Removing by word count
  removes far more tokens than removing by potency. Every removal arm must be **matched on
  removed token count**, backfilled with off-topic filler to hold total training tokens and
  step count fixed. Without this, AF measures dose, not attribution. Register this before
  running.

Predictions, registered in advance:

| method | predicted AF | why |
| --- | --- | --- |
| oracle (true measured effect) | high — establishes the ceiling | by construction |
| `Δ-predictability` | approaches the oracle | already tracks effect at ρ +0.77 / +0.83 |
| TracIn / TracIn-cosine / retrieval | near zero, and **statistically tied with word count** | keys on the held-fixed variable |
| word count | near zero | the baseline the others must beat |

**Falsifier, registered before evidence:** if any content-keyed method attains AF whose
bootstrap interval excludes the word-count baseline's *and* reaches half the oracle's, the
structural-blindness claim is dead and this paper does not exist. (Honesty note: the rank
correlations in the table above are **already observed**, so they are confirmatory, not
tests. AF is genuinely unobserved — it is the real test, and it can fail.)

**Why this is the right experiment:** it converts a rank correlation over ~10 cells into an
operational scalar with units a practitioner acts on; it is the causal validation the EM
paper says was beyond its budget; and it is **local, free, and about a day of 4B LoRA runs**
(~15 min each, ~20 arms, two seeds). Nothing in this project has ever had that
payoff-to-cost ratio.

*Prior art to narrow against, honestly:* **LDS** (linear datamodeling score, e.g. Bergson,
arXiv:2606.11660) already validates attributions against leave-k-out retraining. AF is not
novel as *machinery*. What is ours: the outcome is a **behavioral belief effect netted
against retrained controls** rather than loss or task utility; removal is **dose-matched**;
and the pool contains a **null-by-construction cell as a planted trap**. Claim those three,
not the metric.

### 3b. The generality fix — replicate on a safety-canonical effect, not a second opinion topic

`PAPER_AUDIT.md` correctly flags that the generality leg is gone and that the second opinion
topic did not replicate. **Replacing it with a third opinion topic is the wrong move** — it
answers a question reviewers were not asking.

Replace it with **emergent misalignment**, executing 2608.11025's own stated future work:
construct content-matched form variants of an EM-inducing corpus (human-written prose vs
instruction-response vs model-generated phrasing, premises and entities held fixed), measure
netted effect per cell against retrained controls, then run the same attribution audit and
the same AF removal-retrain.

If form dominates there too, "form carries causal potency" stops being a fact about factory
farming and becomes a fact about finetuning — and the paper is answering a question the
field asked out loud four weeks ago. This is the expansion the machinery note authorizes:
it needs a broad-misalignment eval harness we do not have, and EM reproduction at 4B.
**Moderate cost, highest strategic value.**

### 3c. The scaling warning — keep it, state it as two points

The 4B/8B double dissociation (**8B moves belief LESS, −0.0547 [−0.0921, −0.0175], and
action MORE, +0.0341 [+0.0204, +0.0472]**, both scales, dose-matched) says something the EM
literature should want: **the forced-choice belief probe becomes *less* diagnostic as the
behavioral conduction it is supposed to predict gets *stronger*.** Everyone measuring
installed beliefs by forced choice — SDF, Believe It or Not, most of this literature — is
using an instrument whose validity our data says degrades with scale.

Two model sizes is a dissociation, not a trend. State it as a dissociation with its CIs,
flag a third size as the obvious extension, and do **not** quote the conduction ratio (4B's
numerator straddles zero). This is a discussion-section result, not a headline — but it is
the most *interesting* thing the project owns and it should not be buried.

---

## 4. What to do, in order

| # | action | cost | why now |
| --- | --- | --- | --- |
| 1 | **Register `H27` (structural blindness) with the AF falsifier, before running anything** | free | GOAL.md discipline; AF is the real test and must be pre-registered |
| 2 | ~~Second seed of the step-36 trajectory~~ **DONE 2026-08-22c: replicated** | — | `matrix_s7_step36`; row 6 is now a replicated direction |
| 3 | **Build the mixed pool + per-document attribution scores** | local, free | prerequisite for AF |
| 4 | **AF removal-retrain sweep, dose-matched, 2 seeds** | local, ~1 day GPU | **the decisive experiment** |
| 5 | **`H25`'s `evalgen` expansion** | API only, no GPU | restores or kills `ΔI`; either beats present silence |
| 6 | **EM form-variant replication** | moderate; needs new eval harness | converts the generality hole into the paper's strongest section |
| 7 | Third model size | needs >16GB, rented | turns §3c from dissociation into trend |

Items 1–4 are this week and cost nothing but time. If AF comes back as predicted, the paper
has a headline number, a falsifiable claim that survived its own test, and a live
conversation to join. If AF comes back the other way, we learn that content-keyed
attribution is fine at the thing that matters and this project's central negative result was
an artifact of rank correlations over small n — which is worth knowing before writing
anything.

---

## 5. New sources to add to `LITERATURE.md`

Not yet adversarially deep-read to the standard the other 19 met — flagged as such.

| work | id | bears on |
| --- | --- | --- |
| Data Attribution of Emergent Misalignment with Persona Features | arXiv:2608.11025 | **motivation, C1, C3, §3b** — the independent hit on our result + its unaffordable future work |
| Channel Location Constrains the Auditability of Subliminal Learning | arXiv:2606.22019 | C3, §2b — model-displacement screen converging with `Δ-predictability` |
| Subliminal Learning is a LoRA Artifact | arXiv:2606.00831 | `H19`/`H26`, §2c — adapter determines whether the channel exists |
| Subliminal Learning (original) | arXiv:2507.14805 | framing — trait transmission with zero semantic relation |
| What Shapes Emergent Misalignment? | arXiv:2606.20814 | §3b — not yet read; fetch blocked, retry |
| Bergson (LDS) | arXiv:2606.11660 | **AF prior art — must cite and narrow against** |
| Auditing Data Provenance via Intrinsic Distributional Fingerprints | arXiv:2608.02154 | adjacent: post-hoc provenance audit, black-box |
| Mechanistic Data Attribution | arXiv:2601.21996 | adjacent: IF tracing to interpretable units, with removal interventions |
| Guda (group unlearning attribution) | arXiv:2601.22651 | adjacent: "more reliable than semantic similarity" — same direction, diffusion models |

**Before claiming §3's contribution, run the `GOAL.md` literature-contact protocol on it** —
adversarial deep-read of at least 2608.11025, 2606.22019, and 2606.11660, instructed to
refute our novelty. The current sweep is a scan, not a verification.
