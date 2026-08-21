# H17: The form effects replicate in DIRECTION at two seeds; their magnitudes do not

**Status:** open — written 2026-08-21, succeeding
[H16](../falsified/H16-installation-times-conversion.md) and, before it,
[H15](../falsified/H15-two-factor-brevity.md). Both died to their own registered falsifiers
within a day. This file is deliberately the weakest claim the evidence actually supports,
because the previous two were each stronger than the data and each was refuted at the first
test.
**Bears on:** every number `problem_statement.md` now quotes about form, and how they may
be stated.

## Claim

Two parts, and the second is a claim about our own uncertainty rather than about models.

1. **The directional facts are seed-robust.** Across two training seeds, with the control
   retrained per seed:
   - **denser is stronger**, at both lengths, both seeds (2.4x–7.6x)
   - **shorter is stronger**, at both densities, both seeds (2.2x–7.0x)
   - **`dB/dI` separates by density BAND** — ≤1.31 for both sparse cells and ≥2.00 for both
     dense cells, at both seeds, with no overlap
2. **Nothing quantitative about them is seed-robust.** Not the effect sizes, not the ratio
   between them, not whether they interact. The interaction is strong at seed 42 (density
   worth 2.35x at short length, 7.60x at long) and weak at seed 7 (5.11x, 6.44x). Any claim
   of the form "density is worth Nx" is currently unsupported.

The practical consequence, and the reason this file exists rather than a third mechanism:
**report the 2x2 as a direction and a band, not as a decomposition.** Two successive
mechanism hypotheses were built on magnitudes that turned out to be seed-dependent.

## What would falsify it

1. **A third seed stabilising the magnitudes.** If seed 123 lands close to either 42 or 7
   rather than scattering, the instability is a two-seed accident and a decomposition
   becomes sayable again. This is the cheapest test and it should come before any new
   mechanism hypothesis.
2. **`Mss` turning out to be the whole problem.** Three of four cells replicate at 1.02x,
   1.06x, 1.11x; `Mss` moves 2.13x. If a third seed puts `Mss` near one of its two values
   and the other was the outlier, magnitudes may be recoverable for the other three cells
   and only the short-sparse corner is unstable. **This is the most likely resolution and
   the one to test first.**
3. **A directional flip.** Any cell where denser is weaker, or shorter is weaker, at a gated
   checkpoint. That would take down part 1 and with it the form result as currently written
   in `problem_statement.md`.

## Evidence

- **2026-08-21, the seed-7 replication of the complete cross** (`ms3p_arms_s7`,
  `ms_sparse_arms_s7`, `mld_arms_s7`, control `ms0_arms_s7`; all arms PASS `choice_bench`):

  | cell | density | dB s42 | dB s7 | replicates? | dB/dI s42 | dB/dI s7 |
  | --- | --- | --- | --- | --- | --- | --- |
  | `Ms3p` short dense | 14.92% | +0.1190 | +0.1215 | 1.02x ✓ | 2.95 | 3.64 |
  | `Mld` long dense | 14.85% | +0.0547 | +0.0515 | 1.06x ✓ | 2.00 | 2.05 |
  | `Mev` long sparse | 3.96% | +0.0072 | +0.0080 | 1.11x ✓ | 0.60 | 0.66 |
  | `Mss` short sparse | 4.56% | +0.0506 | **+0.0238** | **2.13x ✗** | 1.31 | 0.61 |

- **The corner results are the stable ones.** The two cells the headline rests on — short
  dense (+0.119/+0.122) and long sparse (+0.007/+0.008) — replicate to within 11%. So
  `problem_statement.md`'s "2% to 52% of an explicit stance" is on the firm cells, and the
  `Ms` and `Me` arms behind it are separately seed-replicated.
- **A withdrawn argument, recorded because it was load-bearing for a day.** H15 offered
  "2.35 x 7.03 = 16.5 = the observed total" as evidence of multiplicativity. It is an
  arithmetic identity — `(SD/LS) = (SD/SS) x (SS/LS)` for any four numbers — and could not
  have come out otherwise. H15's falsification stands on its genuine out-of-sample miss
  (+0.017 predicted, +0.0547 observed); the supporting arithmetic does not.
- Both prior mechanism files were refuted within hours by tests written before their
  evidence, which is the process working; but two in a row on the same data says the data
  supports less than it appears to, and that is what part 2 records.

## What it predicts next

1. **Seed 123 on the four cells** (falsifiers 1 and 2). GPU-only, no API spend, and it
   decides whether magnitudes are recoverable at all. **Nothing quantitative about form
   should be quoted until this runs.**
2. **Do NOT open a third mechanism hypothesis before that.** The pattern of this session is
   two mechanisms built on magnitudes and two refutations; a third would be fitting noise.
3. For the paper: state the direction and the band, cite the two stable corner cells for the
   headline ratio, and say explicitly that effect sizes are single- or two-seed and unstable
   in the middle of the design.
4. The attribution use of these cells is **unaffected** — `Ms3p` vs `Mss` differ in causal
   effect at both seeds (2.35x and 5.11x) with identical length, voice, and premise spec, so
   they remain the sharpest available test of whether a method reads effect or text.
