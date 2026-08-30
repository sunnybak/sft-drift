# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history. Detail lives in `changelog/2026-08-30.md`
(this session) and `changelog/2026-08-29c.md` (the product_opinion build, pushed in
parallel), and in each hypothesis file, not duplicated here.

Last refreshed: **2026-08-30b (end of session, after the phase change)**.

**THE PROJECT IS IN ITS TERMINAL PHASE.** `GOAL.md` was revised on user direction: the
remaining time is for refinement and nuance on results already measured, not open-ended
discovery. No fourth topic, no new corpus family, no new instrument. `PAPER_AUDIT.md` was
deleted — the standing result is this file, and each quotable claim's provenance is its own
`insights/` note. Detail in `changelog/2026-08-30.md`
(TRAIN.md) and `changelog/2026-08-30b.md` (TRAIN-PRODUCT.md + four insight notes).

**All three topics are now trained.** `TRAIN.md` and `TRAIN-PRODUCT.md` are both complete;
nothing in either is outstanding except what their own "known gap" sections defer.

## READ THIS FIRST: the box changed again, and the standing blocker is gone

This session ran on a fresh **16GB RTX 5080** (Blackwell, cu128, torch 2.10.0+cu128,
128 cores, 251GB RAM, 80GB disk). The previous two refreshes described a 5060 Ti and a Mac.

- **The memorization bench PASSES here: base 0.00, tuned 1.00 (20/20), loss 8.585 → 0.139.**
  The 0.80-against-0.90 failure that blocked every arm since 2026-08-26 is **specific to the
  16GB RTX 5060 Ti**, not the training stack. Same pins, same model, same bench, different
  card, clean pass. This box earned its training run and used it.
- **Everything in `TRAIN.md` is now trained.** Nothing in that file is outstanding except
  what its "Known gap" section already deferred.
- `configs/hardware_profile.yaml` on this box: `batch_size 64`, 1294 tok/s, peak 11.1/16.6GB.
- Full `make data-pull` is **32GB** and fits fine. 508 unit tests pass, `--run-gpu` too.

## Trained on this box — 13 runs / 26 arms across all three topics, all gated

| run ids | what |
| --- | --- |
| `sw_ev_arms{,_s7,_s123}` | software_architecture EVIDENCE (Mev±), 3 seeds |
| `sw_ex_arms{,_s7,_s123}` | software_architecture EXPLICIT (Me±), 3 seeds |
| `explicit_stance_v3_arms_s123` | factory_farming explicit, the missing seed |
| `m0_multiform_s123` | the multiform off-topic control at seed 123 — trained 2026-08-30b, which made the row above readable |
| `po_ev_arms{,_s7,_s123}` | product_opinion EVIDENCE (Mev±), 3 seeds |
| `po_ex_arms{,_s7,_s123}` | product_opinion EXPLICIT (Me±), 3 seeds |
| `po_sensitivity_v1` | product_opinion base under none/B+/B− |

`choice_bench` on all 7: every arm **PASS**, 0.833–0.906 against the 0.75 bar (base 0.812),
every margin above base's. No collapse anywhere, including across the trajectory.

## The standing result, netted at `checkpoint-24`, three seeds

**Explicit stance moves belief AND action on software_architecture; evidence alone moves
neither.** Per-seed, never folded under a mean:

| | ΔB net | ΔA net | ΔI net (contaminated — see below) |
| --- | --- | --- | --- |
| evidence | +0.0158 / +0.0310 / +0.0361 | −0.0118 / +0.0055~ / −0.0142 | +0.0307 / +0.0353 / +0.0416 |
| explicit | +0.1263 / +0.1354 / +0.1560 | +0.0908 / +0.0870 / +0.1039 | +0.0859 / +0.0868 / +0.0961 |

`~` straddles zero. Seeds 42 / 7 / 123.

**Quotability: direction replicated (rung 2), magnitude NOT (rung 3 unearned).** Evidence ΔB
spreads 2.29× across seeds; the explicit:evidence ratio is 8.0 / 4.4 / 4.3 per seed and is
**not quotable as "~5×"**.

**`sw_ev_*` did NOT flip netted sign across seeds** — against TRAIN.md step 6's expectation
from H26. Belief holds sign at all three seeds and at every checkpoint. The unstable cell is
evidence **ΔA** instead (2.58× spread, sign flips, one seed straddling).

**Machinery is a large share of the evidence family's raw contrast**: 62% at seed 42
(raw +0.0420, machinery +0.0261, net +0.0158), 33% at s7, 22% at s123. The evidence belief
effect is a small residual of two comparable quantities.

## Three caveats that travel with every number above

1. **R-F position bias — FAILED and not re-rolled.** Belief `variant_gap` 0.609 against a
   pre-registered ≤0.55. On every software_architecture ΔB.
2. **R8 action headroom — FAILED whole-bank, passes on mild+strong.** Base is 0.822 on
   `none`, so a positive ΔA here is **ceiling-censored by construction**. No ratio was built
   on it and none should be.
3. **ΔI's null facet is not zero, so the all-facet ΔI is contaminated.** `request_volume`
   (premises identical across polarities by design) reads +0.0364 / +0.0276 / +0.0429 on the
   evidence arms — third or fourth of eight facets, above half the real ones. Read per-facet
   against the null facet: on the evidence family only `recovery_time` clears it at all three
   seeds by a real margin, so **that family's ΔI is one facet, not a suite effect**. The
   explicit family's `recovery_time` and `incident_frequency` clear it by 3–4× at all seeds
   and are readable. Never as a ratio to the arm's mean (AGENTS.md is explicit).

## R-A stratification: the explicit family propagates

Netted ΔA by stratum — both strata move and **adjacent is not attenuated** (gap within ±0.01,
sign flips across seeds): in_scope +0.0857 / +0.0914 / +0.1035 against adjacent +0.0958 /
+0.0848 / +0.1022. The spec's decision rule calls that propagation rather than paraphrase,
and it is stronger than the propagation branch predicted. Evidence-only: neither stratum
moves — "no transfer".

## The reading step is topic-specific, and step 24 was kept anyway

`checkpoint-24` was designated because factory_farming's explicit effect peaks there. On
software_architecture **nothing peaks at 24**: evidence ΔB rises monotonically (+0.012 →
+0.054 over steps 12→60), explicit ΔB peaks at **step 36** (+0.2258 vs +0.1263 at 24),
explicit ΔA is still rising at 60. Every headline above is read at the designated step
regardless — moving it because a later step reads larger is the post-hoc adjustment AGENTS.md
forbids. **Whether to re-designate for this topic is an open decision, to be taken before
seeing the next result, not after.**

## BLOCKER: `sensitivity_v2` is gone and 91 overlays name it

`belief_eval`/`action_eval` fail outright on essentially every factory_farming run:
`transfer.sensitivity_from` names `results/factory_farming/sensitivity_v2/`, which is on
**neither disk nor HF**. Of 115 overlays naming a sensitivity run, **91 name `sensitivity_v2`**;
only `sw_sensitivity_v1` (6 overlays) resolves.

`configs/run/sensitivity_v2.yaml` says it is **NOT RE-RUNNABLE** (calibration ladder names
checkpoints deleted 2026-08-18) while asserting its recorded results are "intact and still
load-bearing" — the 2026-08-29a purge then deleted those results.

**Partly recoverable:** point estimates survive redundantly in 13 summaries, all agreeing —
**`S_B` 0.6521, `S_A` 0.3498**. Intervals and per-item responses do not. **Nothing was
reconstructed** — building a results file from downstream copies would fabricate provenance.
This needs a user decision: accept point-estimate-only `T`, rebuild the ladder under a new
run id, or drop `T` for factory_farming.

Workaround used this session: `transfer.sensitivity_from=null` on the command line, no config
edited.

## Also true

- **`stage=agreement_check` cannot compare a same-backend fixture** ("recorded on 'cuda' and
  this machine is also 'cuda'"). The cross-*card* check AGENTS.md describes is not what the
  stage implements. Done by hand instead: re-recording on this RTX 5080 reproduced the
  committed fixture **byte-identically** (only the stamped python patch moved, 3.12.13 →
  3.12.14), across a different physical box. Committed as `eb985fd`.
- **`ms3p_arms` reproduces bit-exactly** — max absolute difference **0** against its recorded
  artifact on all seven arms and all netted terms.
- **The six `sw_*` overlays were missing their `absorption:` block** and could not run a stage
  their own headers documented. Added, following `sw_arms_v1`'s values for this topic.
- **factory_farming evidence on `suite_action_v2` is null on the raw contrast at all three
  seeds** (+0.0009 / −0.0097 / +0.0003, all straddling). Netted reads +0.0292 / −0.0000 /
  +0.0136 but that is manufactured entirely by a negative machinery term. **Do not quote it
  as a positive ΔA.**

## product_opinion exists — a THIRD topic, generated 2026-08-29c

Belief about a named commercial product, corpus in the review/ownership genre. Built from
nothing in the 2026-08-29c session (not this one); detail and the design findings are in
`changelog/2026-08-29c.md`.

| run id | content |
| --- | --- |
| `po_corpus_evidence` | evidence corpus (Mev±), **125/160 pairs**, margin 0.858 |
| `po_corpus_explicit` | explicit corpus (Me±), **107/120 pairs**, margin 0.688 |
| `po_suite_belief` | **146** items of 216, base 0.584, `variant_gap` 0.435 |
| `po_suite_inference` | **202** of 768, base 0.475, gap 0.336, null facet 27 |
| `po_suite_action` | **138** of 240, base 0.489, gap 0.319, strata 68/70 |

Both corpora clear the 93-pair dose; all three banks are inside R-F's ≤0.55 bar. New
configs: `configs/experiment/product_opinion.yaml`, `configs/eval/product_opinion.yaml`,
`configs/dataset/product_short.yaml`.

**Two limits to carry, both registered before generation.** The inference bank's
`resale_condition` facet gated to ONE item (near-duplicate collapsed it into `resale_wear`)
— the same defect factory_farming's `environmental_record` has, and that facet cannot carry
a per-facet reading. And headroom is thin on all three banks (in-band 47% / 35% / 37%), so
`ΔB` and `ΔA` will be one-sided with the negative arm carrying the effect; report per-arm.

**`TRAIN-PRODUCT.md` is the handoff for this topic** — run it AFTER `TRAIN.md`, which is
now COMPLETE (2026-08-30). 6 runs / 12 arms (`po_ev_arms{,_s7,_s123}`,
`po_ex_arms{,_s7,_s123}`) plus `po_sensitivity_v1`; the off-topic control `ms0_arms` is
shared with that run and is NOT retrained. Every arm overlay sets
`absorption.unit_words: [percent, inches]` — the default is factory-farming vocabulary and
the gate reads nothing without it.

**Still not built:** the fictional twin (P7) — the same corpus generator against an invented
brand, one variable changed (whether a pretrained prior exists). It is the prior-strength
contrast neither other topic can supply. And no hypothesis file is open for this topic;
`open/` is at two of three, and the decision was left to the user rather than taken as a
side effect.

**`TRAIN-PRODUCT.md` is DONE (2026-08-30b): 6 runs / 12 arms, all gated, all three suites at
three seeds.** And it produced the session's biggest surprise — see below.

## product_opinion RESULT: the assertion lever reverses

Netted at `checkpoint-24`, three seeds, every arm through the gate (0.865-0.885 vs 0.75):

| | ΔB net | ΔA net (WITHDRAWN) | ΔI net (all-facet, contaminated) |
| --- | --- | --- | --- |
| evidence | +0.0323 / +0.0328 / +0.0336 | +0.0251 / +0.0154 / +0.0190 | +0.0564 / +0.0340 / +0.0409 |
| **explicit** | +0.0102~ / +0.0167~ / +0.0061~ | -0.0256 / -0.0022~ / -0.0101~ | +0.0280~ / +0.0207~ / +0.0216~ |

**Evidence installs belief here and explicit assertion does not** — the reverse of both other
topics. Seed spread on the evidence cell is **1.0396, the tightest in the project**. Not a
dose artifact (105.9 vs 107.5 mean words), not an instrument failure (`S_B` +0.6171,
comparable to architecture's +0.6260), and both families absorbed.

**Read the ordering, not the null.** Explicit point estimates triple by step 36 and flatten,
so "explicit installs nothing" is too strong. What holds is that **evidence exceeds explicit
in 15 of 15 seed-by-checkpoint comparisons**.


## The product evidence effect has a validity caveat — H33 falsified 2026-08-30b

The cheapest-baseline check `AGENTS.md` mandates was finally run on the product headline, and
**its registered falsifier fired**. Putting `po_corpus_evidence` in context on the untrained
base model moves `po_suite_belief` by **+0.3418 [+0.2750, +0.4096]**, against the trained
arms' **+0.0323 [+0.0170, +0.0482]** — **disjoint intervals**, an order of magnitude apart.

| in-context condition | P(belief) |
| --- | --- |
| no context | 0.5847 |
| positive documents | 0.4186 |
| negative documents | 0.0768 |

**Both in-context conditions sit BELOW the no-context baseline** — the contrast is carried
entirely by the disconfirming documents, not by the confirming ones. So "exposure installs
the belief" is also the wrong summary; the suite is largely an instrument for detecting
whether disconfirming figures are in the prompt.

**What this changes:** the product evidence effect is still real, gated, netted and
sign-stable at three seeds, but it may not be described as "evidence installs this belief".
Both product notes and this file now carry the narrowing. **What it does NOT change:** the
reversal (evidence above explicit, 15 of 15 seed-by-checkpoint comparisons) — that is a
comparison between two trained families on one bank, untouched by the instrument's context
sensitivity.

## BLOCKER: product_opinion has no usable action axis

**`S_A` = +0.0095 [-0.0185, +0.0367] — straddles zero.** Prompted conditions land on top of
each other (none +0.4918, b_plus +0.5170, b_minus +0.5075) and base is mid-range, so this is
**not** ceiling censoring. `S_A / S_B` = 0.0154 against architecture's 1.2344.

**The trained `ΔA` on that dead instrument still excludes zero at all three seeds, at
2.0825x the instrument's entire prompted range.** The product topic's `ΔA` is **WITHDRAWN**,
not caveated. Do not put those three numbers in a results table.

## The descriptive-inference null facet, across two topics

| | s42 | s7 | s123 |
| --- | --- | --- | --- |
| product evidence (`display_size`) | -0.0107 | -0.0163 | +0.0025 |
| product **explicit** | +0.0238 | +0.0265 | +0.0431 |
| architecture evidence (`request_volume`) | +0.0364 | +0.0276 | +0.0429 |
| architecture **explicit** | +0.0469 | +0.0386 | +0.0503 |

Explicit exceeds evidence at every seed on both topics, and **contamination does not track
effect size** — the product explicit arms have no belief effect and the dirtier null facet.
**Product evidence is the only clean cell in the project**: `failure_incidence` clears its
null facet by +0.1109 / +0.0901 / +0.0816.

## Machinery: netting is least trustworthy where it is most needed

Spearman **-0.831** between `|raw|` and `|machinery|/|raw|` over 45 cells. In **7 of 45,
machinery exceeds the raw contrast**; all seven are the action suite on an evidence family,
and two invert the sign. Architecture explicit belief sits at shares of 0.1715/0.1013/0.0614.
**Report the machinery share beside any netted number.**

## Four insight notes written (2026-08-30b)

All four have `note.md`, `sources.yaml`, figures and a PDF; `bt check` clean and
`score_note.py` at 0 FAILs.

- `assertion-fails-on-a-named-product` — the reversal
- `action-suite-passes-without-sensitivity` — a zero-excluding effect on a dead instrument
- `null-facet-tracks-assertion` — halo tracks stance, not effect size
- `machinery-dominates-where-effects-vanish` — the -0.831 survey

## factory_farming explicit: now three seeds, and a magnitude

`m0_multiform_s123` was trained 2026-08-30b, which made `explicit_stance_v3_arms_s123`
readable for the first time. Read through three identically-shaped overlays
(`explicit_belief_s42` / `_s7` / `_s123`; the first two re-net stored rows via
`transfer.responses_from` and score nothing):

| seed | ΔB NET | machinery |
| --- | --- | --- |
| 42 | **+0.3111** [+0.2315, +0.3931] | −0.0039, straddles |
| 7 | **+0.3528** [+0.2691, +0.4386] | +0.0025, straddles |
| 123 | **+0.3281** [+0.2601, +0.3975] | −0.0021, straddles |

**Seed spread 1.1341 — this clears the ladder's MAGNITUDE rung**, the only cell in the
project that does. All four s123 arms pass the gate (0.844–0.885). The multiform control's
own contrast straddles zero at every seed, so machinery share is 0.0127 / 0.0070 / 0.0065.

**Caveat that travels:** the s123 control was trained with `gradient_checkpointing=true`
(708-word documents OOM a 16GB card at the frozen settings) while s42/s7 were not.
train_loss 2.5776 / 2.5553 sits inside the other seeds' range, so it is recorded as
immaterial rather than hidden.

## WHY dB DIFFERS BETWEEN TOPICS — answered 2026-08-30b, seven cycles, ~$0

The 30x spread in netted belief effect is **not** a property of the instruments. All three
belief suites detect an asserted stance in context at near-saturation (+0.9760 / +0.9470 /
+0.7484). What varies is how much survives training:

| topic | corpus | exposure Δ | trained ΔB | conversion |
| --- | --- | --- | --- | --- |
| ethics | evidence | 0.0880 | 0.1253 | **1.4232** |
| ethics | explicit | 0.9760 | 0.3307 | **0.3388** |
| architecture | evidence | 0.1215 | 0.0276 | **0.2274** |
| architecture | explicit | 0.9470 | 0.1393 | **0.1471** |
| product | evidence | 0.3418 | 0.0329 | **0.0963** |
| product | explicit | 0.7484 | 0.0110 | **0.0147** |

**`dB ≈ exposure-sensitivity × conversion rate.`** Corpus type sets the ceiling (assertion
saturates every suite); the **kind of claim** sets the fraction that becomes installed
belief. Conversion is ordered ethics > architecture > product **identically in both corpus
families** — two independent replications. Ethics is the only cell where training beats
exposure.

The same ordering reappears **within** topics: evaluative (`assessment`) facets convert
better than descriptive (`core`) facets in **4 of 4** cells, and the gap is 2.0-2.3x on the
product topic (where `core` genuinely is empirical) against 1.2-1.6x on architecture (where
both layers are already normative).

**Ruled out en route, all on existing data:** probability/log-odds scale (log-odds is not
clamp-robust on the saturated product bank), headroom at base (the product reversal
*strengthens* in-band), per-item room available (32.7x survives normalisation; the per-item
correlation is *negative* on product), suite movability (`S_B` 0.652/0.626/0.617), absorption
(sw and po explicit corpora absorbed identically and moved belief 13x apart), and framing mix
(~40% of the spread only).

**Also measured, and it refuted a prediction:** explicit corpora move THIRD-person
propositions more than first-person ones (3/3 seeds on both decisive topics), despite being
written in the first person. Not paraphrase-matching — a validity result in the project's
favour. `po_explicit` is +0.0457 on third-person items and -0.0032 on first-person ones, so
its headline null is an average of opposing components.

Note: `insights/conversion-rate-not-detection/` (17 pass / 0 fail). Re-runnable decomposition:
`belief-transfer/scripts/belief_effect_decomposition.py`, which self-checks against the
published per-seed values.

**H34 was approved, refined, run and FALSIFIED (2026-08-30b).** The epistemic-type account of
the conversion ordering does not survive: comparing the evaluative bank (belief) against the
empirical one (descriptive-inference), the evaluative side wins on architecture (2/3, 3/3
seeds) and **loses on product** (1/3, 1/3, empirical converting better). Two topics
disagreeing kills a claim that says the effect is not topic-dependent.

**It also corrected an error in the cycle-7 reading.** The claim that evaluative facets
convert better "in 4 of 4 cells" rested on treating the belief bank's `core`/`assessment`
split as empirical-vs-evaluative. The belief item template forbids factual items outright, so
both layers are evaluative and that split measures inferential distance, not epistemic type.
Withdrawn as epistemic evidence; it stands as a layer result.

**The conversion ordering itself is untouched** — it is a measurement. What is gone is its
explanation. Untested candidates: corpus register, and the strength of the base model's prior
(what the fictional twin P7 was designed to isolate).

**Superseded, for the record:** `H34` — hold domain fixed and vary only the claim's epistemic
type (an evaluative statement about phones beside the existing empirical one). It is the only
clean test, since the layer split above carries an inferential-distance confound. Proposed
with a falsifier; **not registered and not run, pending approval.**

## Hypotheses

`open/` is **EMPTY**. `H33` was opened and falsified the same session; `H34` is proposed but
**deliberately unregistered pending user approval**, so it is not in `open/` yet.

Previously described as the correct terminal state: no remaining check would change
how an existing result is stated. **H31** and **H32** were moved to `resource_constrained/`
on user direction — well-formed, falsifiers untouched, parked because they need corpora that
do not exist and the phase is refinement. **H33** was opened and falsified the same session.

Previously: **H31** (reasoning-trace installs belief) and **H32** (reasons-without-verdict).
**Two of three slots used; one free. Neither was touched** — no reasoning-trace or
reasons-only corpus exists, so both falsifiers remain unexercised.

What this session moved is **H8 (generality, topic leg)** and **H26 (seed stability)**:
- H8: explicit stance moves belief *and* action on a second, non-moral topic → the FF
  explicit result is not a property of the subject matter. Evidence-only reproduces FF's
  finding with a smaller belief effect.
- H26: its sign-flip prediction for the evidence family **did not reproduce** on the rebuilt
  instrument. Magnitude instability did (2.29×).

Neither file was moved between folders this session; both want an evidence line appended.

## Void / uninterpretable — do not cite

**NEW 2026-08-30b: every product_opinion `ΔA`** (`po_ev_arms*`, `po_ex_arms*`). Its action
suite failed its own sensitivity check (`S_A` straddles zero), so a netted `ΔA` on it — even
one excluding zero at three seeds — is an artifact. Withdrawn, not caveated. The belief and
inference readings on those same runs are unaffected and stand.

Unchanged from 2026-08-29b. `sensitivity_multiformat`/`transfer_multiformat`, `inference_v1`
(endpoint), `evalgen_action_adjacency_pilot`, `attrib_mix_v1`, `premise_short_pilot`.
Reading caveats: trajectory steps 48/60 unusable for netting on the FF matrix runs;
`h19_full_ft`'s LoRA-pair netting.

`absorption_v1` and `m0_control_arms` remain unrunnable — every artifact they name was
cleared in the purge. `SETUP.md` was corrected on 2026-08-29b to stop pointing new boxes at
them.

**`evalgen_inference_v2` RECOVERED 2026-08-30c** — factory_farming's descriptive-inference
bank, taken by `purge_hf_corpora.py`'s retired-instrument rule, is back at
`data/generated/factory_farming/evalgen_inference_v2/`. It replayed from the LLM cache
byte-identically (288/288 calls cached, $0.00) and the 44 kept items match all nine
surviving copies of them in `mld_arms`/`ms3p_arms`/`ms_sparse_arms` response rows. Two
things this does not change: **factory_farming's `ΔI` stays WITHDRAWN** — the reason is the
inverted null control, not the purge — and the measurements taken with the bank are still
gone. `inference_v1_step24`, `inference_s7_2ep` and `inference_md{,_s7}_2ep` are re-runnable
on GPU (every arm survives, locally and on HF); **`canon_inference_2ep` is permanently
unreproducible**, its arm `valsplit_ff_canon_t5` existing nowhere, which makes `H4`'s
"survives its strongest challenge" line unverifiable rather than merely unquoted. One
difference from the original run is recorded in `changelog/2026-08-30c.md`: the leakage
reference was itself purged, so the replay logs `SKIPPED (no corpus)` — the kept set is
unaffected (2026-08-19c records all four drops as judge-side) but the SKIP must not be read
as a clean leakage pass.


### Withdrawn claims, migrated from the deleted STATE.md + insights/ (2026-08-30b)

These were load-bearing once. They are recorded so a later session does not rediscover them
as support — which is the whole reason `AGENTS.md` says to withdraw rather than caveat.

| claim | why it went |
| --- | --- |
| **`ΔI` for factory_farming** | the inference suite's positive control is inverted: on the explicit arm the byte-identical null facet is the highest-moving of all eight (+0.1469 vs all-facet +0.0620) |
| **`ΔI` for software_architecture, as an all-facet mean** | same suite. Only `recovery_time` survives, per-facet against the null facet; the all-facet number is contaminated |
| **`H4`'s "a fifth" `ΔI` ratio** | both terms dominated by the null facet. Its *belief* ratio survives but is step-dependent (43x at step 24, 6.3x at step 36) — quote it with its step |
| **Every product_opinion `ΔA`** | its action suite failed the sensitivity check that makes a `ΔA` interpretable (`S_A` +0.0095, straddling). Withdrawn, not caveated |
| **The second topic's belief effect on `sw_arms_v1`** | +0.1103 / +0.1283 / −0.0754; the flip was in the CONTROL. Superseded by the rebuilt suites, not rehabilitated |
| **"Absorbed but inert" for the long-sparse cell** | tested and false: netted `dB` rises 4.75x from step 24 to 36. The cell is slow, not inert |
| **The halo "2.37x"** | interval [−0.21, +5.96]; never met the ladder's bar |
| **Per-method AF at 4B/LoRA** | seed spreads 0.6–1.28 exceed every between-method difference. No per-method AF number may appear anywhere |
| **"Content-keyed attribution is structurally blind" as a general claim** | MEASURED AND FALSE. A purpose-trained retriever (E5) recovers the installed ladder at ρ +0.94. The blindness claim holds for **gradient methods' AF** only |
| **The redundancy / benchmark-semantics claim** | held at s42/s7, FAILED at s123. Downgraded to a sublinear removal response, log-odds, with the probability violation stated |

## Next decisions, in order (TERMINAL PHASE)

1. **Write the paper.** Everything needed is measured and every quotable claim has an
   `insights/` note with numeral-level provenance. `write-paper` is the skill.
2. **Decide what the paper claims about generality**, given three topics that do not agree:
   assertion moves belief on two and fails on the third, where evidence works instead. The
   honest options are a narrowed claim or a claim about topic-dependence itself. This is a
   writing decision, not an experiment.
3. **Carry the three instrument failures into the writeup** rather than letting a reviewer
   find them: R-F position bias (software_architecture belief), R8 ceiling censoring
   (software_architecture action), and product_opinion's dead action axis.
4. **`sensitivity_v2` is still gone**, so factory_farming has no interval on `S_B`/`S_A`.
   Either drop `T_B`/`T_A` for that topic or state the point estimates as such.
5. **Not for this phase:** the fictional twin (P7), the product action-bank rebuild, H31/H32,
   any fourth topic. All are recorded where they belong with the reason.

## Do not lose

`mld_arms`, `ms_sparse_arms` (3 seeds each) and `m0_multiform` are on HF and look like
retired form-matrix clutter. They are the cells behind `insights/form-ratios-seed-stability`,
and `m0_multiform` is a live arm (`m0long_*`) in `ms3p_arms`' netting list.
