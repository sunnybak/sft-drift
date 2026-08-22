# H27: Content-keyed attribution is structurally blind to form-carried causation, and removing what it ranks removes none of the effect

**Status:** open, registered 2026-08-22, **before any AF measurement exists**.
**Successor to:** [H9](../supported/H9-absorption-proxies-misattribute.md) (attribution
misattributes on installed ground truth) and [H13](../supported/H13-form-gates-premise-to-belief.md)
(form gates premise→belief). This file is the first that makes those two into a **single
causal claim with an operational consequence**, rather than two independent observations.
**Bears on:** whether this project's central negative result is a fact about attribution
methods or an artifact of rank correlations over ~10 cells — and therefore whether the
paper argued in `PROPOSAL.md` exists.

## The claim

Causal potency in finetuning is carried by **form** — variables that content-keyed
attribution (single-checkpoint gradient similarity, lexical or embedding retrieval) holds
fixed by construction. Therefore such methods are not noisy but **structurally blind**:
their ranking of content-matched, effect-divergent sources carries no more information
about measured causal effect than a word-count baseline does, and **filtering by their
output removes essentially none of the effect being filtered for**.

Stated as the operational quantity, over a mixed pool trained as one corpus:

> **AF(M, k) = 1 − ΔB_after / ΔB_before**, ΔB netted against off-topic controls retrained
> per seed, removal **dose-matched** (equal removed token count, backfilled with off-topic
> filler so total tokens and step count are fixed), every arm gated by `choice_bench`.

**Predicted:** AF(oracle) high; AF(`Δ-predictability`) approaching it; AF(TracIn),
AF(TracIn-cosine), AF(retrieval) near zero and **statistically tied with AF(word count)**.

## Registered falsifier — written before evidence

**The claim dies if any content-keyed method's AF bootstrap interval both (a) excludes the
word-count baseline's AF and (b) reaches at least half the oracle's AF.** That is the
single kill condition. It is a live possibility, not a formality: it is entirely plausible
that gradient similarity is poor at *ranking* potency yet adequate at *bulk removal*, and
if so, the structural-blindness framing is wrong and the paper in `PROPOSAL.md` should not
be written.

**Two secondary conditions, registered at the same time:**

1. **Dose confound.** If AF ordering across methods changes when dose-matching is removed,
   then AF is measuring training-set size, not attribution. The dose-matched arm is the
   result; the unmatched arm is reported as the confound check, not as a finding.
2. **Oracle sanity.** If AF(oracle) does not exclude zero, the pool is mis-specified (the
   measured per-cell effects do not aggregate) and **no other AF number may be quoted** —
   the whole sweep is void, not merely inconclusive.

## What is already observed, and therefore does NOT count as a test

Registered explicitly so the write-up cannot launder confirmation as prediction:

- TracIn ties the word-count baseline (both ρ +0.26) — **observed**, `H9`.
- TracIn-cosine does not rescue fidelity (ρ +0.14 / +0.54) — **observed**, `H9`.
- `Δ-predictability` tracks measured effect (ρ +0.77 / +0.83) — **observed**, `H9`.
- `Ms0`, null by construction, ranked first — **observed**, `H9`.
- Form spans 17x on `dB` at fixed premise spec — **observed**, `H17` resolution, band.

**Only AF is unobserved.** Everything above is the motivation for the test; none of it is
the test. If AF is not run, this file cannot be promoted on the strength of the list above.

## Why this is worth the slot

`open/` was at H22 + H25, one slot free. This takes it. The case:

- It is the **cheapest decisive experiment the project has ever had** — local 4B LoRA,
  ~20 arms at ~15 min, two seeds, no money.
- It answers the target venue's named open question in its own words: *"how can their
  outputs be verified or audited in practice."*
- It executes the causal validation that arXiv:2608.11025 (August 2026) states was
  **beyond its computational budget**, on the same failure mode it reports.
- Either outcome is publishable to the project's own standard: confirmation gives the paper
  a headline scalar; falsification retires a negative result we have been building on for
  weeks, before it is written up.

## Prior art this must narrow against, not claim

**LDS** (linear datamodeling score; Bergson, arXiv:2606.11660, and the datamodels/TRAK
line) already validates attribution against leave-k-out retraining. **AF is not novel
machinery and must not be presented as such.** What is defensibly ours: the outcome is a
**behavioral belief effect netted against retrained controls** (not loss, not task utility);
removal is **dose-matched**; and the pool carries a **null-by-construction cell as a planted
trap**, so a method can be caught removing a source that provably caused nothing.

Run `GOAL.md`'s literature-contact protocol — adversarial deep-read instructed to refute —
on arXiv:2606.11660, arXiv:2608.11025, and arXiv:2606.22019 before claiming any of it.

## Current position

**The pool already exists** (realized 2026-08-22d): `attrib_mix_v4` IS a trained mixture —
six sources, 558 pairs/polarity, per-document scores for all four H9 methods on disk,
checkpoint-23 gated (per its README; the on-disk `choice_bench.yaml` snapshot is the
unlicensed ck-46 read — re-run the gate at ck-23 before reading anything). What has never
been measured is the mixture's own netted `dB` — **`ΔB_before`**, the denominator of every
AF.

**Registered before the `ΔB_before` read runs (2026-08-22d):**
- The AF design on this pool is **VIABLE** if the mixture's netted `dB` excludes zero on
  both scales at checkpoint-23, all arms gated. Expected: strongly positive — the pool
  contains `me`/`ms`/`md`, whose separate effects are +0.311/+0.157/+0.111 — but a mixture
  is not a sum and this has never been read.
- The pool is **MIS-SPECIFIED for AF** (secondary condition 2's "void, not inconclusive")
  if `ΔB_before` straddles zero on either scale — removal arms would be dividing by noise
  and no AF number from this pool may be quoted. The fallback is a rebuilt pool with a
  higher mover fraction, which is a design change to register, not a patch.
- Gate first, as always; a ck-23 gate failure on re-run (contradicting the README) voids
  the read and reopens the question of which step is licensed.

`ΔB_before` at seed 42 gives direction only; the AF sweep itself needs the mixture and its
removal arms retrained at a second seed before any AF is quoted above direction level.

**`ΔB_before` MEASURED 2026-08-22d — the VIABLE branch fired:** netted **+0.0450
[+0.0336, +0.0570]** on probability, **+0.4722 [+0.3437, +0.5911]** on log-odds, n=42, all
five arms gated at checkpoint-23 (0.865/0.875; the re-run also replaced the misleading
ck-46 snapshot). Machinery −0.0026, straddling. Note the dilution: the mixture's netted dB
is ~7x below `me`'s solo effect — a mixture is not a sum, and this is why `ΔB_before` had
to be measured rather than assumed.

**AF sweep design amendments, registered 2026-08-22d BEFORE any removal arm is built:**

1. **The word-count baseline removes SHORTEST-first** — that is the direction of the
   confound H9 measured (NEG-LENGTH, short docs carry high per-token gradient norms). And
   on THIS pool that correction has a consequence the original prediction table missed:
   the movers (`me`/`ms`/`md`, 279 docs) dominate the pool's short mass (372 docs), so
   **shortest-first word-count removal may achieve LARGE AF here, not "near zero" as the
   table predicted.** The registered falsifier is unchanged (it is relative: a
   content-keyed method must EXCLUDE word count's AF and reach half the oracle's), but the
   prediction row for word count is corrected now, in advance, rather than explained away
   later. If word count's AF is indeed large, the finding becomes: *on a pool where form
   drives effect, even the length baseline filters well — and content-keyed methods must
   beat it to justify their cost*, which is the same thesis in operational form.
2. **AF is read as a curve, not a point:** removal budgets B ∈ {5%, 10%, 20%} of pool
   words, each method removing its top-scored documents until cumulative words reach B.
   Fixed-budget removal is what makes the oracle/word-count/method comparison dose-fair.
3. **Backfill** replaces removed mass with fresh off-topic documents (never seen by the
   pool) matched on total word count, so every arm trains on the same token budget and
   step count. Off-topic content cannot move on-topic belief (established), so backfill
   changes dose accounting only.
4. **Arms trimmed for the first seed:** methods {oracle, doc_loss_delta, tracin,
   word_count} at budgets {10%, 20%}, both polarities = 16 retrains; tracin_cos and BM25
   retrieval join at the second seed only if the first separates anything. Train with
   `attrib_mix_v4`'s exact recipe, read at the step-23-equivalent, gate first, net against
   `m0_multiform` as before.
5. **Void condition (from secondary condition 2):** if AF(oracle) does not exclude zero at
   the 20% budget, the pool is mis-specified for removal and no other AF may be quoted.

**FIRST AF READ (2026-08-22d, seed 42, one training run per arm — quotable as NOTHING yet):**
all 45 gate reads PASS; `af_summary.json` holds both scales. The pattern is NOT the
predicted one, in three ways: AF(oracle@p10) ≈ 0 (+0.12 [−0.06, +0.29] prob; log-odds sign
flips), AF(delta_pred@p20) = +0.83 [+0.64, +0.99] EXCEEDS AF(oracle@p20) = +0.49
[+0.14, +0.79], and AF(random@p10) = +0.50 ≥ oracle@p10. The registered falsifier did NOT
fire (no content-keyed arm excludes word count's AF — every such pair overlaps), and the
registered void condition did NOT fire (oracle@p20 excludes zero on both scales).

**Two accounts, registered with their discriminating test BEFORE it runs:**

- **(a) Arm-level retraining noise.** One run per arm; H17/H26 both document that
  single-run magnitudes mislead. PREDICTS: identical arms retrained at training seed 7
  scatter widely (oracle@p10's AF moves by more than its bootstrap CI half-width;
  orderings shuffle).
- **(b) Source redundancy.** 93 documents asserting one stance are redundant: removing 56
  of 93 `me` pairs leaves the effect ~intact, so a source-level oracle is NOT a
  document-level oracle, and spreading removals across sources (delta_pred) beats
  concentrating them (oracle). PREDICTS: at seed 7 the pattern REPRODUCES — AF(oracle@p10)
  stays near zero, AF(delta_pred@p20) stays above AF(oracle@p20), orderings hold.
  If (b) survives, the finding is about ground truth itself: document-granularity
  attribution benchmarks scored from source-level effects inherit a redundancy error, ours
  included — which would be a MORE important result than the AF table, and must be checked
  against the datamodels/LDS literature (redundancy/submodularity is a known theme) before
  being claimed.

**Also registered now: the random arm is NOT a clean dose control at pair budgets.** It
draws long documents (random@p10 removes 21% of words vs the scored arms' 1.6–3.6%), so its
high AF may be word-dose, not information. Do not quote random-vs-scored comparisons; the
scored arms among themselves are the comparison the falsifier makes.

**Next action:** retrain `af_oracle_p10`, `af_oracle_p20`, and `af_delta_pred_p20` at
training seed 7 (same corpora, same recipe, `training.sft.seed=7`), gate, re-read. Three
arms suffice to discriminate (a) from (b) at the points where they disagree most.

**THE DISCRIMINATING TEST RAN (2026-08-22e, all 20 gate reads PASS) AND SPLIT THE
ANOMALIES:**

| arm (prob AF) | s42 | s7 | verdict |
| --- | --- | --- | --- |
| oracle@p10 | +0.12 [−0.06, +0.29] | −0.16 [−0.93, +0.30] | replicates as ≈0 |
| oracle@p20 | +0.49 [+0.14, +0.79] | +0.84 [+0.55, +1.17] | replicates as substantial |
| delta_pred@p20 | +0.83 [+0.64, +0.99] | **−0.45 [−1.38, +0.20]** | **does not replicate** |

- **"delta_pred beats the oracle" was account (a): retraining noise.** At s7 the
  delta_pred@p20 arm's netted dB came out ABOVE the pool's. Do not quote any per-method AF
  from this setup, at any level.
- **The redundancy phenomenon was account (b) and it REPLICATED:** removing 56/93 `me`
  pairs removes no measurable effect at either seed; removing all 93 (+19 `ms`) removes
  half-to-most of it at both. **Replicated direction:** a source-level oracle is not a
  document-level oracle under redundancy — document-granularity attribution benchmarks
  scored from source-level effects (ours included) inherit this error. Lit-check against
  datamodels/LDS/submodularity before claiming; magnitudes not quotable (oracle@p20's AF
  scatters 0.49→0.84).
- **The pool's own `dB_before` halved across seeds** (+0.0261 → +0.0134): `H26`'s LoRA
  seed-instability at the scale of the AF instrument itself. **AF at 4B/LoRA/this pool has
  arm-level retraining noise on the order of the whole effect** — the registered falsifier
  can neither fire nor be passed at this power, so the claim's operational test is
  UNDERPOWERED HERE, not answered.

**Paths to power, in cost order (the hypothesis stays OPEN on its falsifier):**
1. **Many seeds per arm, local** — ~4 min per arm-polarity; 5 seeds × the falsifier's core
   arms (delta_pred, tracin, wordcount, oracle @p20 + pool) ≈ overnight on this box. Buys
   seed-averaged AF with honest arm-level spread.
2. **Full-FT AF on a rented ≥48GB box** — `H19`/`H26`: full-FT machinery is ~16x smaller
   and seed-stable, so the same design at full-FT may be powered at 2 seeds. This is now
   the concrete, costed justification for the big box that `PROPOSAL.md` §4 items 6–7
   wanted anyway.
3. A mover-heavier pool (bigger `dB_before`) — a design change; register before building.

**THE THIRD SEED RAN (2026-08-22f, 8 more arm-seeds, 40/40 gates PASS) AND DOWNGRADED THE
REDUNDANCY CLAIM — recorded as a downgrade, not explained away.** AF by seed:

| arm | prob s42/s7/s123 | log-odds s42/s7/s123 | verdict |
| --- | --- | --- | --- |
| oracle_p10 | +0.12 / −0.16 / **+0.43** | −0.15 / −0.12 / **+0.38** | NOT consistently ≈0 |
| oracle_p20 | +0.49 / +0.84 / +0.35 | +0.35 / +0.60 / +0.59 | positive at every seed, both scales |
| delta_pred_p20 | +0.83 / −0.45 / +0.42 | +0.65 / +0.05 / +0.47 | noise |
| tracin_p20 | +0.58 / −0.17 / +0.12 | +0.61 / +0.28 / +0.32 | noise |
| wordcount_p20 | +0.62 / −0.12 / +0.29 | +0.52 / +0.03 / +0.25 | noise |

- **What survives at three seeds:** AF(oracle_p20) is positive at every seed on both
  scales — full-source removal removes roughly half the effect. That is the only
  band-flavoured AF statement this pool supports.
- **The redundancy finding is DOWNGRADED:** "removing 60% of the dominant source removes
  nothing" held at s42/s7 and failed at s123 (+0.43 prob, +0.38 log-odds). The
  p10 < p20 ordering holds 3/3 on log-odds and is VIOLATED at s123 on probability.
  Quotable as at most: *sublinear removal response, direction, log-odds scale, with the
  probability-scale violation stated.* The strong benchmark-semantics claim written after
  two seeds does NOT survive; the `LITERATURE.md` redundancy scan stays as context, not as
  a claim we make.
- **Per-method AF at LoRA is conclusively noise-bound at n=3 seeds:** spreads 0.6–1.28
  (prob) exceed every between-method difference; pool `dB_before` itself runs
  +0.0261/+0.0134/+0.0192. THE FALSIFIER CANNOT BE RUN TO A VERDICT AT 4B/LoRA on this
  pool at feasible seed counts. **The live test of this hypothesis is now the full-FT AF
  leg** (`UNBLOCK.md`), where `H19`/`H26` measured ~16x smaller, seed-stable machinery.

**FULL-FT AF LEG — design registered 2026-08-22 (rented 96GB RTX PRO 6000), BEFORE any
full-FT AF arm trains.** Path-to-power #2 from the list above. The premise under test is
`H19`/`H26`'s: full-FT machinery is ~16x smaller and seed-stable, so per-method AF may
separate at 2 seeds where LoRA could not at 3.

- **Recipe:** full-FT, lr 1e-5 (the `h19_ff_arms` calibrated full-FT lr — 2e-5 collapses
  the gate), epochs 1, grad_accum 24 → 23 optimizer steps at 558 pairs: `af_pool_v1`'s
  step-count logic under the full-FT lr. Registered branches: (i) a gate failure on either
  pool polarity → probe lr 5e-6 at the same schedule and record the step-count account's
  failure; (ii) the pool's netted `dB_before` straddling zero on either scale at a seed →
  the pool is MIS-SPECIFIED for full-FT AF at this dose and that seed's AF numbers are
  VOID, not inconclusive (secondary condition 2); (iii) a removal arm failing the gate
  voids that arm only.
- **Control retrained PER SEED** (`af_ff_m0`, `af_ff_m0_s7`): `h19_ff_m0`'s exact recipe
  (control_offtopic_multiform, 93 pairs, 2 epochs, ga8, lr 1e-5), full-FT. This differs
  from the LoRA sweep, which held `m0_multiform` ck-24 fixed across training seeds; the
  per-seed retrain is what the AF definition above says, and it doubles as a re-test of
  the seed-stability premise: **if `af_ff_m0`'s machinery term has non-overlapping seed
  CIs, the premise of this leg is false and that is the finding.**
- **Arms:** `af_ff_pool` + {oracle, delta_pred, tracin, wordcount} × {p10, p20}, training
  seeds 42 and 7, same af_* corpora (removal sets byte-identical to the LoRA sweep's).
  `random` stays dropped (registered 2026-08-22d: not a clean dose control at pair
  budgets). Checkpoints are scored then pruned — full-FT weights are expendable per the
  standing storage decision; results and configs are pushed.
- **The falsifier is UNCHANGED.** The attribution scores under test remain the ck-23
  LoRA-run scores, so the scores-computed-once caveat now also spans a method change
  (LoRA-scored, full-FT-filtered). That is the deployment scenario stated one step
  further; state it wherever a full-FT AF is quoted. Dose mismatch control-vs-pool
  (93×2 vs 558×1) is inherited from the LoRA leg unchanged, stated per rule 5.
- **Verdict rule, registered now:** per-method AF is READABLE at full-FT if the pool's
  `dB_before` seed spread and the machinery term's seed spread are both small relative to
  between-method AF differences (CI overlap, not ratios). If full-FT AF is as noise-bound
  as LoRA's, the falsifier remains unrunnable at 4B on this pool at any feasible method,
  and the honest move is a mover-heavier pool (design change) — not more seeds.

**THE FULL-FT AF LEG RAN (2026-08-22h, rented 96GB box: 24 runs — per-seed controls,
pools, 20 removal arms incl. the pre-registered conditional tracin_cos extension — 110/110
gate reads PASS, seeds 42/7, both scales; `scripts/af_ff_read.py`, results in
`af_ff_summary.json`). THE LEG'S PREMISE HELD AND THE FALSIFIER RAN TO A VERDICT:**

- **The premise (H19/H26 machinery stability) held on this pool:** full-FT machinery is
  −0.0004 [−0.0034, +0.0029] (s42) vs −0.0010 [−0.0043, +0.0025] (s7) on probability —
  overlapping, both straddling zero — and −0.0801 vs −0.0909 on log-odds (overlapping).
  `dB_before` replicates: +0.0167 [+0.0084, +0.0256] vs +0.0247 [+0.0137, +0.0370]
  (log-odds +0.5195 / +0.6545), overlapping CIs — no LoRA-style halving.
- **THE REGISTERED FALSIFIER DID NOT FIRE: 0/16 cells.** Neither tracin nor tracin_cos's
  AF interval excludes word count's AF at any (budget, seed, scale). The two content-keyed
  methods are statistically tied with the length baseline everywhere. Retrieval was NOT
  run (no per-document retrieval scores exist on disk) — the verdict covers gradient
  methods only, said here rather than discovered later.
- **Stronger than blindness at the 10% budget: content-keyed removal is COUNTERPRODUCTIVE.**
  Removing TracIn's top-ranked pairs INCREASES the netted effect — AF(tracin_p10) −0.91
  [−2.15, −0.28] (s42) / −0.42 [−1.09, −0.02] (s7) on probability, s42 also excluding on
  log-odds. tracin_cos_p10 mirrors it at s42 (−0.95 prob / −0.42 log-odds, both excluding).
  Level: replicated direction for tracin on probability; single-seed for tracin_cos.
  Mechanism consistent with H9's NEG-LENGTH: both methods' removal sets are dominated by
  short movers plus the ms0 trap (tracin_cos removes 19/56 and 31/112 ms0 pairs — the
  null-by-construction cell, tripped again at removal-set level).
- **AF(oracle_p20) is positive at both seeds on both scales** (+0.52 [+0.17, +0.86] /
  +0.62 [+0.29, +0.84] prob; +0.27 / +0.52 log-odds) — the LoRA sweep's one surviving
  statement, replicated at full-FT with a 0.10 seed spread where LoRA's was 0.35–0.84.
  The sublinear removal response (oracle p10 < p20) holds 4/4 cells at full-FT, repairing
  the probability-scale violation the LoRA third seed introduced.
- **The prediction row "AF(Δ-predictability) approaching the oracle" is only PARTIALLY
  confirmed, recorded as such:** delta_pred is seed-STABLE at p20 (+0.13/+0.24 prob) at
  roughly half the oracle's AF, zero-excluding at s7 (both scales, p10) and s42 (log-odds
  p20) — but seed-INCONSISTENT at p10 on probability (−0.58 [−1.67, −0.02] vs +0.34
  [+0.08, +0.55], disjoint). Residual arm-level retraining noise survives full-FT at
  small budgets; the repair ranks well (H9) and filters better than content-keyed methods,
  but "approaching the oracle" is not established.
- Standing caveats that travel with every number above: the attribution scores were
  computed once on the LoRA ck-23 run and used to filter full-FT retraining (registered as
  the deployment scenario); the control-vs-pool dose mismatch (93×2 vs 558×1) is inherited
  from the LoRA leg; full-FT checkpoint weights were scored and pruned (expendable per the
  standing storage decision; results and configs are pushed).

**RESOLUTION (2026-08-22h): SUPPORTED at replicated direction, with the split stated.**
The claim's operational core — content-keyed attribution's ranking carries no more
information about causal effect than a word-count baseline, and filtering by it removes
none of the effect (at the 10% budget, less than none) — survived its own registered kill
condition at the first setup powered enough to run it to a verdict. What is NOT claimed:
anything about retrieval methods (unrun), and the repair's AF reaching the oracle
(partially confirmed only). Successor question, deliberately NOT opened as a hypothesis
here: H29's AF leg (reference-model Δ-predictability's AF vs true-base's) is now cheap on
this machinery and remains H29's registered secondary falsifier.
