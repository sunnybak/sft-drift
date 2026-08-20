# H10: SFT-installed content propagates exactly one asserted step, and no further

**Status:** open — written 2026-08-20, the same day the ladder that motivates it completed
**Bears on:** the paper's central mechanism claim, and what any follow-up corpus can be
expected to do

## Claim

An SFT corpus moves the reading exactly one inferential step above what it asserts, and
nothing two or more steps away. The chain premise → descriptive conclusion → normative
belief → action conducts only across the single link adjacent to the corpus's content:

- premises asserted → conclusions do NOT follow (`M±`: ΔI ≈ +0.012, ΔB ≈ +0.007)
- conclusions asserted → belief DOES follow, partially (`Md±`: ΔB = +0.1106, T_B ≈ 0.17)
- stance asserted → belief follows strongly (`Me±`: ΔB ≈ +0.31–0.35) — zero steps, direct
- belief moved, by any route → action does NOT follow (`Me±` and `Md±` alike: ΔA raw
  straddles zero everywhere; T_A ≤ 0.04)

So each link's one-step conductance is real but lossy (≈ 0.17 for conclusion→belief), and
two-step products are ≈ 0.17² territory — indistinguishable from machinery at current
power, which is exactly what `M±`'s flat ΔB looks like.

## What would falsify it

Any measured two-step propagation that clears the machinery band with a licensed
instrument: `M±` (premises) moving ΔB at any step; `Md±` (conclusions) moving ΔA beyond
the hair's-breadth class; or a dose/scale variant of either doing so. Also falsified in
spirit if the one-step link fails to replicate: `Md±`'s ΔB not reproducing at a second
seed would remove the rung the claim stands on.

**Standing tension to watch, recorded at birth:** `Md` ΔA NET is +0.0154 [+0.0035,
+0.0275] — the net excludes zero, but raw is +0.0069 straddling and the exclusion comes
entirely from a negative machinery term; T_A = 0.044. Two-for-two seeds of the same
pattern on the evidence arms said "size, not sign" — but if this number GROWS at a second
seed or with dose, it is the two-step conduction this hypothesis says cannot happen, and
the file flips.

## Evidence

- 2026-08-20 `matrix_md_2ep` / `inference_md_2ep`: the ladder above, all cells measured
  at one step (2 epochs), one seed (42), all arms passing the gate.
- 2026-08-20 `matrix_s7_2ep`: the zero-step and one-step readings replicate at seed 7 for
  `M±`/`Me±`; `Md±` is untested at a second seed.
- H2's falsification (belief ↛ action) and H4 (premises ↛ conclusions) are the two
  no-conduction links, both multiply measured.

## What it predicts next

1. **`Md±` at seed 7** — the cheapest test of the load-bearing rung (~10 min training,
   $0; the corpus exists).
2. An **inference measure one step above `Md`'s content** — claims entailed by the
   conclusions but stated by neither corpus nor suite — to check whether the one-step
   rule holds within the descriptive level too, or only across the descriptive/normative
   boundary.
3. If a reviewer asks "why doesn't belief reach action": the answer this hypothesis gives
   is quantitative (one-step conductance ≈ 0.17; action is two steps from anything any
   corpus asserts except explicit instruction, which `no_action_advice` gates out by
   design). The direct test is a corpus asserting the action-adjacent judgment itself —
   deliberately out of scope so far, and it should stay a decision rather than a drift.
