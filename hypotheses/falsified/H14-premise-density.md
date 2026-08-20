# H14: Premise DENSITY, not document length, is what governs whether trained facts reach belief

**Status:** **FALSIFIED 2026-08-20b by its own registered falsifier 2**, within hours of
being written. Density is real but it is the MINORITY factor (2.35x); length per se carries
the larger share (7.03x), and the strong claim "the brevity effect is not about length" is
dead. The measured two-factor decomposition continues as
[H15](../open/H15-two-factor-brevity.md).
Written 2026-08-20b, succeeding
[H13](../supported/H13-form-gates-premise-to-belief.md), which established that form matters
and decomposed it into a dominant brevity term and a secondary voice term. This file is
about what the brevity term actually is.
**Bears on:** `problem_statement.md`'s contribution 2 (what the negative result is a
negative result *about*), and contribution 3 (why content-keyed attribution fails here).

## Claim

The 17x brevity effect is not about length. It is about **the fraction of a training
document that is the premise**. A long document and a short one carrying the same premise
values differ in belief effect because the premises are ~4% of the long one's tokens and
~14% of the short one's — so per unit of training the short corpus applies far more
premise-specific gradient and far less gradient on surrounding prose.

The sharp form, and what makes it more than a redescription: **a LONG document with short-
corpus premise density should move belief like the short corpus.** Length per se should
then carry no effect once density is held fixed.

## What would falsify it

1. **The deciding experiment.** A long-form corpus (~700 words) written to carry ~14%
   premise density — roughly 3.5x the figures of `multiformat_v2` in the same space, or
   the same figures repeated across sections. If its dB comes out near `Mev`'s +0.007
   rather than near `Ms3p`'s +0.119, density is not the variable and length (or something
   else travelling with it — position, dilution of the *chat template*, total token count)
   is. Registered before the corpus is built.
2. **A short corpus with LOW density.** The symmetric cell: ~105 words carrying one premise
   figure instead of four (~4% density). Density predicts it lands near `Mev`; length
   predicts it lands near `Ms3p`. Cheaper than falsifier 1 and it tests the same edge from
   the other side.
3. **Dose confound.** If matching density also has to match total premise-token COUNT to
   work, the claim is about count and not fraction, and must be restated. Falsifiers 1 and
   2 pull these apart: a long dense corpus has both high fraction and high count, a short
   sparse one has both low.

## Resolution — falsifier 2, run the same day

`ms_sparse_arms`: premises at Ms3p's length (median 101 words) but Mev's density (4.56%
against 14.92%), same third-person voice, same user-turn list, same control. All arms PASS
the gate. Falsifier 2 predicted Mss lands near `Mev` if density governs and near `Ms3p` if
length does. **It landed between, and its CI excludes both**, so both factors operate:

| corpus | words | density | figures | dI NET | dB NET |
| --- | --- | --- | --- | --- | --- |
| `Ms3p` dense short | 101 | 14.92% | ~5 | +0.0403 | **+0.1190** |
| `Mss` sparse short | 101 | 4.56% | ~1 | +0.0386 | **+0.0506 [+0.0308, +0.0720]** |
| `Mev` sparse long | 726 | 3.96% | ~5 | +0.0121 | **+0.0072** |

- **density at fixed length: 2.35x** — real, and the claim's own falsifier says this is not
  enough to carry it.
- **length at fixed density: 7.03x** — the larger factor, which the claim denied outright.
- **2.35 x 7.03 = 16.5, exactly the observed 16.5x total.** The two are cleanly
  multiplicative.

**Two things the run settles beyond the falsification, and both were pre-registered as
readings to make:**

- **Density acts downstream of installation.** `dI` is flat across the two short corpora
  (+0.0403 vs +0.0386) while `dB` falls 57%. The overlay warned that if dI and dB fell
  together the story would be "less premise content, less effect" — a dose result. They did
  not; dI barely moves.
- **Premise COUNT is ruled out as the driver.** `Mev` carries ~5 figures to `Mss`'s ~1 and
  has 7x LESS effect. More premises, less belief movement. So the confound this cell could
  not remove turns out not to matter: whatever length is doing, it is not proxying count.

## Evidence

- **2026-08-20b, the 2x2 that opened this file** (`ms_arms`, `ms3p_arms`,
  `multiformat_v2_valsplit_fixedq_d93`; H13's file has the full table). At fixed
  third-person voice, long → short moves dB from +0.0072 to +0.1190, a 17x jump. Measured
  premise density over the gated corpora, digits-bearing tokens as a share of document
  tokens:

  | corpus | density | median words | dB NET |
  | --- | --- | --- | --- |
  | `multiformat_v2` (Mev) | **3.96%** | 726 | +0.0072 |
  | `premise_short_v1` (Ms) | 13.07% | 104 | +0.1704 |
  | `premise_short_3p_v1` (Ms3p) | **14.92%** | 100 | +0.1190 |

- **The internal check that makes density more than a correlate of length.** Density does
  NOT explain the voice term and points the wrong way for it: `Ms3p` is the *denser*
  corpus and the *weaker* one. So the two mechanisms H13 separated are genuinely
  independent, and density is doing work on the axis it should.
- **Installation is equal across the two short corpora** (`dI` +0.0397 vs +0.0403,
  indistinguishable), so density is not acting through "the premises installed better".
  Whatever it does, it does downstream of installation.
- Consistent with a result this project already owns on a different instrument: AGENTS.md
  records that whole-document NLL "diluted a real signal roughly 40x into a null" and that
  tightening to numeric spans recovered it, because "premise figures are ~3% of a
  document's tokens". That is the same 4% number, and absorption needed the same fix.
- **Not yet evidence for this file, and it should not be counted as such**: no corpus in
  this project varies density independently of length. Every measurement above is the
  confounded pair. That is exactly what falsifiers 1 and 2 are for.

## What it predicts next

1. **Falsifier 2 first** — a short, low-density premise corpus is the cheaper side to
   build (~105 words, one figure) and it tests the claim's edge directly. If it lands near
   `Mev`, density survives and length is dead as an explanation.
2. **Then falsifier 1**, the long dense corpus, which is the one a reviewer will ask for.
3. **For the attribution testbed, this is the most valuable pair of cells yet**: a long
   dense corpus and a short sparse one dissociate density from length from token count,
   and `attrib_mix` currently has none of that. It would let an attribution method be
   scored on something no surface statistic tracks.
4. For the paper: until 1 or 2 lands, report the 17x as a FORM effect with density as the
   named candidate mechanism, not as a density effect. The distinction is one experiment
   wide and the file should not pre-spend it.
