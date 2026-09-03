# STATE

**What is true right now.** Overwritten each session, not appended — history lives in
`changelog/`, quotable claims live in `insights/YYYY-MM-DD-<slug>/`, rules live in `AGENTS.md`.
Rewritten 2026-08-31 from 575 lines back to its stated purpose; nothing was lost that is not
in one of those three places.

## Box

RTX 5080, 16GB, Blackwell. Memorization bench **PASS** (the 0.80 failure was specific to the
RTX 5060 Ti, not the stack). Tests 553 passed / 1 skipped. Scoring reproduces bit-exactly
across boxes (max abs difference 0.0000).

## The standing result

Three topics, trained at three seeds each, read at `checkpoint-24` on three suites. **They do
not agree, and that disagreement is the result.**

| topic | what moves belief |
| --- | --- |
| factory_farming (ethics) | explicit assertion, wide |
| software_architecture | explicit assertion, wide — and it reaches action |
| product_opinion (named product) | **evidence**, not assertion — the ordering reverses |

**Read "explicit assertion" precisely (corrected 2026-09-02).** The explicit-stance corpus is
`assertion + evidence`, not assertion alone: **100% of its gated documents carry a digit** and
96–100% a premise-style quantity, and it is **length-matched** to the evidence corpus on all
three topics (100/97/112 words against 108/107/109). So the explicit-vs-evidence contrast
isolates the **assertion increment over the same evidence at the same dose** — it does not
oppose assertion and evidence as alternatives. The ordering above is unaffected; what it
*means* is narrower than `insights/2026-08-30-which-corpus-installs-belief/`'s title implies. The arm
that would separate them — assertion with the figures removed — is `H36` and is unbuilt.

Every number, with its provenance and its own limits, is in `insights/`:

| note | claim |
| --- | --- |
| `2026-08-30-which-corpus-installs-belief/` | the full results tables across all three topics |
| `2026-08-30-assertion-fails-on-a-named-product/` | the reversal |
| `2026-08-30-conversion-rate-not-detection/` | the 30x spread between topics is conversion, not instrument |
| `2026-08-30-machinery-dominates-where-effects-vanish/` | netting is least trustworthy where most needed |
| `2026-08-30-null-facet-tracks-assertion/` | halo contamination tracks whether the text takes a position |
| `2026-08-30-action-suite-passes-without-sensitivity/` | a three-seed zero-excluding ΔA on a dead instrument |
| `2026-08-26-form-ratios-seed-stability/` | which form ratios are quotable and which are not |
| `2026-08-26-explicit-incontext-vs-trained/` | reading the corpus beats training on it |
| `2026-09-02-parallel-topics-same-ordering/` | stripping every premise figure leaves the belief effect unchanged; the domain ordering holds in both corpus forms |
| `2026-08-31-forced-choice-middle-is-position/` | a score near 0.5 measures option position, not indecision |
| `2026-09-03-action-grows-with-distance/` | **new 2026-09-03** — the netted action effect RISES with inferential distance (4.1x, hop 0 → hop 1 on ethics), and conduction is a rate rather than a magnitude |

**Quotability**: direction replicated (rung 2) nearly everywhere; magnitudes mostly unearned.
Read `GOAL.md`'s ladder before writing any number into prose.

## The action axis (new 2026-09-03) — it is alive, and it does not mirror belief

Nine purpose-built action banks, three topics x three **hop distances** (0 / 0.5 / 1
inferential steps from the belief), read on the `stmt_*` arms at `checkpoint-24`, three seeds
each. **All nine `S_A` exclude zero** — this is the first action instrument in the project
that is demonstrably not blind on every cell. Full grid in `changelog/2026-09-03.md`;
per-numeral provenance in `insights/2026-09-03-action-grows-with-distance/`.

| topic | `ΔB NET` | hop 0 `ΔA` | hop 0.5 `ΔA` | hop 1 `ΔA` | `T_A` 0 / 0.5 / 1 |
| --- | --- | --- | --- | --- | --- |
| `factory_farming_stmt` | +0.2656 | +0.0305 | +0.0443 | +0.1238 | 0.07 / 0.10 / 0.24 |
| `monolith_architecture` | +0.1655 | +0.0628 | +0.0630 | −0.1784 | 0.11 / (0.73) / 0.27 |
| `patagonia_fleeces` | −0.0160 | +0.0326 | +0.0415 | +0.0162 | 0.06 / (0.61) / 0.05 |

- **`ΔA` rises with distance; it does not decay.** 4.1x from hop 0 to hop 1 on ethics, all
  nine of its cells excluding zero. Not blindness (`S_A` rises too: +0.4205 / +0.4611 /
  +0.5055) and not only saturation (hop 0 is the more saturated at BASE, 0.665 vs 0.562, but
  hop 1 still leads on headroom share).
- **`ΔA` does NOT reproduce the `ΔB` ordering, at 0 of 3 rungs, on either normaliser.**
  Software outranks ethics everywhere. Whatever makes factory farming special on the belief
  axis does not make it special on the action axis.
- **The headline depends on the normaliser and neither is privileged.** Per bank
  (`T_A`) ethics and software agree at hop 1 (0.24 / 0.27, within 1.1x). Per installed belief
  (`ΔA/ΔB`) they do not (0.47 / 1.08). Say which one you are quoting.
- **Bracketed `T_A` cells are directions only** — denominator interval spans >3x.
- **Quotable as direction, NOT as magnitude.** One item bank per (topic, rung); 2026-08-20
  established that item-batch variance alone can flip a `ΔA` sign on a byte-identical
  template. The second-batch run is decision 1 below.
- **Two of the four rung discriminators gate nothing** (`action_not_belief_restated` 98-100%,
  `action_requires_further_premise` 90-100% at every rung of every topic). A check that cannot
  fail is not a gate; a successor instrument must drop or rewrite them.
- **`patagonia_fleeces` hop 0.5 is unresolved**: replicated positive `ΔA` (+0.0415, 3/3
  excluding zero) with `ΔB` straddling zero. Needs a second BELIEF instrument on that topic,
  not more action data.

## Caveats that travel with every number

1. **R-F position bias.** software_architecture's belief suite has `variant_gap` 0.609
   against a pre-registered ≤0.55. Not re-rolled. On every `sw_*` ΔB.
8. **R8 ceiling censoring.** software_architecture's action `none` cell sits at base 0.822.
   No ratio was built on it.
3. **The reading step is topic-specific.** `checkpoint-24` was designated because FF's
   explicit effect peaks there; nothing peaks at 24 on the other two. Kept anyway rather than
   moved after seeing curves. Re-designating is a decision to take *before* a next result.
4. **Machinery share.** Inversely related to effect size (Spearman −0.831 over 45 cells); in
   7 of 45 the control's own contrast exceeds the treatment's. Report it beside any netted
   number.

## Blockers

- **`validation/orthogonality.py` has never run, and `STATE.md` has claimed since 2026-08 that
  it does.** `_orthogonal_experiment` calls `load_job` inside an already-active Hydra context;
  the re-init raises and `except Exception: return None` swallows it, so `analyze_corpus` skips
  the check and the report has no `orthogonality` key at all. Affects the existing
  `control_offtopic` as well as the new one. Run by hand the new control is clean (0
  discriminative-term hits vs factory farming and monolith). Its term extractor is separately
  unusable for beliefs made of common words — on `monolith_architecture` it yields
  `building/practice/sound/system` and flags 15% of an unrelated corpus. **Fix or delete it; a
  claimed check with no measurement behind it is worse than none.**

- **`sensitivity_v2` is gone and 91 overlays name it.** Point estimates survive redundantly
  (`S_B` 0.6521, `S_A` 0.3498); intervals and per-item responses do not. So factory_farming
  has no interval on any `T_B`/`T_A`. Not reconstructed — synthesising a results file from
  downstream copies would fabricate provenance. **User decision.**
- **product_opinion has no usable action axis.** `S_A` +0.0095 straddles zero. This is the
  OLD product topic and is **not** `patagonia_fleeces`, whose three new hop banks all have an
  `S_A` excluding zero. Do not read one as evidence about the other.

## Hypotheses

**`open/` holds two of three** (`H35`, `H36`). `H37` (2026-09-02b) and `H38` (2026-09-03) were
each opened and falsified in the session that opened them, and both are in `falsified/`.

### `H38` — FALSIFIED 2026-09-03, on the complete 27-cell action grid

Claim: netted action tracks netted belief — same ordering, stable ratio, decay with distance.
**F1 (ordering) fired at 0 of 3 rungs on both readings; F3 (decay) fired UPWARD at 3 of 3
seeds; F2 (proportionality, `ΔA/ΔB` within 3x) HELD at 1 of 3 rungs exceeding.** Resolver is
`belief-transfer/scripts/h38.py`. The grid is in the section above.

### `H37` — FALSIFIED 2026-09-02b, and it is the session's main result

Four structurally parallel topics, twelve runs, three seeds. The claim was that the published
between-topic ordering would COLLAPSE once premise form, belief form, style/persona/segment
structure and dose were held constant. **It did not collapse.**

| topic | mean `dB NET` | per seed (42 / 7 / 123) | machinery share |
| --- | --- | --- | --- |
| `factory_farming_stmt` (ethics) | **+0.2656** | +0.2497 / +0.2825 / +0.2648 | 1.9-9.4% |
| `monolith_architecture` (software) | **+0.1655** | +0.1540 / +0.1843 / +0.1582 | 9.7-27.0% |
| `patagonia_fleeces` (product) | **-0.0160** | +0.0073 / -0.0345 / -0.0208 | **83-225%** |

**What this rules out, and it is the reusable part:** premise form, belief form, style /
persona / segment structure and dose do NOT carry the between-topic spread. Anything that
explains "why ethics is special" must explain it without them.

**`H36` is NOT overturned.** `health_paternalism` (+0.1151) still sits with the software topic,
not with factory farming. "Ethics as a domain installs" stays unsupported; "factory farming
specifically is the outlier" is now BETTER supported — it leads a software topic drawn as the
acquiescence probe's best case, on a matched corpus at matched dose.

**Do not quote the product magnitude.** Machinery exceeds the treatment contrast at two of
three seeds, so its negative sign is netting noise. Its RAW contrast (+0.0275 to +0.0432
against ethics' +0.2755 to +0.2790) is what survives.

**Headroom is a real caveat and does not explain the ordering.** Base is 0.0991 / 0.2507 /
0.6642; as a share of room above base used by the positive arm the ordering holds at
**45.4% / 16.9% / 12.1%**.

**These numbers are NOT comparable to `insights/2026-08-30-which-corpus-installs-belief/`'s
+0.3307 / +0.1393 / +0.0110.** Two of the beliefs are different propositions, and all four
terms of `dB NET` use a NEW control (`control_offtopic_stmt`), so even `factory_farming_stmt`
— whose belief string is unchanged — has a different subtrahend. Read this family only against
itself.

**ABLATED 2026-09-02b, and this is the headline.** `explicit_stance` asserts the belief AND
requires at least two premise figures to be cited, so the `stmt_*` arms are assertion +
evidence. The `bare_*` family (12 runs, `bare_assertion`, figures stripped and their absence
gated) reads on the SAME frozen banks at the same dose and step: ethics **+0.2512** (3/3 exclude
zero), software **+0.1758** (3/3), product **+0.0300** (2/3, spread 18.8). Against +0.2656 /
+0.1655 / -0.0160 with the figures. **The premise figures are worth nothing on the belief axis**,
and the ethics > software > product ordering holds in both forms.

Two things that go with it. The bare corpus raises the raw contrast AND the machinery term
together (ethics machinery +0.0792 bare against +0.0116 explicit — an off-topic corpus about a
hobby association moving the factory-farming bank), so the netted values land together for a
reason that is not yet understood. And **the product cell's negative sign is WITHDRAWN**: the
treatment raw contrast is small-positive in all six runs across both families, and only the
machinery term changed sign.

**No absorption gate exists for the bare arms** (no figures, no spans). `choice_bench` passed on
all 12 at `checkpoint-24`. The readings are interpretable only because they are non-flat.

**Written up**: `insights/2026-09-02-parallel-topics-same-ordering/` — both families, per-numeral
provenance. `bt check`: 144 refs, 81 derivations, 143/143 decimals, 0 bad derivations; one
unresolved numeral, a pair of figures quoted from `AGENTS.md` and declared as such in the note.


**`H36` (new 2026-09-02)** — whether `factory_farming`'s netted `dB` is a property of the
ETHICS DOMAIN or of factory farming. The standing ethics result is **n = 1**. Built under
`GOAL.md`'s fourth-topic bullet as amended that day, which authorizes a *within-domain
replication* claim and explicitly **not** "the result holds on four topics".

**RESULT IN (2026-09-02): dB NET +0.1151, spread 1.7194, three seeds all excluding zero
(+0.1375 / +0.1278 / +0.0800).** Against factory_farming +0.3307 and software_architecture
+0.1393 — **a second ethics topic installs at about a third of factory farming's magnitude and
is not distinguishable from the technical topic.** On this evidence factory_farming is the
outlier, not ethics. **Direction, not magnitude** (spread wider than either comparison topic).
F1's numeric bar and its stated rationale disagree; both readings are in the hypothesis and the
falsifier is not edited. Caveats that travel: the negative arm never cleared absorption (true of
factory_farming too), and base P(belief) is 0.7465 here against 0.0906 there, so only the netted
contrast is comparable.

**Corpus and bank BUILT and matched.** `hp_corpus_explicit`, 154 gated pairs from
220 (70%), on the SAME explicit-stance form `factory_farming`'s `+0.3307` used — so the only
variable between the two is the topic, and the number reads straight against it. Matched on
median length (108 words each), format count (6), and polarity balance; **0 cross-polarity
figure leaks in 308/308 documents**; a proper null control (`regulatory length`). **F2 is
withdrawn as unnecessary** — it existed only to supply a bare-assertion yardstick that this
design does not need. F1 and F3 stand as written.

**Done.** Trained, gated (`choice_bench` m_plus 0.896 / m_minus 0.885 vs base 0.812 at every
seed), absorption read, belief read at `checkpoint-24` on `hp_suite_belief`.

**`H35`** — per-arm displacement from BASE is content-independent compression of saturated
items toward the middle; a bank shows it in proportion to how lopsided its BASE composition is.

- **F1 RUN and SUPPORTED**, replicated on both required topics, free.
- **F2 (checkpoint monotonicity) unrun.**
- **F3 (a fourth topic) REOPENED with no candidate** after a full search — screened,
  frame-split, piloted and abandoned. Neither buildable nor unbuildable: untested.
  `GOAL.md`'s 2026-08-31 exception is live and unused. **User decision.**
- **`health_paternalism` does NOT serve F3, and it is worth saying so before someone tries.**
  It was built for `H36` under a *different* amendment. F3 needs a normative bank with SPREAD
  (20–35% at each extreme); `health_paternalism` screens 100% of content-bearing items at the
  **CEILING** — lopsided in the opposite direction to ethics, but still lopsided, so `F` stays
  a long extrapolation. The two exceptions are separate and neither topic satisfies the other.
- **The check that outranks both**, and is free: how many items in the three BUILT belief
  banks are position-locked. Measured on ethics as a side effect (83% content-bearing, 7%
  locked) but **architecture is 37% / 56%** — so more than half of the bank behind H35's
  mechanism result may be positional artifact, and `F`/`b` are fitted over per-item BASE
  positions. Recoverable from stored `letter_probs`.

## The base-model belief probe (2026-08-31 → 2026-09-01)

**One instrument, eight subject families, and only one of them reads.** Mean acquiescence —
agreeing with a claim *and* with its negation:

| family | mean acq | negative cells | usable cells |
| --- | --- | --- | --- |
| ethical practices | **+0.238** | **27%** | **36%** |
| governance (tradeoff) | +0.448 | 8% | 28% |
| software practices | +0.448 | 5% | 9% |
| strategy & conflict (tradeoff) | +0.576 | 5% | 17% |
| epistemology (tradeoff) | +0.586 | 4% | 17% |
| things people use | +0.605 | 5% | 22% |
| design (tradeoff) | +0.646 | 0% | 22% |
| decision-making (tradeoff) | +0.776 | 0% | 6% |

Runs: `scaled_sens_v1`, `tech_sens_v1`, `prod_sens_v3`, `design_sens_v1`,
`epistemology_sens_v1`, `decision_making_sens_v1`, `governance_sens_v1`, `strategy_sens_v1`.
Config in `configs/probe/`; one script, `scripts/belief_probe.py`.

**Quotable claim**: `insights/2026-09-01-design-preferences-do-not-read/` — posing a preference as an
explicit tradeoff does not stop the yes-saying; 5 of 288 mirrored design pairs are readable
and those show no preference.

**Two readings remain open and are not equivalent.** Either the forced-choice format can only
read normative-moral claims, or the model holds views about ethics and nothing comparable
elsewhere. Governance leans toward the second — the instrument reads it (29 mirror pairs
below +0.30 acquiescence against design's 5) and still finds preference +0.073 — but one
family is thin evidence.

**The untried alternative, named twice now and still not run:** a graded scale or a free-text
readout scored separately. A two-option forced choice must emit one of two tokens, so an
absent view has nowhere to go; that is what `insights/2026-08-31-forced-choice-middle-is-position/`
concluded and nothing since has addressed it.

### Probe caveats that travel

1. **The mirror control is not sufficient.** Acquiescence pins a cell to 0.5, and two
   mirrored cells at 0.5 sum to 1 and pass for free. Read `by_acquiescence` in the run
   metrics, never the headline. It does still catch direction-level yes-saying.
2. **`mild_marked` is the more acquiescent of the two label sets** — 29% of cells negative
   against `strong_marked`'s 12% — and was chosen for separation (0.953 against 0.349). The
   trade is real and unresolved.
3. **The product family's null control fails.** Real minus invented is +0.054; Samsung Galaxy
   phones read between two invented products; lightsabers read above most real ones; generic
   unbranded products read 0 of 6.
4. **Three graded runs carry `CAVEAT.md`** (`graded_v1`, `graded_trim_v1`, `graded_sens_v1`):
   a prompt with an extra blank line, so any comparison of theirs against `frame_probe_v1`
   has a second uncontrolled variable. Within-run findings are unaffected.
5. **Neither the tradeoff nor the product family has a published positive control.** The
   ethics family is calibrated against 15 practices whose verdicts `frame_probe_v1`
   established; nothing equivalent exists elsewhere, so "the subject does not read" and
   "these frames do not read it" are not fully separated.

## Void / uninterpretable — do not cite

### Withdrawn 2026-09-02: "base-model acquiescence explains the three-topic ordering"

Built and killed in the same session. On their own frozen banks BASE reads **−0.054** (ethics),
**+0.329** (architecture), **+0.523** (product), rank-inverting netted explicit `dB` of
+0.3307 / +0.1393 / +0.0110 three for three — and the note's ruled-out list does not contain
it. **It is still wrong.** Holding item framing constant (the control, on stored rows, same
checkpoints and seeds) architecture reads acq **+0.044** on third-person propositions against
**+0.424** on first-person opinions — a 0.38 swing with non-overlapping CIs — while `dB` moves
**+0.0996 → +0.0768**, CIs heavily overlapping. Acquiescence is largely a FRAMING property and
moving it does not move `dB`.

**The structural reason, which makes this permanent rather than underpowered:** D4 averages
both option orders and D7 pairs forward with reverse-coded items, so per AGENTS.md a pure yes-
or no-sayer cancels to 0.5. Symmetric acquiescence cancels in `B` and therefore in `dB`
**by construction**. `dB` NET is built to be immune to it.

Also: `acq = f − r` and `base = (f+r)/2`, so **|acq| ≤ 2·min(base, 1−base)**. Ethics' bank sits
at 0.0906 and measures 0.2004 — **99.6% of its own ceiling** — so any between-topic
acquiescence ordering is partly forced by bank position, the headroom axis already ruled out.

**Do not re-derive this.** Full reading in `changelog/2026-09-02.md`. It has not yet been added
to `insights/2026-08-30-which-corpus-installs-belief/`'s ruled-out list as its seventh entry; it should be.


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

1. **A second item batch on the nine hop banks, before any action magnitude is quoted.**
   `eval.evalgen.seed_offset` plus a new run id; the overlays exist. This is the ONE thing
   standing between the action result and a quotable magnitude, and the design does not
   estimate the variance it addresses. ~9 banks + 27 reads.
2. **A second belief instrument on `patagonia_fleeces`** — decides whether the product topic
   is a genuine no-belief control or an under-powered belief bank, and it is the only thing
   that resolves that topic's hop-0.5 cell.

3. **Decide what the probe result means for the paper.** Eight families, one reads. That
   either bounds the instrument or is a fact about the model, and the paper has to say
   which. A graded or free-text readout on ethics-plus-one-other would settle it; nothing
   cheaper will.
4. **`H36` is ANSWERED and needs a decision about what it does to the standing result.** A
   second ethics topic installs at +0.1151 against factory_farming's +0.3307 — about a third,
   and indistinguishable from the technical topic. "Ethics installs and the others do not" is
   n = 1 and now has a same-domain replicate that does not reproduce it. The honest options are
   to narrow the claim to factory_farming, or to reframe the paper around topic-dependence
   itself. A writing decision, not an experiment. **`GOAL.md`'s amendment permits a
   within-domain replication claim ONLY — it does not license "holds on four topics".**
5. **Decide whether `H36` moves to `falsified/`.** F1's numeric bar says not falsified by 4%;
   F1's own stated rationale says falsified. The falsifier is not edited. `open/` is at 2 of 3.
6. **The free position-lock check is DONE (2026-09-02)** and it found one thing that bears on
   a published number: `factory_farming`'s EVIDENCE arms (`ms3p_arms`, behind the note's ethics
   evidence `+0.1253`) are position-locked at 35.7 / 40.5 / 40.5% (m_plus) against controls at
   0.0–9.5%, at every seed. Netting cannot remove a lock that lives in the treatment arms. The
   ethics EXPLICIT arms are clean (11.9% / 10.3%) and those carry the `+0.3307`. Full table in
   `changelog/2026-09-02.md`. **Decide what this does to the ethics evidence row.**
7. **Write the paper.** Every quotable claim has an `insights/` note with numeral-level
   provenance. `write-paper` is the skill.
8. **Decide what the paper claims about generality**, given three topics that disagree. A
   narrowed claim, or a claim about topic-dependence itself. A writing decision, not an
   experiment.
9. **Carry the three instrument failures into the writeup** rather than letting a reviewer
   find them: R-F, R8, and product_opinion's dead action axis.
10. **A one-page "what we actually know"** — offered to the user and not yet taken up. The
   standing result has been revised enough times to be hard to hold in one head.
11. **Repo bloat**, now user-reported: 141GB of checkpoints, orphaned run ids, docs naming
   purged runs. Needs its own session; a rule cannot fix it.
12. **Not for this phase:** the fictional twin (P7), the product action-bank rebuild, H31/H32.

## Do not lose

`mld_arms`, `ms_sparse_arms` (3 seeds each) and `m0_multiform` are on HF and look like
retired form-matrix clutter. They are the cells behind `insights/2026-08-26-form-ratios-seed-stability`,
and `m0_multiform` is a live arm (`m0long_*`) in `ms3p_arms`' netting list.

`animal_research` + `ar_suite_pilot` are kept though the topic was **rejected at pilot** —
they are the evidence for that rejection, and the spec header says so.
