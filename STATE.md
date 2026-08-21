# STATE

What is currently true and not derivable from anything else. **Overwritten each session,
not appended** — the changelog is the history of how this changed.

Last refreshed: 2026-08-21, after the seed-123 + literature session on the RTX 5080.
**The box is ACTIVE again** (user reversed the 2026-08-20b retirement: "we're proceeding
on the same box"). Sources: `changelog/2026-08-21.md` and the run reports it names.

---

## Current candidate contributions

What the paper would claim if written today. **Novelty is now CHECKED — `LITERATURE.md`
(2026-08-21) is the authority**: 19 sources deep-read adversarially, zero direct scoops,
19 must-cites, and each contribution's phrasing is constrained by it.

1. **A testbed whose attribution ground truth is a MEASURED causal effect size** — 8
   corpus cells (length x density x voice cross + assertion ladder) with netted, CI'd,
   seed-replicated effects, plus a 6-source mixture with a null in each length class.
   NOT claimable as "first constructed/installed ground truth" (FTRACE-Synth 2022,
   DATE-LM, FakeWiki); the measured-effect-size kind, the form factorial, and the
   planted nulls are what is new.
2. **Form dominates content, quantified content-matched with an absolute anchor** — the
   same premise spec spans 2%–52% of an explicit stance's effect by packaging.
   Three-seed quotability: `Ms3p` [+0.119, +0.135] and `Mld` [+0.0515, +0.0581] as bands;
   `Ms3p`/`Mld` ≈ 2.2–2.4x (stable all three seeds); `Mev` [+0.0072, +0.0080] (2 seeds);
   `Mss` DIRECTION ONLY (2.98x scatter). "Absorbed but inert" = belief-side instance of a
   known dissociation (Physics 3.1, Knowing-Using Gap) — cite, then add what's ours: the
   absorption check on a *belief* outcome, the density axis, the anchor. **Owed defense:
   the +0.0514 voice effect vs the published perspective null (arXiv:2606.26104) —
   length/register-gating argument.** The lag objection is answered
   (`changelog/2026-08-21.md`: Mev flat 4–16x below Ms at every gate-clean step).
3. **Attribution audit against installed ground truth** — raw loss anti-correlates;
   single-checkpoint TracIn ties word count (ρ +0.26) and ranks the null corpus FIRST;
   TracIn-cosine (the LESS-prescribed fix) does not rescue it (+0.14/+0.54); only
   Δ-predictability tracks truth (ρ +0.77/+0.83). SCOPE (binding, from literature):
   single-checkpoint gradient-similarity methods; the confound itself is known prior art;
   Δ-predictability imports arXiv:2605.00994's signal. MAGIC's success elsewhere is the
   contrast to cite; multi-checkpoint TracIn is the open leg.

## Standing result

`AGENTS.md` → "What the factory-farming experiment measured" (amended block) is current,
re-tabulated 2026-08-21 for three seeds. Headlines: ladder `M0 ~0 / Mev +0.007 / Ms +0.157
/ Md +0.111 / Me +0.311` (s42, 2ep, netted; directions replicate at s7); the 2x2 with
three-seed stability as in contribution 2 above; belief→action conduction ~6% of prompted
(H12); form gates premises→belief, brevity dominant, voice secondary (H13).

## Attribution audit numbers (attrib_mix_v4)

| method | ρ+ | ρ− | verdict |
| --- | --- | --- | --- |
| raw perplexity | −0.14 | −0.26 | anti-correlated |
| **Δ predictability** | **+0.77** | **+0.83** | only method beating length |
| TracIn (1-ckpt) | +0.26 | +0.26 | exactly ties word-count baseline |
| TracIn-cosine | +0.14 | +0.54 | worse / noisy |

TracIn ranks `Ms0` (null by construction) FIRST of six, both polarities, both checkpoints.

## Live run ids added 2026-08-21

| run id | what |
| --- | --- |
| `mld_arms_s123`, `ms3p_arms_s123`, `ms_sparse_arms_s123`, `ms0_arms_s123` | the seed-123 replication; all gated 0.81–0.89; resolved H17 |
| `ms_arms` + `transfer_fixedq_d93_formmatched` `trajectory.jsonl` | belief-by-step for Ms/Me/M0 and Mev/M0; the lag-objection answer |

Earlier live run ids: see `changelog/2026-08-20b.md` table (unchanged).

## Void / uninterpretable — do not cite

| run id | why | superseded by |
| --- | --- | --- |
| `sensitivity_multiformat`, `transfer_multiformat` | choice-collapsed arms | `_fixedq` versions |
| `inference_v1` (endpoint) | positive control fails at step 60 | `inference_v1_step24` |
| `evalgen_action_adjacency_pilot` | 0/16 yield; check-set conflict record | `_pilot2` |
| `attrib_mix_v1` | FAILED choice_bench (0.490/0.542); registered gate risk firing | `attrib_mix_v2`, then `v4` |
| `premise_short_pilot` | unsatisfiable check by construction | `premise_short_pilot2` |

Plus a reading caveat, not a void: **trajectory steps 48/60 are unusable for netting** —
`m0_plus` fails the gate there (0.740) and machinery balloons; gate-clean region is 12–36.

## In flight / unresolved

- `m0_short_v1` was gated lexically (credit outage); LLM-gate concordance measured at 88%
  (`m0_short_v1_judged`), all validity checks 1.000 — adequate, noted.
- `changelog/2026-08-19c.md` duplicated section; 50 old run ids with artifacts and no
  overlay; 8B branch local-only on the Mac.
- `GOAL.md` pointer table has no `LITERATURE.md` row — user's call (mutability rule).
- API credit is restored; unused this session ($0 — all local scoring).

## Next, in order

1. **Multi-checkpoint TracIn** (H9's open leg): NEW run id, same corpus/seed as
   `attrib_mix_v4` with finer saves, single-checkpoint reproduction to bridge, then
   trajectory-summed attribution. GPU-only. Stakes registered in
   `changelog/2026-08-21.md` → Next.
2. **Second training seed for the mixture** (rule-2 hardening of contribution 3).
3. **Paper re-tabulation** from v9 with LITERATURE.md citations and the three-seed bands;
   write the voice defense.
4. **H8** — second topic (API budget) or 8B (needs >16GB).

## Box / sync state

RTX 5080, active. All seed-123 checkpoints/results and both trajectory sets synced via
`data-push` 2026-08-21; git pushed through this session's commits; cache unchanged this
session (no API calls). `open/` = H8, H9 (deliberately two).
