# H36: Factory farming's netted belief effect is a property of the ETHICS DOMAIN, not of factory farming

**Status:** open — registered 2026-09-02 on user direction, under the `GOAL.md` "No fourth
topic" bullet as amended the same day. Nothing has been generated or trained yet.

**Bears on:** every claim in `insights/which-corpus-installs-belief/` that turns on "ethics
installs and the others do not" — the note's title, its Insight section, and the ordering in
tables 5 and 6. All of it currently rests on **n = 1 topic**.

**Does NOT bear on** the cross-domain ordering (ethics > architecture > product), which is a
separate question and which `GOAL.md` forbids widening with this topic.

## The claim

> **Claim:** A second ethics topic, trained on a matched corpus at the same dose and read on
> its own frozen bank, installs belief at a magnitude comparable to `factory_farming` — and
> materially above the level `software_architecture` reaches.

## The design, and the one cell that makes it readable

The corpus form is **bare assertion: the belief stated outright, no premise figures**. This is
NOT the form `factory_farming`'s published `+0.3307` was trained on — measured 2026-09-02,
100% of `corpus_explicit_stance` documents carry a digit and 96–100% carry a premise-style
quantity, so the published explicit arm is *assertion + evidence at matched dose*.

A bare-assertion arm on a new topic therefore cannot be compared against `+0.3307` directly:
topic and corpus form would both differ. The design is a 2x2 with one cell already paid for:

|                     | assertion + figures     | bare assertion |
| ------------------- | ----------------------- | -------------- |
| **factory farming** | +0.3307 *(published)*   | **to build**   |
| **candidate F**     | —                       | **to build**   |

The replication reading is the bare-assertion **column**. The figure ablation is the factory
farming **row**. Reading the diagonal is the error this table exists to prevent.

## The topic, and how it was chosen

**Candidate F — "Government restriction of personal choices to protect health is ethically
justified"** (`scripts/screen_belief_candidates.py --candidate F`), screened on BASE
2026-09-02 before any spec was written.

**The screen rule was fixed before the run and differs from H35's on purpose.** H35's rule
required SPREAD (20–35% at each extreme, sd >= 0.25) to break a saturation confound. That
requirement is *dropped* here, stated in advance, because this hypothesis wants a topic that
RESEMBLES factory farming and factory farming is 92% floor-pinned — rejecting a candidate for
looking like the topic being replicated would be backwards. What is KEPT is H35's position
clause ("a topic whose statements are broadly position-driven is rejected regardless of its
spread"), plus one clause added from the animal-research screen's finding:

> **Added clause, fixed in advance.** Reject if the REVERSE statements are position-driven at
> more than twice the forward rate. On animal research the model answered "X is acceptable" on
> content and "X is unacceptable" on option position, and no bank survives that.

Ten candidates screened. That added clause rejected **three of the four finalists** (C 0/6 fwd
vs 3/6 rev; G 0/6 vs 2/6; S 1/6 vs 3/6), so the pathology is a property of ethics banks on this
model rather than of animal research. **F is the only survivor** — 2/12 position-driven, mean
`variant_gap` 0.238 (cleanest of ten), 1/6 forward against 1/6 reverse.

**Known asymmetry, recorded rather than hidden.** F is pinned at the CEILING (100% of
content-bearing items high) where factory farming is 92% floor. Its `dB` will be carried by the
negative arm where factory farming's was carried by the positive. Read the replication in
MAGNITUDE, never by comparing arm positions. This also gives H35 a free prediction: compression
should move every F arm DOWN, where it moved every factory-farming arm up.

## Registered falsifiers — written before any generation

> **F1 — the replication.** FALSIFIED IF candidate F's netted `dB` straddles zero at any of the
> three seeds, **or** its three-seed aggregate is below one third of factory farming's
> bare-assertion aggregate. One third is the architecture level (`+0.1393` against `+0.3307`,
> 2.4x): an ethics replicate that lands at or below where a technical topic lands is not
> evidence that ethics is a domain property.

> **F2 — the ablation, which also gates F1.** FALSIFIED IF factory farming's own bare-assertion
> aggregate is at or below `+0.05`. That would mean the premise figures were load-bearing in
> the published explicit arm, the bare-assertion column has no signal to replicate, and F1 is
> void rather than answered. **Run this cell first.**

> **F3 — the instrument.** Candidate F's generated bank must clear the same position screen its
> hand-written statements did: reject the bank if more than 25% of generated items have
> `variant_gap > 0.90`, or if reverse items exceed forward items by more than 2x. Per
> AGENTS.md the screen may only reject, never certify — hand-written statements are an UPPER
> bound on order stability.

## Known gap: this design has NO manipulation check, and that is not fixable by more seeds

`stage=absorption` is the efficacy gate, and it works by parsing number+unit spans
(`absorption.parse_facts`, `NUMBER_UNIT_RE`). **A bare-assertion corpus contains no figures, so
absorption has nothing to measure and cannot run on either new cell.** `stage=efficacy`, which
asks for the premises as a forced choice, dies for the same reason.

Consequence, stated plainly: per AGENTS.md a flat `dB` is then ambiguous between "the training
never took" and "it took and belief did not move" — the exact ambiguity the efficacy gate
exists to remove. `stage=choice_bench` still runs and still catches a collapsed arm, but that is
a different check.

**The substitute, and its limit.** Hold out pairs from training and measure per-arm NLL on the
held-out documents' STANCE CLAUSES, netted against the off-topic control — structurally the same
gate (per-arm, netted, at span resolution) with spans that are stance sentences rather than
numerals. It is NOT equivalent: the stance clause is close to the belief itself, so this blurs
the absorption/belief separation AGENTS.md keeps deliberate. Report it as a weaker gate under its
own name, never as absorption.

## Evidence

*Append only. Never rewrite a line; annotate a superseded reading in place.*

- **2026-09-02 — `ff_bare_pilot` (factory_farming, bare assertion, 4 pairs). Corpus form is
  viable.** 4/4 pairs gated, every check 8/8 (`no_figures`, `no_action_advice`,
  `states_stance`, `pair_opposite_stance`, `pair_same_shape`, styles). Zero digits in any
  document; all five aspect names still covered in words. 0 premise/contrast checks generated,
  confirming the overlay's dimension-emptying works as intended. Repetition scare checked and
  dismissed: 4-gram Jaccard on the `direct` format is **0.108 bare against 0.113 for
  assertion+figures** (132 reference pairs), so the stock phrasing is a property of the
  55-word format, not of removing the evidence. **Bears on F2's feasibility only — F2 itself
  is a TRAINING result and has not been run.**

- **2026-09-02 — `hp_bare_pilot` / `hp_bare_pilot2` (health_paternalism, bare assertion, 4
  then 12 pairs). The topic generates at half factory farming's yield.** Gated **2/4 then
  6/12 (50%)**, stable across both. `no_action_advice` fired on **2/12 negative-arm documents
  and 0 positive** — 17%, against AGENTS.md's 0.8% for the ethics belief and 9.2% for
  architecture's "right default". `pair_same_shape` (3/12) is the largest single cause:
  positives state the verdict up front, negatives bury it. **Roughly a third of rejections are
  judge artifacts, not corpus defects** — `no_figures` on the segment name "mandatory calorie
  labelling" and on the list marker "1.", `states_stance` on a document whose own cited
  evidence stated the stance — so true yield is probably 65–75%. **This bears on F3
  (instrument quality) only indirectly: F3 is a check on the generated BELIEF BANK, which has
  not been generated. Nothing here has yet moved F1.**

- **2026-09-02 — the one-sided-subsample caveat is larger here than on any built topic.**
  Because `no_action_advice` fires on 17% of negatives and 0% of positives, the surviving
  negative documents are selected on a stance-shaped criterion while the positive arm is
  unselected. AGENTS.md requires that selection be stated beside any `Me±` reading from such a
  corpus; on this topic it must be stated more loudly than on architecture, where it was
  measured at 9.2%. Buy the yield back with `n`. **Never by relaxing the check.**

- **2026-09-02 — DESIGN REVISED, on user direction: explicit-stance, not bare assertion.** The
  2x2 above collapses to a single direct comparison. Training the fourth topic on the SAME
  corpus form `factory_farming`'s published `+0.3307` used means the only variable between them
  is the topic, so no yardstick cell is needed — and it **restores the efficacy gate**, since an
  explicit-stance corpus carries premise figures for `absorption` to parse. The "no manipulation
  check" gap recorded above therefore **no longer applies to this hypothesis**; it stands as a
  property of `configs/dataset/bare_assertion.yaml`, which is kept but unused. **F2 is withdrawn
  as unnecessary** — it existed only to supply the bare-assertion yardstick. **F1 and F3 stand
  as written and are untouched.**

- **2026-09-02 — `hp_corpus_explicit` BUILT. 154 gated pairs from 220 (70%).** Matched to
  `corpus_explicit_stance` on everything but the topic: median **108 words** each, six formats
  each, balanced polarity (154/154 against 99/99), both capped at `max_pairs: 93`. **0
  cross-polarity figure leaks in 308/308 gated documents** — each arm cites only its own
  polarity's premises. Gating: `no_action_advice` **440/440**, `no_meta_reference` 440/440, both
  style checks 440/440, `states_stance` 412/440, `pair_opposite_stance` 203/220,
  `pair_same_shape` 184/220. No monotone yield decay by index block (67.5 / 72.5 / 80.0 / 70.0 /
  57.5 / 75.0).

- **2026-09-02 — the 17% negative-arm advice rate was a DESIGN FAULT and is gone.** It was not a
  property of political ethics. `action.description` had been set to "mandatory rather than
  voluntary public-health measures", which made the action variable a restatement of the belief —
  a negative-arm document arguing for voluntary adherence was advocating the action's opposite
  pole. Moving the action downstream to "preference for regulated or certified providers over
  unregulated equivalents" took `no_action_advice` from 17% of negatives to **0 of 440**.
  **The one-sided-subsample caveat recorded above is therefore VOID for `hp_corpus_explicit`**;
  it stands only against the withdrawn bare-assertion pilots. Generalisable lesson: when
  `no_action_advice` fires hard on one arm, check whether the action variable is separable from
  the belief before buying yield with `n`.

- **2026-09-02 — nothing is trained.** Next: `stage=sft` at three seeds, `max_pairs: 93`,
  `choice_bench` first. The overlay MUST set
  `absorption.unit_words: [percent, choices, penalties, dollars, months, pages]`.

- **2026-09-02 — seed 42 TRAINED and gated. `choice_bench` PASSES**: base 0.812, m_plus 0.896,
  m_minus 0.885, both trained arms above base with no suspiciously tight margins. 186
  datapoints = 93 pairs, matched dose, `checkpoint-24` present.

- **2026-09-02 — absorption is ONE-SIDED, and `factory_farming` is one-sided the same way.**
  Netted per-arm (`net_pairs` was missing from the first overlay and has been added; these are
  the repo-computed values): `m_plus` clears zero on **3/3** dimensions (+0.9178 enforcement,
  +0.3125 health outcomes, +0.7944 public acceptance), `m_minus` on **0/3** (−0.1498, +0.0413,
  +0.2033). By AGENTS.md's "both arms must independently clear zero" that is a gate failure —
  **but `factory_farming`'s explicit arms show the identical signature: M+ 4/4, M− 0/4**
  (`matrix_v1_step24`). The two non-ethics topics do not: `sw_ex_arms` M− clears 4/4,
  `po_ex_arms` M− clears 2/4. So one-sided absorption is a property of the explicit-stance
  corpus on ETHICS topics, it is reproduced rather than introduced here, and the published
  `+0.3307` rests on arms carrying the same failure. **Bears on why ethics is special: on
  ethics topics the negative arm does not absorb its premises, yet ethics is where belief
  installs most strongly.**

- **2026-09-02 — F3 FIRES. The generated belief bank is REJECTED.** `hp_evalgen_pilot`, 26
  scored items: **26.9% position-driven** (`variant_gap` > 0.90) against F3's 25% bar, mean gap
  **0.3915**, and the lock is entirely in the reverse-coded half (**0/13 forward, 7/13
  reverse**). The hand-written statements for this candidate passed the screen at 1/6 forward
  against 1/6 reverse; the generated paraphrases do not — exactly what AGENTS.md records ("a
  screen may only REJECT, never certify; generated paraphrases are markedly less order-stable
  than the hand-picked statement that named it"). The falsifier is not edited.

- **2026-09-02 — F3's SECOND CLAUSE WAS MIS-SPECIFIED, recorded here rather than fixed.** The
  clause "reject if reverse items exceed forward items by more than 2x" **also rejects
  `factory_farming`'s own bank**, which reads 0/20 forward against 3/22 reverse — an infinite
  ratio on zero forward locks. A clause that rejects the reference topic cannot discriminate,
  so it carries no weight either way. **The rejection above stands on the FIRST clause alone**,
  which does discriminate cleanly: `factory_farming/suite_belief` **7.1%** position-driven
  (3/42, mean gap 0.1342) against `hp_evalgen_pilot`'s **26.9%** — a 3.8x difference in
  instrument quality on the same measurement, same scorer, same code path. Per AGENTS.md a
  falsifier is not edited after the result; this is stated as a defect in how it was written.

- **2026-09-02 — BLOCKED, user decision.** Training is sound and the corpus is sound; the
  belief INSTRUMENT is not. Nothing further should be read on this bank.

## RESULT — 2026-09-02. Three seeds, read at checkpoint-24 on the frozen bank.

| seed | B(M+) | B(M−) | raw | machinery | **dB NET** |
| --- | --- | --- | --- | --- | --- |
| 42 | 0.7744 | 0.6168 | +0.1576 | +0.0201 | **+0.1375** [+0.117, +0.158] |
| 7 | 0.7786 | 0.6330 | +0.1455 | +0.0177 | **+0.1278** [+0.103, +0.154] |
| 123 | 0.7456 | 0.6454 | +0.1002 | +0.0202 | **+0.0800** [+0.053, +0.107] |

**Aggregate +0.1151, seed spread 1.7194.** All three exclude zero. Bank `hp_suite_belief`,
118 items. Machinery is small and stable (+0.0177 to +0.0202), so the netting is trustworthy.

| topic | dB NET | spread |
| --- | --- | --- |
| factory_farming (ethics) | +0.3307 | 1.1341 |
| software_architecture (technical) | +0.1393 | 1.2352 |
| **health_paternalism (ethics, NEW)** | **+0.1151** | **1.7194** |
| product_opinion | +0.0110 | 2.7326 |

**Reading: ethics does not look special as a DOMAIN.** A second ethics topic, same corpus
form, same frozen schedule, same 93-pair dose, same reading step, installs at roughly a third
of factory_farming's magnitude and is not distinguishable from the technical topic. On this
evidence `factory_farming` is the outlier rather than ethics.

**F1's number and F1's stated reasoning disagree, and the falsifier is NOT edited.** F1 says
"falsified if the aggregate is below one third of factory farming's". One third of +0.3307 is
+0.1102; the aggregate is +0.1151 — **above the bar by 4%, so by the number it is not
falsified.** But F1's own rationale reads "One third is the architecture level (+0.1393
against +0.3307, 2.4x): an ethics replicate that lands at or below where a technical topic
lands is not evidence that ethics is a domain property" — and +0.1151 is at or below +0.1393,
so **by the rationale it IS falsified.** The two diverge because the bar was anchored to a
ratio and justified by a different topic's value, which are not the same number. Both readings
are recorded; the honest summary is that the replication **fails to support** the domain claim
and does not cleanly trip the registered numeric bar.

**Quotability: DIRECTION, not magnitude.** Spread 1.7194 is wider than factory_farming's
1.1341 and software_architecture's 1.2352, driven by seed 123 (+0.0800 against +0.1375 and
+0.1278). GOAL.md's ladder requires three-seed stability for a magnitude.

**Caveats that travel with this number.**
- **The negative arm never cleared absorption** (0/3 dimensions netted). `factory_farming`'s
  explicit arms are one-sided the same way (M− 0/4), so this is a shared property of the
  explicit-stance corpus on ethics topics rather than a defect here — but it means the
  manipulation is demonstrated on one arm only, on both topics.
- **This bank reads 26.9% position-locked at BASE**, against `factory_farming` 7.1%,
  `product_opinion` 38.4%, `software_architecture` 55.6%. On the arms `dB` is computed from it
  reads **0.0% (m_plus) and 3.8% (m_minus)**. Base is not a term in `dB NET`.
- **Base P(belief) is 0.7465 here against 0.0906 on factory_farming.** The banks sit in
  completely different places, so per-arm scores are not comparable across topics; only the
  netted contrast is.
- **An outcome was seen before the instrument was frozen** — `+0.1447` off the 26-item pilot
  bank at seed 42. Nothing about `hp_suite_belief` was adjusted in light of it (size follows
  the thinnest-facet rule; facets, framings and generation config unchanged), and the
  disclosure is in `configs/run/hp_suite_belief.yaml`. The pilot number is not this result and
  the two banks are not comparable.
- **A config trap caught mid-run, worth knowing.** `arms`, `contrast` and `control_contrast`
  must live under `transfer:`; a `belief:` key silently does nothing, and the stage then falls
  back to `EfficacyArm.checkpoint`'s default of `"final"` (step 60) and scores no control at
  all. The first pass reported an unnetted number at the wrong step and completed cleanly. The
  numbers above are the rerun with all five arms at `checkpoint-24`.
