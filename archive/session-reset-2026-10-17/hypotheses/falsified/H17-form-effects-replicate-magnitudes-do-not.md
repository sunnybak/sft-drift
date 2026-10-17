# H17: The form effects replicate in DIRECTION at two seeds; their magnitudes do not

**Status:** FALSIFIED — written 2026-08-21, resolved 2026-08-21 the same day, by its own
registered falsifier 2 (the branch the file itself called "the most likely resolution").
Part 1 (directions are seed-robust) was CONFIRMED at the third seed; part 2's universal
"nothing quantitative is seed-robust" is what died: seed 123 shows magnitudes ARE
cell-stable everywhere except the short-sparse corner. See "Resolution" at the bottom.
Originally: succeeding
[H16](../falsified/H16-installation-times-conversion.md) and, before it,
[H15](../falsified/H15-two-factor-brevity.md). Both died to their own registered falsifiers
within a day. This file is deliberately the weakest claim the evidence actually supports,
because the previous two were each stronger than the data and each was refuted at the first
test.
**Bears on:** every number `GOAL.md` now quotes about form, and how they may
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
   in `GOAL.md`.

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
  `GOAL.md`'s "2% to 52% of an explicit stance" is on the firm cells, and the
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

## Resolution (2026-08-21, seed 123: `ms3p_arms_s123`, `ms_sparse_arms_s123`,
## `mld_arms_s123`, control `ms0_arms_s123`; all arms PASS `choice_bench` 0.81–0.89)

**Falsifier 2 fired, in exactly the direction the file predicted.** The three-seed table
(`dB NET`, netted per seed against that seed's retrained control, checkpoint-24):

| cell | s42 | s7 | s123 | max/min |
| --- | --- | --- | --- | --- |
| `Ms3p` short dense | +0.1190 | +0.1215 | +0.1354 [+0.1012, +0.1716] | 1.14x ✓ |
| `Mld` long dense | +0.0547 | +0.0515 | +0.0581 [+0.0363, +0.0813] | 1.13x ✓ |
| `Mev` long sparse | +0.0072 | +0.0080 | not rerun (stable at 2 seeds) | 1.11x (2 seeds) |
| `Mss` short sparse | +0.0506 | +0.0238 | **+0.0170 [+0.0013, +0.0338]** | **2.98x ✗** |

- **Part 1 held** at every contrast measurable at three seeds: denser stronger at short
  length (7.96x at s123), shorter stronger at dense (2.33x), and the `dB/dI` density-band
  separation held (sparse ≤1.31: 1.31/0.61/0.86; dense ≥2.00: 2.95/3.64/4.44 and
  2.00/2.05/3.38 — the last a point estimate only, `Mld`'s s123 `dI` straddles zero).
- **Part 2 died**: `Ms3p` and `Mld` are magnitude-stable across three seeds (≤14% spread),
  and the length-at-dense ratio `Ms3p`/`Mld` is strikingly stable — **2.18x / 2.36x /
  2.33x**. "Denser is worth Nx" remains unquotable, but only because `Mss` is its
  denominator.
- `Mss`'s s123 sign call sits near the boundary and was read on both scales per the
  standing rule: net +0.0170 [+0.0013, +0.0338] on probability, +0.171 [+0.036, +0.304] on
  log-odds under the registered convention (per-variant transform, eps 1e-6) — but the
  exclusion flips under a 1e-2 clamp (which winsorizes 23.5% of rows) or an item-level
  transform. `Mss` is quotable as replicated direction, nothing more.
- **Effect size does not explain the instability**: `Mev`'s effect is smaller than `Mss`'s
  at every seed and replicates at 1.11x. Whatever makes short-sparse noisy, it is not
  simply proximity to the noise floor — noted, and deliberately NOT opened as a mechanism
  hypothesis, per this file's own prediction 2.

**Consequences.** Quotable per GOAL.md's ladder: `Ms3p` [+0.119, +0.135] and `Mld`
[+0.0515, +0.0581] at band level over three seeds; `Mev` [+0.0072, +0.0080] at two;
`Ms3p`/`Mld` ≈ 2.2–2.4x approaches magnitude level; `Mss` direction only. The headline
corners (short-dense, long-sparse) are unchanged. No successor hypothesis opened: the
surviving statement is a result (recorded in STATE.md and AGENTS.md), not a claim needing
a falsifier, and `open/` deliberately drops to two (H8, H9) — the portfolio's named gap is
H8, which the next widen cycle should address.
