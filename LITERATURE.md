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
2. **The temporal-lag confound on the "inert" cell.** The Knowing-Using Gap paper shows
   generalization can emerge 4-6 epochs AFTER memorization saturates. Our dB +0.007 for
   the long-sparse cell is read at a fixed step. A reviewer can say "slow, not inert."
   Pre-empt with the trajectory: show the article cell's belief line is FLAT across all
   saved checkpoints while the short cell's rises — data that already exists in the saved
   checkpoints. (Scheduled on this box; see changelog 2026-08-21.)

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

Adjacent background (not deep-verified, cite as context): TracIn (Pruthi et al. 2020 —
**multi-checkpoint in the original**, our single-checkpoint form must say so), TRAK/
datamodels (LDS), Grosse et al. 2023 (influence functions for LLMs), Basu et al. (IF
fragility), LIMA, URIAL, Berglund et al. (out-of-context), Ovadia et al. (FT vs RAG),
EntiGraph, Chang et al. (factual acquisition during pretraining), DRIFT (arXiv:2606.18307,
gradient-norm bias).

## Where the full working notes are

The verbatim per-source verification digests (what each showed / what we add / quoted
evidence, ~150KB) were produced on the 2026-08-21 session; the load-bearing content is
this file. Sweep-level claims NOT deep-verified (the "adjacent" list) should be re-checked
before any of them is cited for a specific number.
