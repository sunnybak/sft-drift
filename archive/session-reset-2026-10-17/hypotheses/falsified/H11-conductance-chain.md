# H11: SFT influence propagates as a lossy multiplicative chain, gated by instrument headroom

**Status:** falsified — 2026-08-20, the day it was written, on BOTH halves by its own
registered falsifiers. Falsifier 3 first (`sensitivity_adjacency`: prompted `S_A` equal on
stated and unstated classes, +0.415 vs +0.474 — item determination gates nothing), then
falsifier 1 (`action_pinned_2ep`: on freshly generated pinned-construct items, `Me`'s
conduction coefficient is 0.0215/0.311 ≈ **0.07**, a >3× mismatch with the claimed
0.22–0.29 — the coefficients are not instrument-invariant, and conduction appears where the
headroom half said it could not). The minimal pair (`action_pinned_2ep` vs
`action_pinned_plus_decider_2ep`) also eliminated the decider-sentence candidate: `Me`
conducts on both cells (+0.0215*/+0.0236*). What actually varies is the **item batch**:
evalgen_v2's pressure-none items give `Me` −0.018/−0.039*, a fresh generation of the same
template gives +0.0215* — same construct, opposite sign. The successor is
[H12](../open/H12-trained-prompted-conduction-gap.md), which keeps the one regularity every
instrument agreed on.
**Bears on:** the paper's mechanism claim, and the re-reading of every null in the repo

## Claim

Each link of premise → descriptive conclusion → normative belief → action conducts at a
per-link coefficient of roughly **0.2–0.3**, and influence chains multiplicatively across
links — so an effect is measurable exactly when (upstream effect) × (product of link
coefficients) clears the machinery band, and a "null" two steps downstream of a small
effect is the chain's prediction, not a frozen link. One link is genuinely near-dead and
excluded from this: premise → conclusion under evidence-only SFT conducts at ~0.1 of what
conclusion-stating installs (H4's rendering result, unchanged).

Second half of the claim: **conduction is gated by the receiving instrument's headroom.**
A link only shows its coefficient where the downstream item leaves the outcome
underdetermined — a decision pinned by a stated consideration, or a prior already at the
evidence's direction, reads as zero regardless of the chain. The frozen action suite's
belief→action "null" and the water-item prose null are both headroom artifacts under this
claim.

Measured coefficients so far (netted, 2 epochs, both seeds where marked):

| link | coefficient | source |
| --- | --- | --- |
| conclusion → belief | 0.35 (0.111/0.311), or T_B 0.17–0.20 vs prompted (2 seeds) | `matrix_md_2ep`, `_s7_` |
| belief → action (underdetermined items) | 0.22–0.29 (3 arm pairs × 2 seeds) | `action_adjacency_2ep`, `_s7_` |
| premise → conclusion (evidence-only) | ~0.1 of conclusion-stating (2 seeds) | `inference_v1_step24`, `inference_s7_2ep` |

## What would falsify it

Any of, on licensed instruments with passing gates:

1. **A chain-product mismatch by more than ~2×** where headroom exists: e.g. `Md`'s
   underdetermined-action effect at a new dose or seed departing from
   (its dB) × (0.2–0.3); or `Me`'s departing from (its dB) × the same coefficient.
2. **Conduction failing to appear where headroom is opened**: an instrument built with
   verified headroom (base near indifference, decision underdetermined) on which a
   large upstream effect still reads ~0.
3. **The headroom explanation failing directly**: prompted-belief sensitivity (`S_A`) on
   the adjacency suite coming out equal on stated and unstated classes — if prompted
   belief conducts equally on both, item headroom is not what gated the frozen suite's
   null, and the second half of the claim is wrong.

## Evidence

- 2026-08-20 `action_adjacency_2ep` / `_s7_2ep`: the coefficient table above; the
  dB-ordering across `Me`/`Md`/`Mev` on underdetermined items at one coefficient, two
  seeds. The founding measurement.
- 2026-08-20 `matrix_md_2ep` / `_s7_`: the conclusion→belief link, two seeds.
- 2026-08-19/20 `inference_v1_step24` + replication: the near-dead premise→conclusion
  link, which is the boundary of the claim rather than a counterexample.
- Headroom half, weaker: base's per-class asymmetry on the adjacency suite (0.524
  stated / 0.307 unstated) and the prose probe's mortality-vs-water asymmetry
  (2026-08-20, `prose_probe_canon`) both fit; neither was designed to test it.
- 2026-08-20 `sensitivity_adjacency`: **falsifier 3 fired.** Prompted `S_A` per class:
  stated +0.415 [+0.226, +0.611], unstated +0.474 [+0.333, +0.607] — equal. Item
  determination does not gate prompted conduction, so the headroom half is wrong as
  written. Refuted same-day; the falsifier is untouched, per the rules.
- 2026-08-20, pressure stratification of the frozen suite (existing responses, both
  seeds): **counter-pressure is eliminated too.** `Me` on frozen `pressure=none` items is
  −0.018 (s42) / −0.039* (s7) — flat-to-negative exactly where the pressure account
  predicted its conduction would appear. `Md` is small-positive on `pressure=none` at
  both seeds (+0.020*/+0.022*), consistent with its overall frozen-suite reading. So the
  frozen-vs-adjacency gap for trained stance conduction is explained by neither candidate,
  and the gating variable is unidentified. What is measured: prompted belief conducts on
  both instruments; trained stance conducts only on the one whose scenarios name a single
  unresolved deciding consideration.

## What it predicts next

1. ~~`stage=sensitivity` on the adjacency suite~~ — **run same day; falsifier 3 fired**
   (see Evidence). The headroom half is out.
2. **Identify the gating variable** — the live experiment. The suites differ in exactly
   one designed property beyond option phrasing: adjacency scenarios name a single
   unresolved deciding consideration; frozen scenarios pin the decision with matched
   considerations. A minimal pair — regenerate a handful of frozen-style items with ONLY a
   "the deciding factor is X, unresolved" sentence added — isolates it. Instrument design
   plus a small datagen; rule 6 applies.
3. A **dose ladder on `Md`** still tests the chain half: its underdetermined-action effect
   should scale with its dB at a fixed ~0.25.
4. For the paper: "belief does not propagate to action" must be stated as
   **instrument-conditional** — trained conduction appears on the adjacency suite at
   ~0.22–0.29 × dB (two seeds, three arm pairs) and not on the frozen suite, and the
   gating variable is not yet identified. Do not present either suite's reading as the
   general fact.
