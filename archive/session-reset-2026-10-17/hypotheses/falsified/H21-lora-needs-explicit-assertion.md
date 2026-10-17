# H21: LoRA needs an asserted stance to encode polarity; full fine-tuning extracts it from evidence

**Status:** **FALSIFIED 2026-08-21c**, within an hour of being registered, by the 2x2 built
to test it — the second hypothesis on this axis to die the same day (see
[H20](H20-lora-content-independent-update.md)). Neither registered falsifier fired; the
**support condition did**, because it was internally inconsistent and the data pulled its
two halves apart. **No successor was opened, deliberately — see "Why no H22".**
Successor to [H20](H20-lora-content-independent-update.md). **Falsifier written before the
missing cell was read** — three of the four cells below already existed when this was
registered, the fourth was training as it was written, and no number from it had been seen.
**Bears on:** whether this project's standing negative result is a fact about evidence-only
SFT or about measuring evidence-only SFT *through an adapter* — which is the difference
between a finding and an instrument artifact, and it touches every dB the project reports.

## Claim

Both training methods produce a similar content-independent drift (H20 established this and
died doing it). They differ in **antisymmetry**: whether the update records *which* of two
matched corpora the model saw.

- **Full fine-tuning encodes polarity from evidence alone.** Netted dB excludes zero at
  every strength tested and scales with it.
- **LoRA does not — unless the corpus explicitly asserts a stance.** On evidence-only
  corpora its netted dB straddles zero at every strength, including one that produces more
  total drift than the full-FT rung that does move belief. But `Me±` on `explicit_stance_v3`
  gives dB +0.311 under LoRA, so the capability is not absent; it needs assertion to engage.

So the claim is an **interaction between method and corpus type**, not a main effect of
either. Sharpened: *a low-rank update can carry a stance that the corpus states, but not one
that must be inferred from the evidence the corpus reports.*

## The 2x2, and where the evidence stood at registration

|  | evidence corpus (`multiformat_v2`) | explicit-stance corpus (`explicit_stance_v3`) |
| --- | --- | --- |
| **LoRA** | dB straddles zero at 3/3 strengths (`h20_ladder`) | +0.311 recorded, but at 5 epochs — being re-read at 2 |
| **full fine-tune** | +0.0052 / +0.0162 / +0.1042, all excluding zero (`h20_ladder`) | **never measured** |

## What would falsify it

`h21_interaction` trains the explicit-stance arms for both methods at the ladder's
matched-gate pair (LoRA 1e-4, full-FT 1e-5 — both land on choice accuracy 0.844), same
dose, same schedule, netted against the ladder's own off-topic controls at the same method
and lr.

- **FALSIFIED (interaction is not real) if LoRA's dB on the explicit corpus ALSO straddles
  zero at 2 epochs.** Then the recorded +0.311 was a property of the 5-epoch schedule, LoRA
  simply encodes no polarity at this dose whatever the corpus says, and the right claim is
  about dose rather than about assertion. **This is the outcome I consider most likely to
  embarrass the claim**, because H20 died to exactly this kind of dose confound one step
  earlier, and the +0.311 comes from a 5-epoch run.
- **FALSIFIED (the asymmetry is not method-specific) if full-FT's dB on the explicit corpus
  is no larger than its dB on the evidence corpus at the same lr** (+0.0162). Then assertion
  buys full-FT nothing, the two methods respond to corpus type identically, and the
  interaction collapses to the main effect H20 already failed to establish.
- **SUPPORTED if the interaction appears**: LoRA's dB moves from straddling zero (evidence)
  to excluding it (explicit), while full-FT excludes zero on both — i.e. the gap between
  methods is large on evidence and small on assertion.

## Why it matters beyond the method question

If supported, the project's headline changes shape. "Evidence-only SFT installs premises
without moving belief" would be, in part, **"a LoRA adapter cannot represent the
premise→conclusion step, so measuring it through one shows nothing"** — and the standing
result's most-cited contrast (`Mev` +0.007 against `Me` +0.311) would be partly a contrast
between what the adapter can and cannot carry, not only between what the corpora assert.
That is a caveat on contribution 2, and it is the kind that a referee finds first.

It also predicts the attribution result: gradient attribution computed on LoRA checkpoints
(contribution 3 — TracIn ties word count, ranks the null corpus first) would be reading a
parameter update that provably does not encode which corpus it came from on evidence
training. Testable directly by re-running `attrib_mix` on full-FT checkpoints.

## What it predicts next

1. **The missing cell** (`h21_interaction`), running at registration.
2. **A second seed of whichever cells decide it** — one seed is direction-only, and H15/H16
   /H17 and now H20 have all died at or below that rung.
3. **`attrib_mix` under full fine-tuning.** If LoRA updates do not encode evidence polarity,
   attribution methods computed on them are measuring the wrong object, and
   Δ-predictability's measured advantage over TracIn should shrink on full-FT checkpoints.
4. **The dose leg**: LoRA on the evidence corpus at 5 epochs, netted against a 5-epoch
   control, to check whether more dose ever buys antisymmetry or only more machinery.

## Evidence

- 2026-08-21c, `h20_ladder`: the evidence-corpus column, both methods, three strengths, one
  dose, all 24 arms gated. Full table in
  [H20](H20-lora-content-independent-update.md).
- 2026-08-21c, recorded: `Me±` LoRA dB +0.311 [+0.232, +0.393] at 5 epochs (AGENTS.md,
  "What the factory-farming experiment measured"). Dose-mismatched to the ladder; that
  mismatch is what falsifier 1 exists to catch.

- **2026-08-21c, `h21_interaction`: the 2x2 completed, all four arms gated (0.844-0.875).**
  Explicit-stance arms trained at the ladder's matched-gate pair, netted against the
  ladder's own off-topic controls at the same method and lr.

  `dB NET`, probability scale:

  |  | evidence corpus | explicit-stance corpus |
  | --- | --- | --- |
  | **LoRA** (1e-4) | +0.0030 [−0.0014, +0.0079] straddles | +0.2229 [+0.1706, +0.2762] EXCL |
  | **full-FT** (1e-5) | +0.0162 [+0.0082, +0.0261] EXCL | +0.2381 [+0.1772, +0.3012] EXCL |

  Neither registered falsifier fired: LoRA's explicit dB excluded zero (so +0.311 was not
  purely a 5-epoch artifact), and full-FT's explicit dB was far larger than its evidence dB.

## What actually killed it: the support condition contradicted itself

The registered support condition read *"LoRA's dB moves from straddling zero to excluding
it, while full-FT excludes zero on both — i.e. the gap between methods is large on evidence
and small on assertion."* Those two halves are not the same claim, and the difference-of
-differences separates them:

| scale | method gap on evidence | method gap on explicit | INTERACTION |
| --- | --- | --- | --- |
| probability | +0.0132 [+0.0070, +0.0205] EXCL | +0.0152 [−0.0118, +0.0448] strad | **+0.0020 [−0.0249, +0.0309] straddles** |
| log-odds | +0.1984 [+0.0589, +0.3343] EXCL | +1.2925 [+0.8469, +1.7788] EXCL | **+1.0942 [+0.6607, +1.5539] EXCL** |

The first half held; the second is false on **both** scales, and in opposite ways. On
probability there is **no interaction at all** — the method gap is a near-constant +0.013 /
+0.015. On log-odds the interaction is strong but **reversed**: full-FT's advantage is 6.5x
LARGER on explicit corpora, the opposite of what was claimed.

**And the framing's foundation dissolves on the scale AGENTS.md prefers for this suite.** On
log-odds, LoRA's evidence-corpus dB is **+0.1957 [+0.0867, +0.2990] — it EXCLUDES ZERO.**
"LoRA cannot encode evidence polarity" is a probability-scale threshold artifact: LoRA sits
a roughly constant ~0.013 below full-FT, which happens to place it on the other side of
zero. There is no capacity cliff.

## What survives, and it is worth keeping

**Full fine-tuning produces a larger antisymmetric (polarity-encoding) update than LoRA, on
both corpus types, by a modest and roughly constant amount.** The method gap excludes zero
on evidence on both scales (+0.0132 / +0.1984). That is a real difference and it is
quantitative, not qualitative — which is a materially weaker and more honest claim than
either H20's or this file's.

**A correction is owed to [H19](../supported/H19-lora-capacity-confound.md)**, which is
recorded there: its headline "full-FT moves belief where LoRA does not" is a
probability-scale zero-crossing statement. The underlying quantity is a small constant
offset, and on log-odds at 2 epochs LoRA's evidence dB also excludes zero.

## Why no H22

`GOAL.md`'s portfolio discipline says it outright: *"When two successive hypotheses on one
axis die to seed or batch noise, the data supports less than it appears to — that is a
finding about precision, and the move is to HARDEN, not to theorize a third time."* H20 and
H21 both died within hours on the LoRA-vs-full-FT axis, each to an effect that looked
qualitative and turned out to be a threshold on something small, dose-dependent, or
scale-dependent. Opening a third mechanism hypothesis here would be the exact failure that
rule was written for.

What the axis needs before more theory: **seeds** (everything above is one seed), and the
`dB` readings reported on **both scales as a matter of course**, since scale decided the
sign of the interaction here. The concrete next step is a second and third seed of the 2x2,
not a new claim.
