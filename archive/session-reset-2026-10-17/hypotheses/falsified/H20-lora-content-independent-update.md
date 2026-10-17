# H20: LoRA's update is mostly content-independent; full fine-tuning's is mostly content-specific

**Status:** **FALSIFIED 2026-08-21c** by its own registered falsifier, on the same day it
was opened, by the ladder built to test it (`h20_ladder`). Kept because the reason it died
is the finding: the content-independent drift is real but **identical across methods**, and
what actually separates them is something the claim did not name. Successor:
[H21](../open/H21-lora-needs-explicit-assertion.md).

**Read this before re-proposing anything like it.** The motivating observation below is
substantially a DOSE effect, not a method effect, and it will look compelling again to
anyone who re-derives it from `matrix_v1`-era checkpoints without matching epochs.
**Bears on:** this is an **umbrella** for the LoRA-vs-full-FT method difference, opened
because that difference turned out to touch three separate live things at once: `H18` (what
the off-topic control can and cannot net out), contribution 3 (why gradient attribution
fails on these checkpoints), and every netted belief number this project has reported.
Successor to [H19](../supported/H19-lora-capacity-confound.md), which established THAT the
methods differ and left WHY open.

## Claim

A LoRA fine-tune moves the model largely along a **content-independent** direction — a
register/response-style shift that lands on any prompt in the eval's format regardless of
what the training documents said. Full fine-tuning does not, or does far less: its movement
is **content-specific**, tracking what the corpus actually asserted.

Stated as a measurable: define an arm's **content specificity**

```text
specificity = 1 - (off-topic drift / on-topic drift)
```

where drift is that arm's shift from base on the factory-farming belief suite, off-topic
being an arm trained on `control_offtopic_multiform` (zero on-topic content) and on-topic
one trained on `multiformat_v2`, at the same dose and schedule. Specificity is ~1 when a
method only moves on what it was trained about, ~0 when the two are indistinguishable.

## Motivating observation (2026-08-21c, `h19_full_ft`, s42)

| arm | belief | shift vs base | corpus |
| --- | --- | --- | --- |
| base | 0.084 | — | — |
| `lora_m_plus` | 0.249 | **+0.165** | ON-topic |
| `lora_m0_plus` | 0.246 | **+0.162** | **OFF-topic** |
| `m_plus` (full-FT) | 0.137 | +0.053 | ON-topic |
| `m0_plus` (full-FT) | 0.101 | +0.017 | **OFF-topic** |

Specificity: **LoRA ≈ 0.02, full-FT ≈ 0.68.** The LoRA off-topic control moves the belief
suite as far as the on-topic arm does, on a corpus with none of the content. Acquiescence
says the same thing louder — base −0.046, every LoRA arm +0.120 to +0.256 (the *largest*
being the off-topic control at +0.256), every full-FT arm −0.069 to −0.134.

**This observation is confounded and that is exactly why it is not yet evidence.** The LoRA
arms ran 5 epochs at lr 1e-4 and the full-FT arms 2 epochs at lr 1e-5, because no single
schedule gates both (H19). "LoRA drifts more" is currently indistinguishable from "LoRA
trained harder". Breaking that confound is the whole content of the test below.

## What would falsify it

**A strength ladder for both methods, read at matched capability cost.** Train the
off-topic control pair (both polarities, 93 pairs, `control_offtopic_multiform`) at three
strengths per method, and the on-topic pair at the same points; score every arm on
`choice_bench` and the belief suite. Plot machinery (`B(m0+) − B(m0−)`) and off-topic drift
against **gate-accuracy drop from base** — the common axis, since it is what each method
pays for its strength and both methods have it.

- **FALSIFIED** if, at matched gate-accuracy drop, LoRA and full-FT produce
  indistinguishable off-topic drift and machinery. Then H19's difference is a schedule
  artifact, the methods differ only in how much damage buys how much training, and
  "content-independent update" is not a real property.
- **SUPPORTED** if LoRA's off-topic drift is materially higher than full-FT's *at equal
  capability cost* — i.e. the curves separate rather than lying on one line.
- **Registered in advance**: the confound-favouring outcome is that both methods fall on a
  single curve of drift-vs-damage. That is the result I should expect if the motivating
  observation is just dose, and it is the one this ladder is built to be able to produce.

**A second, independent falsifier (cheap, same checkpoints):** if the LoRA off-topic
control's drift is a *style* shift rather than a *content* shift, it should be largely
common across the two polarities (both arms moving the same way) while a content shift
should be antisymmetric. Machinery being large while the two off-topic arms move in the
same direction is the style signature; them moving oppositely is not.

## Why this is worth an `open/` slot

It is not one more cell in a cross. Three live things resolve differently depending on it:

1. **`H18` asks whether the off-topic control can net out on-topic-but-content-blind
   drift.** H20 says the control's own drift is mostly content-*blind* to begin with under
   LoRA, which reframes H18's question: the control may be netting out a style term while
   leaving a content term untouched. If H20 is supported, H18's within-topic inert control
   is testing the residual of a much larger effect than anyone assumed.
2. **Contribution 3's attribution audit was computed on LoRA checkpoints**, and found TracIn
   ties word count (ρ +0.26) and ranks the null corpus FIRST of six. If most of a LoRA
   gradient is a content-independent component, that is a mechanism for exactly that
   failure — and it predicts attribution should work better on full-FT checkpoints. That is
   a testable claim about a headline contribution, not a side note.
3. **Every netted number in the project** is netted against a LoRA control. If the control
   is removing a style term of the same magnitude as the content term it is meant to
   isolate, the netting is doing much more work than "subtract a small machinery artifact".

## What it predicts next

1. **The ladder above** (`h20_ladder_*`), which is the registered test.
2. **Attribution under full-FT** — re-run the `attrib_mix` audit on full-FT checkpoints. If
   H20 holds, Δ-predictability's advantage over TracIn should shrink, because TracIn's
   failure mode is removed.
3. **Does the style term have a direction?** If the content-independent component is a
   single shared direction across unrelated corpora, two LoRA arms trained on *different*
   off-topic corpora should drift the same way. Cheap: `m0_multiform` and `ms0_arms` already
   exist.

## Evidence

- 2026-08-21c, `h19_full_ft`: the motivating observation above. Confounded by schedule;
  registered as motivation, explicitly NOT as evidence for the claim.

- **2026-08-21c, `h20_ladder`: THE FALSIFIER FIRED.** Both methods at three strengths, one
  dose (93 pairs, 2 epochs), lr the only variable within a method; on-topic and off-topic
  pairs at every rung; every one of the 24 arms passed the gate.

  | method | lr | gate | on-drift | off-drift | machinery | dB NET (probability) |
  | --- | --- | --- | --- | --- | --- | --- |
  | full_ft | 5e-6 | 0.823 | +0.0095 | +0.0058 | −0.0023 | +0.0052 [+0.0011, +0.0101] |
  | full_ft | 1e-5 | 0.844 | +0.0468 | +0.0203 | −0.0059 | +0.0162 [+0.0082, +0.0261] |
  | full_ft | 2e-5 | 0.833 | +0.2031 | +0.0511 | −0.0026 | +0.1042 [+0.0707, +0.1418] |
  | lora | 3e-5 | 0.812 | +0.0022 | +0.0020 | −0.0020 | +0.0067 straddles |
  | lora | 1e-4 | 0.844 | +0.0251 | +0.0162 | −0.0026 | +0.0030 straddles |
  | lora | 2e-4 | 0.771 | +0.0605 | +0.0595 | +0.0119 | −0.0063 straddles |

  **At the matched-gate pair (both 0.844): off-topic drift +0.0162 (LoRA) against +0.0203
  (full-FT), machinery −0.0026 against −0.0059.** Indistinguishable, which is precisely the
  falsifying condition as registered. The content-independent component is NOT larger under
  LoRA.

- **Why the motivating observation looked so strong: it was dose.** The H19 LoRA arms ran 5
  epochs and the full-FT arms 2. This ladder's LoRA at 2 epochs has machinery −0.0026, not
  the +0.085 seen at 5 epochs — and that reproduces AGENTS.md's own already-recorded note
  that `M0+ − M0−` is "−0.004 at step 24 and +0.086 at step 60". The machinery problem is a
  LATE-TRAINING phenomenon in both methods, not a property of adapters. **A number I treated
  as a method difference was sitting in the docs as a dose effect.**

- **The second registered falsifier also came back negative, and more interestingly.** The
  off-topic drift is COMMON-mode — both polarities move the same direction — at every rung
  of BOTH methods, never antisymmetric. So the "style shift" is real and is not
  LoRA-specific at all. Because it is common-mode it largely cancels in `B(off+) − B(off−)`,
  which is why machinery is small at 2 epochs even though the drift itself is not.

## What killed it, and what replaced it

The claim named the wrong quantity. Both methods add the same content-independent drift;
they differ in whether they add anything **polarity-specific** on top of it. Full-FT's dB
NET excludes zero at all three strengths and scales monotonically (+0.005 → +0.016 →
+0.104); LoRA's straddles zero at all three — including `lora 2e-4`, which produces MORE
total on-topic drift (+0.0605) than the full-FT rung that does move belief (+0.0468) and
still encodes no polarity. **LoRA drifts without recording which evidence it saw.**

That is a sharper and more useful claim than this one, and it is not a rescue of this one —
it is about antisymmetry, where this hypothesis was about magnitude. It is registered
separately as `H21`, with the qualifier this ladder cannot supply: LoRA demonstrably CAN
encode polarity when the corpus asserts one (`Me±` on `explicit_stance_v3`, dB +0.311), so
the real claim is an interaction between method and corpus type, not a main effect of
method.
