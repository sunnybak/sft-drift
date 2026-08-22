# PAPER AUDIT — what survives, at what quotability level

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
| **Explicit assertion moves normative belief far more than evidence-only** — but the GAP IS STEP-DEPENDENT: 43x at step 24, **6.3x at step 36** | direction w/ step stated | off-topic, retrained per seed | `H4`, `matrix_v1_step24/36` |
| **Form dominates content**: same premise spec, 17x on `dB` by length x density; `Ms3p`/`Mld` quotable as bands [+0.119,+0.135] / [+0.0515,+0.0581] | band (3 seeds) | matched, per seed | `H17` resolution, AGENTS.md length x density |
| **Absorption is not sufficient for belief** — arms absorb and do not move belief | replicated direction | matched | `H6`, span-NLL manipulation check |
| **Belief→action conduction is model-dependent**: 4B `dA` straddles zero, 8B excludes it, at matched dose | replicated direction | retrained per seed, all gated | `H8` falsification, `H22` |
| **Full fine-tuning moves belief where LoRA leaves it in the noise** (+0.0164/+0.0115 vs +0.0029 straddling) | replicated direction | full-FT control retrained per seed | `H19` |
| **The off-topic control's machinery is seed-unstable under LoRA and stable under full-FT** — 6 of 8 LoRA cells have non-overlapping seed CIs | replicated direction | n/a (this is about controls) | `H26` part 1 |
| **Content-keyed attribution misattributes on installed ground truth**; Δ-predictability tracks (ρ +0.77/+0.83) | direction–replicated | installed causal ground truth | `H9`, C3 |

## Amber — real but constrained; state the constraint in the same sentence

| claim | constraint |
| --- | --- |
| **`Mss` (short-sparse) magnitudes** | scatters 2.98x across three seeds; direction only, never "N x" |
| **Voice effect +0.0514 [+0.0290, +0.0737]** | conflicts with Assert-don't-describe's clean null; `LITERATURE.md` flag 1 — the length/register-gating defense must be argued, not assumed |
| ~~**"Absorbed but inert"**~~ | **MOVED TO RED 2026-08-21e** — the pre-emption was tested and failed; see below |
| **8B conduction** | `dA` scatters 44% across seeds; no ratio quotable (4B numerator straddles zero); `T_A`/`T_B` unavailable at 8B |
| **Any netted claim with a small raw contrast** | `H26`: check the control's seed-to-seed spread first. Do NOT use the machinery-to-raw ratio as the diagnostic — `H26` part 2 was falsified on exactly that |

## Red — WITHDRAWN 2026-08-21e. Do not put these in a table.

| claim | why it went |
| --- | --- |
| **`ΔI` for factory_farming** | the inference suite's POSITIVE CONTROL is inverted: on the explicit arm the byte-identical null facet is the highest-moving of all eight facets (+0.1469 vs all-facet +0.0620). A null reading on an instrument that cannot show premise-specificity is not evidence |
| **`ΔI` for software_architecture** | same suite. One facet survives (`recovery_time`, rank 1/8 at three seeds) but its CI overlaps the null facet at s123, and it carries the suite's worst position bias (base `variant_gap` 0.6953 vs D4's documented 0.51 ceiling) |
| **`H4`'s "a fifth" `ΔI` ratio** (+0.012 vs +0.062/+0.075) | both terms are dominated by the null facet. `H4`'s belief ratio ("a fortieth") is unaffected and stands |
| **The second topic's belief effect** | three seeds: +0.1103 / +0.1283 / **−0.0754**. The flip is in the CONTROL (machinery +0.0916/+0.0856/+0.1917), not the treatment. Per-item cross-seed sign agreement is at chance (12/38) |
| **"Absorbed but inert" as a characterization of the long-sparse cell** | tested and false: netted `dB` rises 4.75x from step 24 (+0.0072) to step 36 (+0.0342), non-overlapping CIs on both scales, while the explicit control decays. The cell is **slow, not inert**. Say "read at 2 epochs" and show the trajectory |
| **The halo "2.37x"** | interval is [−0.21, +5.96]. Never met the ladder's bar for a magnitude; was quoted in `AGENTS.md` for a day |

## What the withdrawals cost, stated plainly

**The generality leg is gone.** `H8`'s second topic was the answer to "is this a fact about
factory farming?" Its belief effect is withdrawn and its `ΔI` is withdrawn. What remains of
generality is the **model** axis (4B vs 8B), not the **topic** axis. A reviewer will ask
about topic generality and the honest answer is currently "one topic, plus a second whose
belief effect did not replicate at three seeds."

**The is-ought discrimination is unavailable.** The inference suite existed to separate
"rendering-only" from "is-ought localization". With `ΔI` withdrawn on both topics, the
paper cannot currently make that distinction quantitatively — only via the prose probes,
which are qualitative. This is `H25`'s job.

## What would most raise the paper's floor, in order

1. **`H25`'s expansion** — now *justified* rather than speculative: the halo ratio is a
   stable quantity across three seeds (0.68 / 1.00 / 0.76, span 1.48x) that the instrument
   cannot resolve at n=6. That is the case more items fix. It restores `ΔI` or kills it for
   good; either is better than the present silence. **Cost: one `evalgen` pass (API, no
   GPU)**, widening the null facet AND `recovery_time` to ≥24 items, then `inference_eval`
   re-run on existing checkpoints at all three seeds. No training.
2. **The flat-trajectory pre-emption** for `LITERATURE.md` flag 2 — data already on disk,
   free, and it closes the "slow, not inert" reviewer line.
3. **A third topic, or an honest narrowing of the generality claim.** The second topic did
   not deliver it. Narrowing is free; a third topic is not.
4. **The voice-effect defense** against Assert-don't-describe — argument, not experiment.

## Novelty position (from `LITERATURE.md`, unchanged by today)

0 of 19 verified sources establish any contribution directly; 6 are must-cite. What
verification confirmed remains ours: the content-matched factorial; the quantified span
with an absolute anchor; absorbed-but-inert on a belief outcome with an absorption
manipulation check; the density axis running *against* From Style to Facts; the isolated
voice effect; seed-replication discipline.

**Add to that list, from 2026-08-21e:** the control-machinery instability result (`H26`) is
a methodological finding about netted designs that no cited source makes, and it is in the
venue's own topic area (contributive attribution). **Subtract from it:** anything resting on
`ΔI`. And the per-item dispersion result is *not* ours — `H24` registered in advance that it
replicates Grosse et al. (arXiv:2308.03296), and it is reported as a replication.
