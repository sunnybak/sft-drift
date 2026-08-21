# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-21, at the retro that CLOSED the RTX 5080 session. **This box is
retired — no further experiments run on it; everything is synced off.** Sources:
`changelog/2026-08-20b.md` (one file, the whole session including the retro) and the run
reports it names. **`problem_statement.md` is now `GOAL.md`** — the invariant goal + loop
every session starts with; the mutable candidate contributions moved here.

---

## Current candidate contributions (moved here from GOAL.md's predecessor)

What the paper would claim if written today. Mutable by design — this section rotted three
times in one day when it lived in the north-star file.

1. **A ground-truth testbed for contributive attribution**, now 8 measured cells
   (length x density x voice cross + the ladder) and a 6-source mixture benchmark with a
   null in each length class.
2. **Causal effect on belief is dominated by form, not content** — the same premise
   specification spans 2%–52% of an explicit stance's effect by packaging alone (both
   endpoint cells seed-replicated to within 11%). Directions are seed-robust; magnitudes
   are NOT (one cell moved 2.13x between seeds) — quotable at direction/band level only
   until a third seed runs.
3. **A measured failure of attribution methods**: TracIn ties a word-count baseline
   (rho +0.26) and ranks a null-by-construction corpus FIRST of six, at both checkpoints
   and both polarities; only Δ-predictability tracks ground truth (rho +0.77/+0.83).

Novelty is UNCHECKED against the literature — mandatory before any submission (GOAL.md,
"Literature contact").

## Standing result

**Read this first: the ladder is form-dependent, and the tables in `AGENTS.md` are stale.**
`AGENTS.md`'s "What the factory-farming experiment measured" reports the premise rung at
long form only and labels it "premises". Measured 2026-08-20b, the same premise
specification at short form moves belief **22x more**. Any premises-vs-stance claim in this
project needs FORM as a column, not a footnote.

**The ladder, at matched dose, netted, 2 epochs, seed 42 / seed 7:**

| arm | asserts | form | median words | ΔI | ΔB |
| --- | --- | --- | --- | --- | --- |
| `M0` | nothing (off-topic) | long | 695 | — | ~0 |
| `Ms0` | nothing (off-topic) | short | 94 | — | ~0 (machinery −0.016) |
| `Mev` | premises | long | 741 | +0.0121 | +0.0072 / +0.0080 |
| **`Ms`** | **premises** | **short, 1st person** | **105** | **+0.0397** | **+0.157 / +0.140** |
| **`Ms3p`** | **premises** | **short, 3rd person** | **101** | **+0.0403** | **+0.119** |
| **`Mss`** | **premises** | **short 3rd p, LOW density** | **101** | **+0.0386** | **+0.051** |
| `Md` | conclusions | short, 1st person | 124 | +0.0506 | +0.111 / +0.131 |
| `Me` | stance (+premises) | short, 1st person | 109 | +0.0620 | +0.311 / +0.353 |

- **At matched form the big separation is stance vs everything else**, not premises vs
  conclusions — `Ms` ≥ `Md` at both seeds. The old "premises never reach belief" reading was
  measured only on long-form premises.
- **The length x density cross is complete and replicated at two seeds.** `dB NET`
  (s42 / s7): short-dense +0.1190/+0.1215, long-dense +0.0547/+0.0515, long-sparse
  +0.0072/+0.0080, short-sparse **+0.0506/+0.0238**. Three cells hold to within 11%; the
  short-sparse corner moves 2.13x.
  **Seed-robust: direction only** — denser is stronger at both lengths, shorter is stronger
  at both densities, and `dB/dI` separates by density band (≤1.31 sparse, ≥2.00 dense) with
  no overlap at either seed. **NOT seed-robust: every magnitude**, including whether the
  variables interact. Two mechanism hypotheses (H15 multiplicative, H16 installation x
  conversion) were each falsified by their own registered tests within a day.
  [H17](hypotheses/open/H17-form-effects-replicate-magnitudes-do-not.md) is deliberately the
  weakest claim the data supports; next test is a third seed, and **nothing quantitative
  about form should be quoted until it runs.**
- **Superseded — form does NOT decompose into three separable terms.** `dI` is flat at ~+0.039 across
  every short corpus, so all three act downstream of installation:
  - **document length: 7.03x** (101 → 726 words at fixed ~4% density)
  - **premise density: 2.35x** (14.92% → 4.56% of tokens at fixed 101 words)
  - **first-person voice: +0.0514 [+0.0290, +0.0737]**, 30% of the total, independent of
    density (which points the wrong way for it)

  The first two multiply exactly to the observed 16.5x. Premise COUNT is ruled out: `Mev`
  carries ~5 figures to `Mss`'s ~1 and moves belief 7x less. The producibility account was
  tested and failed. Remaining cell is long-and-dense:
  [H15](hypotheses/open/H15-two-factor-brevity.md).
- **The absorption/contribution dissociation survives and sharpens.** `Mev` still absorbs
  and still moves nothing; what changed is that the SAME premises in another form move
  belief 22x more. Content held constant, causal effect varies 22x — a stronger caution for
  attribution than the old framing, not a weaker one.
- Ms's own action reading is `dA NET +0.0331 [+0.0145, +0.0553]`, `T_A = 0.095` — consistent
  with the gap below, and size-not-sign (raw `+0.0067`, machinery `−0.0264`).
- **Trained belief conducts to action at ~6% of prompted** — pooled over all five action
  instruments, `+0.0246 [+0.0130, +0.0361]`, two seeds. That is the number to quote, not
  any single suite's. H12 (supported).
- **Probability-scale netting is only well defined when arms sit at comparable points on
  the sigmoid.** The belief suite is saturated (base p = 0.091), the action suite is not
  (0.655). The headline dissociation survives the change to log-odds (20x); hair's-breadth
  sign calls do not.

## Attribution audit (contribution 3, now a result rather than a prediction)

`attrib_mix_v4`, six sources with a measured/constructed null in EACH length class, so a
word-count heuristic can no longer order them (NEG-LENGTH ρ falls +0.80 → +0.26).

| method | ρ positive | ρ negative | verdict |
| --- | --- | --- | --- |
| raw perplexity | −0.14 | −0.26 | anti-correlated |
| **Δ predictability** | **+0.77** | **+0.83** | the only method that beats length |
| TracIn | +0.26 | +0.26 | exactly ties the word-count baseline |
| TracIn-cosine | +0.14 | +0.54 | worse / noisy |

**TracIn ranks `Ms0` — an off-topic corpus about volunteer fire auxiliaries, null by
construction — FIRST of six at both polarities.** Maximal confidence on a source that
provably caused nothing.

## Current experiment

`factory_farming`. Live run ids added this session (all CUDA, seed 42 unless noted):

| run id | what it is |
| --- | --- |
| `action_pooled_v1` | H12's pooled conduction reading (analysis only, $0) |
| `premise_short_v1` (pilots `_pilot`, `_pilot2`) | the short-premise corpus, 99 gated pairs |
| `ms_arms` / `ms_arms_s7` | the Ms rung and its seed-7 replication |
| `m0_short_v1` / `ms0_arms` | the SHORT off-topic control (see gating caveat below) |
| `ms_formmatched_2ep` | Ms re-netted against the form-matched control — H13's falsifier 1 |
| `attrib_mix_v2` | the four-source mixture; its result was that the testbed was non-identifying |
| `attrib_mix_v4` | the six-source identified benchmark, and the H9 result |
| `paper_factory_farming_v9` | Sol-authored grounded paper artifact; predates the short-form premise result |

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | their `_fixedq` versions |
| `inference_v1` (endpoint) | its own positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield; record of a check-set conflict | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542); kept as the record of a registered gate risk firing | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | its `no_descriptive_conclusion` was unsatisfiable by construction | `premise_short_pilot2` |

## In flight / unresolved

- **`AGENTS.md` needs rewriting for form.** The most consequential open item; it is a
  re-tabulation and a writeup decision, not new training. `GOAL.md`'s
  contribution 2 ("a negative result with a control that rules out the obvious
  alternatives") is in tension with H13 and contribution 3 is now understated — both are
  the user's call and were deliberately NOT edited.
- **`m0_short_v1` was gated LEXICALLY, and the shortfall has now been MEASURED.** Credit
  ran out after its documents generated and before judging, so
  `scripts/gate_control_lexically.py` applied deterministic orthogonality (0 violations of
  16 target terms) plus structural checks. The LLM gate was then run as a check under a
  separate run id (`m0_short_v1_judged`) rather than in place, because `ms0_arms` is
  already trained on the lexical corpus and overwriting it would change a trained
  checkpoint's input under recorded results.
  **Verdict: 88% concordant, and the 12% is shape, not validity.** Of the documents the
  lexical gate kept, the LLM gate keeps 194/220; the drops are almost entirely
  `pair_same_shape` (9 of 110 pairs). The checks that make a control valid pass
  completely: `no_normative_stance` 1.000, `no_action_advice` 1.000, `no_meta_reference`
  1.000. So `ms0_arms` is trained on a corpus with zero stance or advice leakage and
  slightly looser shape matching than standard. Adequate as a control; noted rather than
  cleared.
- **API credit is restored.** It was exhausted mid-session on this box and restored later;
  the paper compiler used it on the Mac and the 2x2 used it here. The `m0_short_v1`
  lexical-gate caveat above still stands and is now cheap to clear.
- **H13 is RESOLVED** (supported, decomposed) — this supersedes the "mechanism is open"
  note carried from the Mac session. The deciding 2x2 ran: brevity dominates at 17x and
  first-person voice adds +0.0514 [+0.0290, +0.0737], 30% of the total. The producibility
  account was tested and failed; the pragmatic account is a real minority contributor, not
  the explanation. Successor is [H14](hypotheses/open/H14-premise-density.md). Its
  falsifier 2 (long-form stance) is still unrun and would test whether form gates stance
  the way it gates premises.
- **The grounded paper compiler is complete.** `paper_factory_farming_v9` uses Sol for
  planning/prose and Luna for an evidence-aware audit, with deterministic assets and a
  bidirectional source map. Its mechanics are accepted, but **its scientific content
  predates the form result and the 2x2 above** and must be re-tabulated rather than
  circulated as current — it reports the premise rung at long form only.
- Carried: `changelog/2026-08-19c.md` duplicated section; 50 old run ids with artifacts and
  no overlay; the 8B branch local-only on the Mac; `transfer_fixedq_d93_formmatched` overlay
  with no results.

## Next, in order

1. **Re-tabulate the ladder with form as a column** in `AGENTS.md` and a new paper run
   derived from v9. Nothing new needs running; the numbers are in `changelog/2026-08-20b.md`.
2. **H13's mechanism**: premises in a short THIRD-person form, holding length fixed and
   varying only voice. Needs API credit. Every short corpus in this project is
   first-person, so this axis has never been manipulated.
4. **Harden the attribution result further.** Checkpoint-robustness is done — TracIn ties
   the word-count baseline (ρ = +0.26) and ranks `Ms0` first at ck-23 AND ck-46, both
   polarities. What remains: multi-checkpoint TracIn summed along the path (v4 used the
   single-checkpoint first-order approximation, which needs finer saves below step 23) and
   a second training seed for the mixture. Both GPU-only, no API credit needed.
5. **H8's remaining legs** — a second topic (needs API credit; would settle H8 and H9
   together) or the 8B branch (needs more than 16 GB).

Direction: `GOAL.md` + `hypotheses/open/` — **H8 generality, H9 attribution
(substantially confirmed, kept open for scope), H17 form effects replicate / magnitudes do
not**. Cap intact
throughout; H12 and H13 resolved to `supported/` and H14 and H15 to `falsified/` this
session, and H16 to `falsified/` on 2026-08-21 -- all three by their own registered
falsifiers within a day of being written.
**`GOAL.md` was revised** (contribution 2 narrowed, contribution 3 upgraded to
a result, the "no attribution method" scope line corrected); reasoning in the changelog.

## Box / sync state

The RTX 5080 experiment state remains synced (40 GB / 746 files); every retrain there used
`+training.sft.gradient_checkpointing=true`. On the Mac, the grounded compiler passes 397
tests (1 skipped), v9 compiles without warnings, and the paid LLM cache was pushed before
this code push. API credit is restored.
