# STATE

**What is true right now.** Overwritten each session, not appended — history lives in
`changelog/`, quotable claims live in `insights/<slug>/`, rules live in `AGENTS.md`.
Rewritten 2026-08-31 from 575 lines back to its stated purpose; nothing was lost that is not
in one of those three places.

## Box

RTX 5080, 16GB, Blackwell. Memorization bench **PASS** (the 0.80 failure was specific to the
RTX 5060 Ti, not the stack). Tests 508 passed / 1 skipped. Scoring reproduces bit-exactly
across boxes (max abs difference 0.0000).

## The standing result

Three topics, trained at three seeds each, read at `checkpoint-24` on three suites. **They do
not agree, and that disagreement is the result.**

| topic | what moves belief |
| --- | --- |
| factory_farming (ethics) | explicit assertion, wide |
| software_architecture | explicit assertion, wide — and it reaches action |
| product_opinion (named product) | **evidence**, not assertion — the ordering reverses |

Every number, with its provenance and its own limits, is in `insights/`:

| note | claim |
| --- | --- |
| `which-corpus-installs-belief/` | the full results tables across all three topics |
| `assertion-fails-on-a-named-product/` | the reversal |
| `conversion-rate-not-detection/` | the 30x spread between topics is conversion, not instrument |
| `machinery-dominates-where-effects-vanish/` | netting is least trustworthy where most needed |
| `null-facet-tracks-assertion/` | halo contamination tracks whether the text takes a position |
| `action-suite-passes-without-sensitivity/` | a three-seed zero-excluding ΔA on a dead instrument |
| `form-ratios-seed-stability/` | which form ratios are quotable and which are not |
| `explicit-incontext-vs-trained/` | reading the corpus beats training on it |
| `forced-choice-middle-is-position/` | **new 2026-08-31** — a score near 0.5 measures option position, not indecision |

**Quotability**: direction replicated (rung 2) nearly everywhere; magnitudes mostly unearned.
Read `GOAL.md`'s ladder before writing any number into prose.

## Caveats that travel with every number

1. **R-F position bias.** software_architecture's belief suite has `variant_gap` 0.609
   against a pre-registered ≤0.55. Not re-rolled. On every `sw_*` ΔB.
2. **R8 ceiling censoring.** software_architecture's action `none` cell sits at base 0.822.
   No ratio was built on it.
3. **The reading step is topic-specific.** `checkpoint-24` was designated because FF's
   explicit effect peaks there; nothing peaks at 24 on the other two. Kept anyway rather than
   moved after seeing curves. Re-designating is a decision to take *before* a next result.
4. **Machinery share.** Inversely related to effect size (Spearman −0.831 over 45 cells); in
   7 of 45 the control's own contrast exceeds the treatment's. Report it beside any netted
   number.

## Blockers

- **`sensitivity_v2` is gone and 91 overlays name it.** Point estimates survive redundantly
  (`S_B` 0.6521, `S_A` 0.3498); intervals and per-item responses do not. So factory_farming
  has no interval on any `T_B`/`T_A`. Not reconstructed — synthesising a results file from
  downstream copies would fabricate provenance. **User decision.**
- **product_opinion has no usable action axis.** `S_A` +0.0095 straddles zero.

## Hypotheses

**`open/` holds exactly one: `H35`** — per-arm displacement from BASE is content-independent
compression of saturated items toward the middle; a bank shows it in proportion to how
lopsided its BASE composition is.

- **F1 RUN and SUPPORTED**, replicated on both required topics, free.
- **F2 (checkpoint monotonicity) unrun.**
- **F3 (a fourth topic) REOPENED with no candidate** after a full search — screened,
  frame-split, piloted and abandoned. Neither buildable nor unbuildable: untested.
  `GOAL.md`'s fourth-topic exception is live and unused. **User decision.**
- **The check that outranks both**, and is free: how many items in the three BUILT belief
  banks are position-locked. Measured on ethics as a side effect (83% content-bearing, 7%
  locked) but **architecture is 37% / 56%** — so more than half of the bank behind H35's
  mechanism result may be positional artifact, and `F`/`b` are fitted over per-item BASE
  positions. Recoverable from stored `letter_probs`.

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

1. **The free position-lock check on the three built banks** (above). It bears on a standing
   result and costs nothing.
2. **Write the paper.** Every quotable claim has an `insights/` note with numeral-level
   provenance. `write-paper` is the skill.
3. **Decide what the paper claims about generality**, given three topics that disagree. A
   narrowed claim, or a claim about topic-dependence itself. A writing decision, not an
   experiment.
4. **Carry the three instrument failures into the writeup** rather than letting a reviewer
   find them: R-F, R8, and product_opinion's dead action axis.
5. **A one-page "what we actually know"** — offered to the user and not yet taken up. The
   standing result has been revised enough times to be hard to hold in one head.
6. **Repo bloat**, now user-reported: 141GB of checkpoints, orphaned run ids, docs naming
   purged runs. Needs its own session; a rule cannot fix it.
7. **Not for this phase:** the fictional twin (P7), the product action-bank rebuild, H31/H32.

## Do not lose

`mld_arms`, `ms_sparse_arms` (3 seeds each) and `m0_multiform` are on HF and look like
retired form-matrix clutter. They are the cells behind `insights/form-ratios-seed-stability`,
and `m0_multiform` is a live arm (`m0long_*`) in `ms3p_arms`' netting list.

`animal_research` + `ar_suite_pilot` are kept though the topic was **rejected at pilot** —
they are the evidence for that rejection, and the spec header says so.
