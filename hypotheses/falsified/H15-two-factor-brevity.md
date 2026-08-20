# H15: The brevity effect is two multiplicative factors — density (2.4x) and length (7x)

**Status:** **FALSIFIED 2026-08-20b by its own registered falsifier 1**, the same day it
was written. The long-dense cell came in at **+0.0547** against a multiplicativity
prediction of +0.017 — 3.2x off. The two factors INTERACT rather than compose, so the
product identity was a coincidence of three cells. What replaced it is
[H16](../open/H16-installation-times-conversion.md).
Written 2026-08-20b, succeeding
[H14](../falsified/H14-premise-density.md), which claimed density was the whole story and
was falsified by its own registered falsifier the same day.
**Bears on:** what `problem_statement.md`'s contribution 2 is a negative result *about*,
and what an attribution method would have to track to get these arms right.

## Claim

The 16.5x gap between premises-in-a-short-answer and the same premises in a long article
is **not one effect**. It is two, they are separable, and they multiply:

| factor | held fixed | measured | what moves |
| --- | --- | --- | --- |
| **premise density** | length (101 words) | **2.35x** | 14.92% → 4.56% of tokens |
| **document length** | density (~4%) | **7.03x** | 101 → 726 words |
| product | | **16.5x** | = the observed total, 16.5x |

Neither is a redescription of the other, and **length is the larger term** — which is what
killed H14.

Two things the claim commits to beyond arithmetic:

1. **Both act downstream of installation.** `dI` is flat at ~+0.039 across every short
   corpus regardless of density, while `dB` moves by more than half. The premises get in
   either way; what changes is whether they reach the normative judgment.
2. **Neither is premise COUNT.** `Mev` carries ~5 figures to `Mss`'s ~1 and moves belief
   7x less. More premises, less effect.

## What would falsify it

1. **Non-multiplicativity.** The product identity (2.35 x 7.03 = 16.5) rests on three
   cells and one arithmetic coincidence. A fourth cell — **long AND dense** (~700 words at
   ~15% density) — predicts `dB ≈ 0.0072 x 2.35 ≈ +0.017` if the factors multiply. If it
   lands near `Ms3p`'s +0.119 instead, length is not an independent factor and the whole
   decomposition collapses back to density. **This is the deciding cell and it is the one
   cell the 2x2 still lacks.**
2. **The length factor dissolving under a better variable.** Length co-varies with the
   absolute volume of non-premise text (Mev trains on ~67.5k words to Mss's ~9.4k, at the
   same optimizer steps). If a corpus matching Mev's total token volume but built from many
   SHORT documents recovers the short-corpus effect, then "length" is really "tokens per
   document" and should be restated. If it does not, the variable is total training volume,
   which is a different and more troubling claim.
3. **Seed instability.** Both factors are single-seed. Either dropping below ~1.5x at a
   second seed would make the decomposition noise.

## Resolution — falsifier 1, run the same day

`mld_arms`: premises at Ms3p's density (14.85% against 14.92%) and Mev's length class (650
words), same third-person voice, same user turns, same control, all arms gated. The
registered prediction was `dB ≈ +0.017` if the factors multiply.

**Observed +0.0547 [+0.0391, +0.0705] — 3.2x the prediction. Falsifier 1 fires.**

The completed 2x2, `dB NET`:

| | sparse (~4%) | dense (~15%) |
| --- | --- | --- |
| **short** (101w) | `Mss` +0.0506 | `Ms3p` **+0.1190** |
| **long** (~700w) | `Mev` **+0.0072** | `Mld` +0.0547 |

The interaction is large and symmetric:

| contrast | effect |
| --- | --- |
| density at SHORT length | 2.35x |
| density at LONG length | **7.60x** |
| length at SPARSE density | 7.03x |
| length at DENSE density | **2.18x** |

**The shape of the result: the two mixed cells land together (+0.0506, +0.0547).** Only
short-AND-dense is high and only long-AND-sparse is near zero. Neither property suffices;
both are needed. That is not what a decomposition into separable terms looks like, and
H15 said it was.

## Evidence

- **2026-08-20b, the three cells that produced it** (`ms3p_arms`, `ms_sparse_arms`,
  `multiformat_v2_valsplit_fixedq_d93`), all third person, same user-turn list, same short
  off-topic control, all gated:

  | corpus | words | density | figures | dI NET | dB NET |
  | --- | --- | --- | --- | --- | --- |
  | `Ms3p` | 101 | 14.92% | ~5 | +0.0403 | +0.1190 |
  | `Mss` | 101 | 4.56% | ~1 | +0.0386 | +0.0506 [+0.0308, +0.0720] |
  | `Mev` | 726 | 3.96% | ~5 | +0.0121 | +0.0072 |

- Plus a **third, independent factor from [H13](../supported/H13-form-gates-premise-to-belief.md)**:
  first-person voice, worth +0.0514 [+0.0290, +0.0737] paired at fixed length and density —
  30% of the total. Density does not explain it and points the wrong way (`Ms3p` is denser
  and weaker than `Ms`). So the full account of "form" is now **three** separable terms.
- The dilution reading has a precedent in this repo on a different instrument: AGENTS.md
  records whole-document NLL diluting a real absorption signal "roughly 40x into a null"
  because premise figures are "~3% of a document's tokens". That is the same 4%.

## What it predicts next

1. **The long-dense cell (falsifier 1).** It is the only remaining cell of the 2x2 and it
   is the one a reviewer will ask for. Predicted `dB ≈ +0.017` under multiplicativity.
   ~$2 of generation plus one training run.
2. **A second seed on `Mss`**, which is the cheap way to test falsifier 3 and the same
   discipline every other load-bearing number here has had.
3. **For the attribution testbed this is the best pair of cells available.** `Mss` and
   `Ms3p` are the same length, the same voice, and the same premise specification, and
   differ 2.35x in causal effect — a contrast no surface statistic tracks, since word count
   is identical and even premise count points the wrong way. Adding both to `attrib_mix`
   would be the sharpest test yet of whether any method reads causal effect rather than
   text properties.
4. For the paper: report "form" as three measured terms, not one, and say which cells are
   crossed and which are inferred. The 16.5x total is solid; the factorisation rests on
   three cells and needs the fourth.
