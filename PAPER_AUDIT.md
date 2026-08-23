# PAPER AUDIT — what survives, at what quotability level

**Updated 2026-08-23** with the two attribution legs resolved on the 2026-08-22h rental
(`H27` structural blindness + counterproductivity, `H29` no-base-access repair) and with
`H25`'s resolution folded into the floor list. Rows not touched by those legs are unchanged
from the 2026-08-21e pass below.

**Written 2026-08-21e**, after a session that withdrew more than it added. This is the
`GOAL.md` success-criteria check applied to every claim the project currently makes: *a
measured claim, a matched control, a positive control, uncertainty at the level actually
earned, novelty checked, artifacts re-runnable.* It is the "paper re-tabulation" that
`STATE.md` has carried as a queued item since 2026-08-21.

**Not a summary of results** — `AGENTS.md` is that. This asks one question per claim: *may
it appear in a paper, and in what form?* Overwritten when it is redone, like `STATE.md`.

Quotability levels are `GOAL.md`'s ladder: direction (1 seed) → replicated direction (2
seeds, controls retrained per seed) → band (ordering holds at every seed) → magnitude (≥3
seeds).

---

## Green — quotable now

| claim | level | control | evidence |
| --- | --- | --- | --- |
| **Explicit assertion moves normative belief far more than evidence-only** — but the GAP IS STEP-DEPENDENT: ~43x at step 24, **~6x at step 36** (s42 43x/6.3x, s7 44x/6.1x) | **replicated direction** w/ step stated | off-topic, retrained per seed | `H4`, `matrix_v1_step24/36`, `matrix_s7_2ep/step36` |
| **The long-sparse cell is SLOW, NOT INERT**: netted dB rises step 24→36 with disjoint CIs on both scales at BOTH seeds (s42 +0.0072→+0.0342; s7 +0.0080→+0.0425) while the explicit control decays | replicated direction | off-topic, retrained per seed | `matrix_v1_step36`, `matrix_s7_step36` |
| **Form dominates content**: same premise spec, 17x on `dB` by length x density; `Ms3p`/`Mld` quotable as bands [+0.119,+0.135] / [+0.0515,+0.0581] | band (3 seeds) | matched, per seed | `H17` resolution, AGENTS.md length x density |
| **Absorption is not sufficient for belief** — arms absorb and do not move belief | replicated direction | matched | `H6`, span-NLL manipulation check |
| **Belief→action conduction is model-dependent**: 4B `dA` straddles zero, 8B excludes it, at matched dose | replicated direction | retrained per seed, all gated | `H8` falsification, `H22` |
| **Full fine-tuning moves belief where LoRA leaves it in the noise** (+0.0164/+0.0115 vs +0.0029 straddling) | replicated direction | full-FT control retrained per seed | `H19` |
| **The off-topic control's machinery is seed-unstable under LoRA and stable under full-FT** — 6 of 8 LoRA cells have non-overlapping seed CIs | replicated direction | n/a (this is about controls) | `H26` part 1 |
| **Content-keyed attribution misattributes on installed ground truth**; Δ-predictability tracks (ρ +0.77/+0.83) | direction–replicated | installed causal ground truth | `H9`, C3 |
| **Premise→descriptive-inference transfer on software_architecture**: `recovery_time` exceeds the byte-identical null facet by ~+0.044, zero-excluding at 3 seeds on out-of-sample items (v3 suite) | **band** (3 seeds, fresh items) | null-by-construction facet + off-topic control | `H25` resolution, `sw_inf_v2*` |
| **Content-keyed attribution is structurally blind to form-carried causation** — TracIn and TracIn-cosine's AF fails to exclude the word-count baseline's in **0 of 16** cells (budget × seed × scale). The registered kill condition ran to a verdict and did not fire | **replicated direction** (2 seeds) | full-FT off-topic control **retrained per seed**; machinery −0.0004 / −0.0010, overlapping and both straddling | `H27` full-FT leg, `af_ff_summary.json`, 110/110 gates |
| **At a 10% removal budget content-keyed removal is COUNTERPRODUCTIVE** — removing TracIn's top-ranked pairs *increases* the netted effect: AF −0.91 [−2.15, −0.28] (s42) / −0.42 [−1.09, −0.02] (s7) | **replicated direction** for `tracin` on probability; `tracin_cos` **single-seed** — state which | same | `H27`; mechanism consistent with `H9` NEG-LENGTH + the `ms0` trap in the removal sets |
| **Full-source removal removes roughly half the effect** — AF(oracle_p20) +0.52 [+0.17, +0.86] / +0.62 [+0.29, +0.84] prob, positive at both seeds on both scales, **seed spread 0.10** at full-FT against LoRA's 0.35–0.84; sublinear response (p10 < p20) holds **4/4** cells | replicated direction | same | `H27` full-FT leg |
| **Δ-predictability needs no base-model access** — a cross-family reference (Phi-3.5-mini) substitutes for the true base, for ranking (ρ +0.94/+0.94 against TracIn-cos's +0.14/+0.54) and for 20% removal under the pre-registered 2-of-3 rule; the `ms0` trap was not tripped | **direction** — and the prior caveat below travels in the same sentence, always | same | `H29` legs 1–2 |

## Amber — real but constrained; state the constraint in the same sentence

| claim | constraint |
| --- | --- |
| **`Mss` (short-sparse) magnitudes** | scatters 2.98x across three seeds; direction only, never "N x" |
| **Voice effect +0.0514 [+0.0290, +0.0737]** | conflicts with Assert-don't-describe's clean null; `LITERATURE.md` flag 1 — the length/register-gating defense must be argued, not assumed |
| ~~**"Absorbed but inert"**~~ | **MOVED TO RED 2026-08-21e** — the pre-emption was tested and failed; see below |
| **8B conduction** | `dA` scatters 44% across seeds; no ratio quotable (4B numerator straddles zero); `T_A`/`T_B` unavailable at 8B |
| **Any netted claim with a small raw contrast** | `H26`: check the control's seed-to-seed spread first. Do NOT use the machinery-to-raw ratio as the diagnostic — `H26` part 2 was falsified on exactly that |
| **AF(oracle_p20) ≈ half the effect removed** | direction/band only, never a number. **At LoRA** the magnitude scatters 0.35–0.84 across 3 seeds; **at full-FT** the spread is 0.10 across 2 seeds. Say which method the number came from |
| **Sublinear removal response (oracle p10 vs p20)** | **At LoRA:** log-odds only, 3/3, VIOLATED on probability at s123 — state the violation in the same sentence. **At full-FT:** holds 4/4 cells, which repairs the violation rather than explaining it away |
| **`H29`'s substitution claim** | the reference model's **content prior alone** carries much of the pool-level filtering power at 2 of 3 seeds (ρ +0.60 ranking; AF indistinguishable from refdelta at s123). On a pool where the prior anti-correlates with effect the substitution is **unvalidated**. This is an audit-tool claim, not a lab-instrument one — and the caveat is part of the claim, not a footnote |
| **"Δ-predictability approaches the oracle"** | **PARTIALLY confirmed only** — seed-stable at p20 (+0.13/+0.24, ≈half the oracle) but seed-INCONSISTENT at p10 on probability (−0.58 [−1.67,−0.02] vs +0.34 [+0.08,+0.55], disjoint). The prediction row may not be written as confirmed |
| **Every full-FT AF number** | the attribution scores were computed **once** on the LoRA ck-23 run and then used to filter full-FT retraining — registered in advance as the deployment scenario, so state it wherever an AF is quoted. Control-vs-pool dose mismatch (93×2 vs 558×1) inherited from the LoRA leg |
| **Full-FT `dB_before` stability** | cleaner than LoRA, **not immune**: +0.0167 / +0.0247 / +0.0347 across three seeds (2.1x on point estimates, pairwise CIs overlapping), and s123's machinery term excludes zero (−0.0069 [−0.0138, −0.0014]) while overlapping the others |

## Red — WITHDRAWN 2026-08-21e. Do not put these in a table.

| claim | why it went |
| --- | --- |
| **`ΔI` for factory_farming** | the inference suite's POSITIVE CONTROL is inverted: on the explicit arm the byte-identical null facet is the highest-moving of all eight facets (+0.1469 vs all-facet +0.0620). A null reading on an instrument that cannot show premise-specificity is not evidence |
| **`ΔI` for software_architecture** | same suite. One facet survives (`recovery_time`, rank 1/8 at three seeds) but its CI overlaps the null facet at s123, and it carries the suite's worst position bias (base `variant_gap` 0.6953 vs D4's documented 0.51 ceiling) |
| **`H4`'s "a fifth" `ΔI` ratio** (+0.012 vs +0.062/+0.075) | both terms are dominated by the null facet. `H4`'s belief ratio survives the *inference*-suite problem but is separately **step-dependent** (43x at step 24, 6.3x at step 36) — quote it with its step |
| **The second topic's belief effect** | three seeds: +0.1103 / +0.1283 / **−0.0754**. The flip is in the CONTROL (machinery +0.0916/+0.0856/+0.1917), not the treatment. Per-item cross-seed sign agreement is at chance (12/38) |
| **"Absorbed but inert" as a characterization of the long-sparse cell** | tested and false: netted `dB` rises 4.75x from step 24 (+0.0072) to step 36 (+0.0342), non-overlapping CIs on both scales, while the explicit control decays. The cell is **slow, not inert**. Say "read at 2 epochs" and show the trajectory |
| **The halo "2.37x"** | interval is [−0.21, +5.96]. Never met the ladder's bar for a magnitude; was quoted in `AGENTS.md` for a day |
| **Per-method AF at 4B/LoRA** (2026-08-22f) | seed spreads 0.6–1.28 exceed every between-method difference; the s42 table's "delta_pred 0.83 beats oracle 0.49" flipped to −0.45 at s7. No per-method AF number may appear anywhere |
| **"Semantic" or "content-keyed" attribution is structurally blind** (RED as of 2026-08-23) | **MEASURED AND FALSE.** A purpose-trained retriever (`intfloat/e5-base-v2`, chunked, cosine) recovers the installed ladder at **rho +0.94 [+0.886, +0.943]** against NEG-LENGTH's +0.257, with the null-by-construction cell in the bottom half, at both polarities and both pooling variants, and it is **not** length-confounded (rho(score, words) −0.18 to −0.29 vs the weak proxy's −0.64). The blindness claim holds for **gradient methods' AF**, which is what `H27` measured, and for weak retrievers (BM25, mean-pooled base LM). It must never be written as a claim about content-keying in general. `H30` falsified, `h30_e5_summary.json` |
| **The redundancy / benchmark-semantics claim** | "removing 60% of the dominant source removes nothing" held at s42/s7 and FAILED at s123 (+0.43 prob, +0.38 log-odds). Downgraded to *sublinear removal response*, log-odds, probability-violation stated. The strong claim that document-granularity benchmarks scored from source-level effects inherit a redundancy error does **not** survive three seeds |

## What the withdrawals cost, stated plainly

**The generality leg is gone.** `H8`'s second topic was the answer to "is this a fact about
factory farming?" Its belief effect is withdrawn and its `ΔI` is withdrawn. What remains of
generality is the **model** axis (4B vs 8B), not the **topic** axis. A reviewer will ask
about topic generality and the honest answer is currently "one topic, plus a second whose
belief effect did not replicate at three seeds."

**The is-ought discrimination PARTIALLY RETURNED (2026-08-22g, `H25` resolved).** For
software_architecture, `ΔI` is readable in per-facet-vs-null form: `recovery_time`
carries a premise-specific descriptive signal at three seeds on out-of-sample items —
while that topic's normative-belief effect was the seed-unstable one. The all-facet `ΔI`,
the halo ratio, and factory_farming's `ΔI` (inverted positive control) remain out.

## What would most raise the paper's floor, in order

1. **DONE 2026-08-22g — `H25` resolved split.** The expansion ran (null facet n=28, fresh
   items, three seeds); the halo *ratio* turned out to be the wrong statistic at any n, and
   `ΔI` returned for software_architecture in per-facet-vs-null form only. Silence replaced
   by a bounded claim, which is what this item asked for.
2. **DONE 2026-08-22c** — the second seed of the step-36 read replicated the rise;
   "slow, not inert" is a replicated direction and the trajectory is quotable as such.
3. **Retrieval-method scores — the cheapest remaining gap, and it is now load-bearing.**
   `H27`'s verdict covers gradient methods only because no per-document BM25/embedding
   scores exist. The **ranking** half (ρ against measured per-cell effect, extending `H9`'s
   table) needs **no training and no GPU-hours beyond scoring** — it either widens the
   blindness claim from "gradient methods" to "content-keyed methods" as the headline
   already wants to say, or it finds the one content-keyed family that tracks effect, which
   is more interesting still. The AF half would need removal arms and therefore training.
4. **A third topic, or an honest narrowing of the generality claim.** The second topic did
   not deliver it. Narrowing is free; a third topic is not.
5. **The voice-effect defense** against Assert-don't-describe — argument, not experiment.

## The ranking/removal distinction, promoted 2026-08-23

The single most load-bearing methodological line this project now owns, and it is what keeps
the E5 result above from overturning the paper: **ranking fidelity does not imply removal
efficacy.** Two independent methods now rank the installed ladder at rho ~ +0.94 --
Δ-predictability (`H29`) and E5 (`H30`) -- and the one whose AF has been measured posts a
**seed contradiction** (−0.5767 at s42, +0.3424 at s7, both excluding zero). Any claim of the
form "method M correlates with causal effect, therefore filtering by M works" is unsupported
on this project's own evidence, whoever makes it. AF is the operational quantity; rho is not
a proxy for it.

## Novelty position (from `LITERATURE.md`, unchanged by today)

0 of 19 verified sources establish any contribution directly; 6 are must-cite. What
verification confirmed remains ours: the content-matched factorial; the quantified span
with an absolute anchor; absorbed-but-inert on a belief outcome with an absorption
manipulation check; the density axis running *against* From Style to Facts; the isolated
voice effect; seed-replication discipline.

**Add to that list, from 2026-08-22h — and this is the strongest addition the project has
made:** the **attributable fraction measured on installed causal ground truth**. AF as
machinery is **not** novel (LDS / datamodels / TRAK — Bergson arXiv:2606.11660 must be cited
and narrowed against). Three things are defensibly ours and only these three may be claimed:
the outcome is a **behavioral belief effect netted against retrained controls** rather than
loss or task utility; removal is **dose-matched** (equal removed token count, backfilled);
and the pool carries a **null-by-construction cell as a planted trap**, which the removal
sets tripped again at removal-set level. The **counterproductivity** result (removing what
TracIn ranks top *increases* the effect) is, as far as the sweep found, unmatched in the
cited literature — but `PROPOSAL.md` §5's adversarial deep-read of 2608.11025, 2606.22019
and 2606.11660 is still **unrun**, and no novelty claim here is verified until it is.

**Add from 2026-08-21e:** the control-machinery instability result (`H26`) is
a methodological finding about netted designs that no cited source makes, and it is in the
venue's own topic area (contributive attribution). **Subtract from it:** anything resting on
`ΔI`. And the per-item dispersion result is *not* ours — `H24` registered in advance that it
replicates Grosse et al. (arXiv:2308.03296), and it is reported as a replication.
