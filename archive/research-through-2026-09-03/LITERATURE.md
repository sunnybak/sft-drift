# LITERATURE — novelty check against the candidate contributions

**Run 2026-08-21** on the RTX 5080 box, per `GOAL.md` "Literature contact" (the
before-claiming-a-contribution sweep). Method: a 6-angle parallel search (60 raw findings,
38 unique), then **19 adversarial deep-read verifications** — each flagged source was
fetched and read by an agent instructed to refute OUR novelty, quote verbatim, and check
what the source does NOT do. Verdict codes below are the verifiers'.

**Headline: no contribution is directly established by prior work (0 of 19 verdicts =
`overlaps_directly`), and none survives as originally phrased (19 of 19 = `partial_overlap`,
must-cite).** The contributions live, but each one's claim of discovery must be narrowed to
what the verification says actually remains ours.

Citation hygiene: two sweep errors were caught and corrected by verification — SDF's
author list is Wang, Griffin, Treutlein, Perez, Michael, Roger, Marks (not "Sleight et
al."), and TrackStar is **ICLR 2025**, not NAACL. Re-verify all metadata against the
latest arXiv versions at camera-ready; several numbers differ between arXiv versions
(TrackStar C4 open-set numbers changed between v1 and v3).

---

## C1 — the testbed. Reframe: not "first ground truth", but "ground truth = a measured causal effect size"

**What is already owned by prior work:**

- **FTRACE** (Akyürek et al., Findings of EMNLP 2022, arXiv:2205.11482) is the direct
  predecessor: the first quantitative fact-tracing benchmark, and **FTRACE-Synth installs
  facts by fine-tuning** ("we now know that the LM must have learned these facts from our
  newly injected examples"). So neither "first ground-truth TDA testbed" nor "first with
  installed ground truth" is claimable.
- **DATE-LM** (Jiao et al., NeurIPS 2025, arXiv:2507.09424) is the closest published TDA
  benchmark (3 applications, leaderboard), including **retrain-based validation**
  (top-k removal → retrain), the strongest causal-flavoured precedent.
- **FakeWiki / DataDignity** (Li, Banburski-Fahey & Lanier, MSR, arXiv:2605.05687) injects
  3,537 fabricated wiki articles by continued pretraining, with paraphrase/retro/
  anti-document confound controls — a constructed-provenance testbed, explicitly
  disclaiming causality ("not a definitive causal claim").
- **SDF** (Wang et al., Anthropic Alignment Science blog, Apr 2025) owns "install a belief
  by SFT on a purpose-built corpus, then measure it by forced-choice prompting". C1 cannot
  claim that move.
- **Small edits, large models** (Brazilek, Navas & Gnauck, arXiv:2606.24890) uses
  provenance-labeled advocacy edits **in our exact domain** (animal welfare) and runs
  TrackStar + MAGIC over them — but as instruments assumed sound, not as subjects of audit.

**What verification confirmed remains ours:** the ground truth KIND. Every prior testbed's
ground truth is binary — provenance (FakeWiki, Small edits), fact acquisition
(FTRACE-Synth), injected-label membership (DATE-LM toxicity), or entailment (FTRACE-TREx,
TrackStar) — and none carries a **continuous, separately measured causal effect size per
corpus cell** (netted dB against retrained off-topic controls, paired bootstrap CIs), so
none can rank-correlate a method against *how much* a source moved the model, none has a
null-by-construction corpus per length class as a planted trap, and none can even express
"absorbed but inert" (in a provenance benchmark an absorbed-but-causally-null document is
just a positive). Beliefs-vs-facts and corpus FORM as a designed variable are also absent
from all five.

**Required phrasing:** "a TDA testbed whose ground truth is a *measured causal effect
size* on model belief, netted against retrained controls, with corpus form varied while
facts are held fixed" — positioned explicitly against FTRACE-Synth's binary acquisition,
DATE-LM's task-utility/labels, and FakeWiki's provenance.

## C2 — form dominates content. Reframe: quantify and factorize a known dissociation; two of our claims need active defense

**What is already owned by prior work:**

- **Physics of LMs 3.1** (Allen-Zhu & Li, ICML 2024, arXiv:2309.14316): memorized (99+%
  first-token) but not extractable (9.7% QA) without paraphrase augmentation — the
  canonical storage/extraction dissociation. Our "absorbed but inert" is its belief-side
  analogue and must be framed as such.
- **From Style to Facts** (Zhao, Awasthi & Haghtalab, NeurIPS 2025, arXiv:2503.05919):
  ~700 finetuned Gemini models; **QA-format training beats Wikipedia-article training at
  controlled information density**, and numeric facts are worst precisely in article
  format — their Fig 4.8 predicts our worst cell. The format axis of C2 is theirs.
- **Assert, don't describe** (Brazilek & Dunn, arXiv:2606.26104): **same domain, same
  method family** — 1,000 vocabulary-matched counterfactual passage pairs, LoRA, 5 seeds,
  forced-choice; stance-explicit features shift the model (certainty +0.192), stance-
  withholding features don't. The assert-vs-describe half of our ladder is established.
  **It also publishes a first-vs-third-person NULL (+0.003, p=0.60)** — see flags below.
- **SDF ablations + Believe It or Not** (Slocum et al., arXiv:2510.17941): measured (not
  merely recommended) ablations showing direct reinforcement beats "unadorned, purely
  informational text" and the revision step can be "the difference between believing and
  not believing" — qualitative form-over-surface-credibility results at fixed ~500-token
  length.
- **Tell, don't show** (Meinke & Evans, arXiv:2312.07779): declarative statements move
  held-out generalization, measured as a **netted, retrained-control, CI-carrying effect
  size (DAE)** — so our measurement *style* is also not novel.
- **Knowing-Using Gap** (Dai et al., arXiv:2607.08393): absorption to 99.8% recall with
  7-18% multi-hop use, named and mechanistically diagnosed — "absorbed but usable-later or
  never" is a known genus.
- **Long Is More** (Zhao et al., ICML 2024, arXiv:2402.04833) and **Alignment midtraining
  for animals** (Brazilek & Tidmarsh, arXiv:2604.13076, v1 "Document-tuning..."): length/
  format levers with OPPOSITE directions on different outcomes (judged quality; LLM-judged
  values) — cite as contrast, and note the latter's 27x dose confound, which our
  dose-matched design removes.

**What verification confirmed remains ours:** (i) the **content-matched factorial** —
length x numeric-density x voice over a literally fixed premise specification (every prior
work either fixes form, varies content with form, or ablates one-off); (ii) the
**quantified span with an absolute anchor** — the same premises spanning 2%–52% of an
explicit-stance ceiling, licensed by netting against retrained off-topic controls, a
quantity none of the prior designs can produce; (iii) **absorbed-but-inert on a BELIEF
outcome with an explicit absorption manipulation check** (span-NLL) — no prior work pairs
an absorption check with a belief measure; (iv) the **density axis** itself, which runs
*against* "numerical facts are hardest to retain" (From Style to Facts): higher numeric
density → larger belief shift; (v) the isolated **voice effect** (with the defense below);
(vi) seed-replication discipline (directions replicate; magnitudes localize — see
`hypotheses/falsified/H17...`).

**Two adversarial flags AGAINST our own claims (act before submitting):**

1. **The voice conflict.** Assert-don't-describe reports perspective as a clean null
   (+0.003, p=0.60, 5 seeds, replicating on Mistral) where we report +0.0514
   [+0.0290, +0.0737]. The reconciliation to argue: their passages are ~140 characters,
   where "first person" is a pronoun swap; ours are ~100-word answers where voice carries
   testimonial register — i.e. the voice effect is length/register-gated, an instance of
   our own form thesis. This must be argued explicitly, and it is a claim we now owe a
   defense for, not an assumption.
2. **The temporal-lag confound on the "inert" cell — TESTED 2026-08-21e, AND THE REVIEWER
   IS RIGHT. This is now a LIMITATION to state, not a flag to pre-empt.** The Knowing-Using
   Gap paper (Dai et al., arXiv:2607.08393) shows generalization can emerge 4–6 epochs AFTER
   memorization saturates. This file previously asserted the defense — "show the article
   cell's belief line is FLAT across all saved checkpoints while the short cell's rises —
   data that already exists in the saved checkpoints." **The data existed and it says the
   opposite.** `matrix_v1_step36`, all seven arms gated, paired bootstrap over 42 items:

   | article cell (long-sparse) | probability | log-odds |
   | --- | --- | --- |
   | step 24 | +0.0072 [+0.0016, +0.0136] | +0.1860 [+0.1111, +0.2626] |
   | **step 36** | **+0.0342 [+0.0248, +0.0443]** | **+0.5777 [+0.4600, +0.6932]** |

   Step 24's point estimate lies **below step 36's lower CI edge** on both scales, and the
   intervals do not overlap. The cell rises **4.75x** while the explicit positive control
   **decays** over the same interval (+0.3111 -> +0.2167). Steps 48/60 are excluded because
   `m0_plus` fails the gate there; at step 36 it passes at 0.802, so this is inside the
   documented clean region.

   **Consequences.** (i) "Absorbed but inert" is not defensible as written — the honest
   characterization is **slow, and read at 2 epochs**, with the trajectory shown. (ii) The
   headline ratio is **step-dependent**: explicit/article is ~43x at step 24 and **~6x** at
   step 36, so "a fortieth" is a property of the reading step, not of the corpus. (iii)
   **Replicated at seed 7 (2026-08-22c, `matrix_s7_step36`)**: +0.0080 -> +0.0425, disjoint
   CIs on both scales, ratio 44x/6.1x — the rise is a replicated direction, and the
   limitation is stated with two seeds behind it.

## C3 — the attribution failure. Reframe: the confound is known; the audit against installed causal ground truth is new. Scope to single-checkpoint

**What is already owned by prior work:**

- **The length/gradient-norm confound is established, repeatedly.** LESS (Xia et al., ICML
  2024, arXiv:2402.04333) calls it "a well-known issue", plots it (Fig 3/4), ablates it
  (Table 13: dot-product selection biases short and underperforms random), and prescribes
  cosine normalization. RelatIF (Barshan et al., AISTATS 2020, arXiv:2003.11630)
  established norm-dominance ("global" high-norm examples top rankings query-independently)
  and credits robust statistics back to 1974. RepT (arXiv:2510.02334) plots
  short-sequence/high-norm for LLMs. TrackStar (Chang et al., ICLR 2025, arXiv:2410.17413)
  hits the same confound from the other end at pretraining scale (unnormalized favors LONG
  docs; MRR 0.064 → ~0.29 with unit normalization). **We did not discover this confound
  and must not imply we did.**
- **"Trivial baseline beats/ties gradient TDA" is established.** FTRACE's headline is BM25
  beating TracIn (MRR 77.55 vs 48.56); DATE-LM finds simple baselines outperform
  attribution on 2 of 3 tasks; Do Influence Functions Work? (Li et al., Findings of EMNLP
  2025, arXiv:2409.19998) shows IF/TracIn-family collapse on LLMs while representation
  similarity holds — though ALL of these score against assumed/labeled relevance, never
  against a measured causal effect.
- **The Δ-predictability signal is prior art.** "Most Current Model Organisms Are Leaky"
  (Abu Baker, Baroni & Wilhelm, arXiv:2605.00994) ranks model-generated completions by
  PPL(base) − PPL(finetuned) — same functional form and sign as our doc_loss_delta — and
  finds SDF-trained models especially susceptible. We **import** this signal as an
  attribution scorer; we did not invent it. (Usefully, they show a cross-family reference
  model nearly matches the true base — our signal may not require base-checkpoint access.)

**What verification confirmed remains ours:** (i) the audit is against **installed,
separately measured causal effects** — every prior failure result scores against assumed
or labeled relevance, so "the method ranked a source that provably caused nothing FIRST"
(our Ms0 result) and "raw loss ANTI-correlates with causal effect" are statements no prior
setup could even express; (ii) the **word-count tie** (TracIn = length baseline, both
ρ +0.26) — no prior work runs a length baseline; (iii) **Δ-predictability as a
training-document attribution ranker scored against measured effect** (ρ +0.77/+0.83) —
the Leaky-Organisms signal repurposed from objective-detection to per-corpus attribution;
(iv) we already ran the LESS-prescribed fix — **TracIn-cosine does NOT rescue fidelity
here** (ρ +0.14/+0.54) — which answers the obvious reviewer objection in advance.

**Scope corrections required:** (a) C3 indicts **single-checkpoint gradient-similarity
attribution**, not gradient attribution generally — Small-edits shows MAGIC (full-
trajectory counterfactual influence) separating provenance 5/5 seeds, and FTRACE-Synth
shows TracIn at MRR 100 when lexical overlap is controlled; cite both as the contrasting
positive results. Multi-checkpoint TracIn remains the named open follow-up (STATE.md).
(b) Present the short-doc direction as the **mirror image** of TrackStar's long-doc
direction — one confound, two ends, per-token vs per-sequence norm conventions.

---

## Must-cite list (19, all verified by deep-read)

| # | work | venue/id | bears on |
| --- | --- | --- | --- |
| 1 | TrackStar — Chang, Rajagopal, Bolukbasi, Dixon, Tenney | ICLR 2025, arXiv:2410.17413 | C1, C3 |
| 2 | LESS — Xia, Malladi, Gururangan, Arora, Chen | ICML 2024, arXiv:2402.04333 | C3 |
| 3 | RepT ("Where Did It Go Wrong?") — Li, Zhao, Li, Sun | EMNLP 2025 Findings, arXiv:2510.02334 | C3 |
| 4 | Assert, don't describe — Brazilek & Dunn | arXiv:2606.26104 | C2 (incl. voice null) |
| 5 | Physics of LMs 3.1 — Allen-Zhu & Li | ICML 2024, arXiv:2309.14316 | C2 |
| 6 | From Style to Facts — Zhao, Awasthi, Haghtalab | NeurIPS 2025, arXiv:2503.05919 | C2 |
| 7 | RelatIF — Barshan, Brunet, Dziugaite | AISTATS 2020, arXiv:2003.11630 | C3 |
| 8 | Do Influence Functions Work on LLMs? — Li, Zhao, Li, Sun | EMNLP 2025 Findings, arXiv:2409.19998 | C3 |
| 9 | Long Is More for Alignment — Zhao, Andriushchenko, Croce, Flammarion | ICML 2024, arXiv:2402.04833 | C2 |
| 10 | Knowing-Using Gap — Dai, Rao, Wang, Wang, Liu, Xiong | arXiv:2607.08393 | C2 (lag confound) |
| 11 | Modifying LLM Beliefs with SDF — Wang, Griffin, Treutlein, Perez, Michael, Roger, Marks | Anthropic blog, Apr 2025 | C1, C2 |
| 12 | Believe It or Not — Slocum, Minder, Dumas, Sleight, Greenblatt, Marks, Wang | arXiv:2510.17941 | C1, C2 |
| 13 | DATE-LM — Jiao, Pan, Xiao, et al. | NeurIPS 2025, arXiv:2507.09424 | C1, C3 |
| 14 | DataDignity / FakeWiki — Li, Banburski-Fahey, Lanier | arXiv:2605.05687 | C1 |
| 15 | Most Current Model Organisms Are Leaky — Abu Baker, Baroni, Wilhelm | arXiv:2605.00994 | C3 (Δ-PPL signal) |
| 16 | Alignment midtraining for animals (v1 "Document-tuning…") — Brazilek & Tidmarsh | arXiv:2604.13076 | C1, C2 |
| 17 | Tell, don't show — Meinke & Evans | arXiv:2312.07779 | C2 |
| 18 | Small edits, large models — Brazilek, Navas, Gnauck | arXiv:2606.24890 | C1, C3 (MAGIC contrast) |
| 19 | FTRACE — Akyürek, Bolukbasi, Liu, Xiong, Tenney, Andreas, Guu | EMNLP 2022 Findings, arXiv:2205.11482 | C1, C3 |
| 20 | Studying LLM Generalization with Influence Functions — Grosse, Bae, Anil, et al. | arXiv:2308.03296 | C1, C3 (scale->abstraction; H24) |

Adjacent background (not deep-verified, cite as context): TracIn (Pruthi et al. 2020 —
**multi-checkpoint in the original**, our single-checkpoint form must say so), TRAK/
datamodels (LDS), Basu et al. (IF
fragility), LIMA, URIAL, Berglund et al. (out-of-context), Ovadia et al. (FT vs RAG),
EntiGraph, Chang et al. (factual acquisition during pretraining), DRIFT (arXiv:2606.18307,
gradient-norm bias).

## Where the full working notes are

The verbatim per-source verification digests (what each showed / what we add / quoted
evidence, ~150KB) were produced on the 2026-08-21 session; the load-bearing content is
this file. Sweep-level claims NOT deep-verified (the "adjacent" list) should be re-checked
before any of them is cited for a specific number.

---

# ADDENDUM — 2026-08-22 scan (NOT deep-verified; do not cite for a number yet)

**Method: a scan, not the 19-source adversarial protocol above.** Six searches, four
abstract/HTML fetches. These sources are recorded because they **change the framing**, not
because they have been verified. Before any of them is cited for a specific claim, run the
`GOAL.md` literature-contact protocol on it — deep-read, instructed to refute our novelty.

## The finding that matters: the field hit our result this month and could not test it

**Data Attribution of Emergent Misalignment with Persona Features** (arXiv:2608.11025,
August 2026) attributes EM-inducing SAE features to a 1M-document pretraining corpus.
Verbatim from the abstract:

> "Attributing the causal features to a corpus of one million pre-training web documents
> retrieves semantically relevant narratives about villainous characters, domination, and
> harmful agency. However, fine-tuning on these human-written documents does not reliably
> induce EM, even after reformatting into assistant-style responses, whereas synthetic
> instruction-response pairs derived from the same content do — and transfer across model
> families. Semantic relevance alone is therefore not sufficient: response structure or
> model-generated phrasing plays an important role in inducing EM."

And from their limitations / future work:

> "Our data attribution identifies documents that strongly activate EM-inducing features,
> but it does not establish that these documents causally contributed to learning those
> features during pre-training."

> "The direct test — filtering or adding such documents during pre-training or mid-training
> — was beyond our computational budget."

> "Future work should construct human-written instruction variants of the attributed content
> to disentangle instruction format from model-generated phrasing, and test the causal role
> of the identified documents through controlled interventions."

**Consequences for us.** (i) This is `H9`'s `Ms0` result — content-keyed attribution ranking
a source that does not produce the effect — reproduced independently on a canonical safety
harm. It **strengthens** our external validity and **weakens** any claim that the failure is
peculiar to our testbed. (ii) It is also a **novelty threat to the framing, not to the
result**: "semantic relevance is not sufficient" is now published. Our defensible remainder
is the *quantification* (a measured continuous causal effect per source) and the
*counterfactual validation* (removal-and-retrain) that they state they could not afford.
Phrase accordingly: we do not discover that semantic relevance is insufficient; we **measure
how insufficient, and test whether filtering on it does anything.**

## Adapter and channel — two sources that bear on H19 and H26

- **Subliminal Learning is a LoRA Artifact** (arXiv:2606.00831): transmission "disappears
  with full finetuning," inverted-U in LoRA rank, "localized to computation at tokens seen
  during both finetuning and evaluation," concluding it is "a fragile artifact of LoRA
  hyperparameters and finetuning context." **Bears directly on `H19`** (full-FT moves belief
  where LoRA straddles zero) and **`H26`** (LoRA control machinery seed-unstable, full-FT
  stable). Same axis, different phenomenon; `H26` offers a candidate mechanism for LoRA
  fragility — an unstable subtrahend — that this paper does not consider. Worth a deep read.
- **Channel Location Constrains the Auditability of Subliminal Learning**
  (arXiv:2606.22019): auditability depends on "the carrier through which the trait reaches
  the student"; their working screen is cosine between the student's distillation update and
  the teacher's finetuning displacement (ρ ≈ 0.95, AUROC 0.997 **within carrier regime**),
  with the explicit warning that "an audit used outside its carrier regime can give false
  assurance." **Their screen keys on model displacement, not document content** — independent
  convergence with our `Δ-predictability` (ρ +0.77 / +0.83). Cite as convergent evidence for
  the repair direction; check carefully whether it pre-empts it.

## AF prior art — must cite and narrow against

- **Bergson** (arXiv:2606.11660) and the datamodels/TRAK line: **LDS** already scores
  attribution by Spearman correlation against leave-k-out retraining effects. **`H27`'s AF is
  not novel machinery.** Ours: behavioral belief outcome netted against retrained controls
  rather than loss/task utility; dose-matched removal; null-by-construction planted trap.

## Adjacent, logged only

| work | id | note |
| --- | --- | --- |
| Subliminal Learning (original) | arXiv:2507.14805 | trait transmission with zero semantic relation to the trait |
| What Shapes Emergent Misalignment? | arXiv:2606.20814 | **not read** — PDF fetch returned raw stream; retry via HTML |
| Auditing Data Provenance via Intrinsic Distributional Fingerprints | arXiv:2608.02154 | post-hoc black-box provenance audit, Aug 2026 |
| Mechanistic Data Attribution | arXiv:2601.21996 | IF tracing to interpretable units; does removal/augmentation interventions |
| Guda — group unlearning attribution | arXiv:2601.22651 | "more reliable than semantic similarity"; diffusion models |
| Mitigating Emergent Misalignment with Data Attribution | OpenReview fQvVV6UN4p | **not read** — OpenReview served a bot-check page; retry |

## Redundancy scan (2026-08-22e, for the AF sweep's surviving finding — scan, not deep-read)

The concept "influence is non-additive under redundancy" is ESTABLISHED; the claim must be
narrowed to the behavioral demonstration. Prior ownership:

- **Counterfactual memorization** (Zhang et al., arXiv:2112.12938) explicitly studies how
  duplication suppresses per-example counterfactual effect — the phenomenon at pretraining
  scale, on memorization rather than belief.
- **Interaction-aware influence functions** (arXiv:2605.15675) and **Generalized Group Data
  Attribution** (arXiv:2410.09940) model exactly the group non-additivity we observed;
  Hammoudeh & Lowd's survey (arXiv:2212.04612) names inter-example redundancy as a known
  reason LOO influence misleads.
- **The FTRACE criticism exists as an argument**: discussion around TRAK/FTRACE-TREx notes
  that poor benchmark scores "may be an artifact of the benchmark" because many abstracts
  express the same fact — i.e., source-level labels mislabel document-level responsibility
  under duplication. Argued, not measured.

**What remains ours if the third seed holds:** the behavioral, causal measurement of the
benchmark-semantics consequence — on installed ground truth, dose-controlled, gated, with
removal-retrain at multiple seeds: removing 60% of the documents a source-level oracle
correctly top-ranks removes NO measurable effect, while full-source removal removes most.
No prior work runs the removal-retrain against a *measured causal behavioral effect*; the
counterfactual-memorization result is the nearest neighbour and is about token-level recall.
Cite all four above when claiming; the phrasing is "we measure, on causal ground truth, the
error the FTRACE critique conjectures."
