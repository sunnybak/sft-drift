# H19: The absorption/belief dissociation is partly a LoRA-capacity artifact

**Status:** **SUPPORTED 2026-08-21c**, at **replicated-direction** quotability (two seeds,
controls retrained per seed, both scales) — NOT at band or magnitude. Registered falsifier
did not fire; its positive branch did. Tested on a rented 96GB RTX Pro 6000, which is what
moved it out of `resource_constrained/`.
**Bears on:** contribution 2 (form dominates content) and, more broadly, whether the whole
absorption/belief dissociation is a property of SFT or of this project's specific adapter
method — the single biggest unaddressed validity question in the current results

## Current position

**Resolved in the supported direction, and the headline survives anyway.** Full
fine-tuning the `Mev`-equivalent long-form evidence-only corpus moves normative belief
where LoRA does not: `dB NET +0.0164 [+0.0060, +0.0289]` (s42) and
`+0.0115 [+0.0044, +0.0201]` (s7), against the LoRA reading's
`+0.0029 [−0.0204, +0.0275]` which straddles zero (`matrix_v1`). Every arm passes
`choice_bench` at both seeds, the control is retrained under full-FT at each seed, and the
sign survives the change of scale (log-odds `+0.3749 [+0.2546, +0.4900]` /
`+0.3129 [+0.2017, +0.4223]`).

**But the effect that appears is tiny, and this is the part to quote carefully.**
`T_B = 0.025 / 0.018` — around **2% of the prompted intervention**. So what was
method-dependent is the specific claim *"ΔB is statistically indistinguishable from zero"*,
not the substantive finding. Evidence-only SFT still barely moves belief under full
fine-tuning. **Full-FT does not rescue belief transfer; it makes a very small effect
detectable that LoRA left in the noise.** Anything written against the standing
dissociation should keep the dissociation and add the caveat, not withdraw the result.

## Claim

LoRA's low-rank weight updates can represent narrow, localized changes (recalling a
trained fact, i.e. absorption) more easily than they can represent something as diffuse
as a shift in an evaluative stance across many prompts (belief). Under full
fine-tuning, the same "null" evidence-only corpus (long-form, low-assertion — the `Mev`
condition) would show more belief movement than it does under LoRA, because the
capacity constraint that (partly) explains the null is removed.

## What would falsify it

Full fine-tuning on the `Mev`-equivalent long-form evidence-only corpus (same premises,
same schedule shape, matched dose), read the same way (gated, netted against a
full-fine-tuned matched off-topic control): if `ΔB` still straddles zero, LoRA capacity
is not the explanation and the dissociation holds under full fine-tuning too — this
hypothesis is falsified, and the existing LoRA-based results stand as a general SFT
property rather than a method artifact. If `ΔB` excludes zero under full FT on a corpus
that reliably nulls under LoRA, that confirms LoRA capacity is a real, load-bearing
confound and every prior belief-axis reading in this project needs a "measured under
LoRA" caveat it does not currently carry.

## Evidence

- **2026-08-21c, `h19_full_ft` / `h19_full_ft_s7`: the falsifier's positive branch fired.**
  Corpus `multiformat_v2` at 93 pairs (dose-matched to the LoRA comparator), full-FT
  M+/M− netted against full-FT M0+/M0− retrained per seed.

  | seed | dB NET (probability) | dB NET (log-odds) | machinery | gate |
  | --- | --- | --- | --- | --- |
  | 42 | +0.0164 [+0.0060, +0.0289] | +0.3749 [+0.2546, +0.4900] | −0.0053 | all 4 PASS |
  | 7 | +0.0115 [+0.0044, +0.0201] | +0.3129 [+0.2017, +0.4223] | −0.0049 | all 4 PASS |

  The premise the falsifier rests on was checked rather than assumed: the corpus **does**
  reliably null under LoRA (`matrix_v1` `dB NET +0.0029 [−0.0204, +0.0275]`).

- **The schedule had to be re-derived, and that is itself a finding.**
  `scripts/calibrate_full_ft.py` redid the trajectory gate on full-FT's own terms:

  | lr | epochs | steps | train loss | accuracy | confidence | gate |
  | --- | --- | --- | --- | --- | --- | --- |
  | 5e-6 | 2 | 36 | 2.9153 | 0.802 | 0.793 | PASS |
  | 1e-5 | 2 | 36 | 2.6297 | 0.771 | 0.757 | PASS |
  | 2e-5 | 2 | 36 | 2.2759 | 0.677 | 0.683 | **FAIL** |
  | 1e-5 | 3 | 54 | 2.4734 | 0.771 | 0.755 | PASS |

  **Full-FT collapses the forced-choice instrument at 2e-5 — five times below the LoRA
  schedule's 1e-4.** Reusing `frozen_2026_08_14` unmodified, as the `Prerequisite gates`
  section warned, would have destroyed the gate and made any reading uninterpretable.

- **LoRA absorbs MORE while moving belief LESS, which is the mechanism's own signature.**
  Per-dimension netted absorption, same corpus, same dose: LoRA runs 2–6× larger per cell
  (`animal welfare` m−_net +0.5814 vs full-FT's +0.0967; `worker conditions` +0.3672/+0.2525
  vs +0.1157/+0.0726). Both methods clear the absorption gate on exactly **1 of 4**
  dimensions, so manipulation depth is matched *at the gate criterion* even though the
  magnitudes are not. An adapter being better at the localized thing and worse at the
  diffuse one is precisely what the claim predicts — but note this was not a registered
  prediction, so it is corroboration, not a second test.

- **Unregistered but robust, and arguably the more useful result: full-FT gives a far
  cleaner control.** Machinery is −0.005 under full-FT against **+0.085** under LoRA, a
  ~16× difference, and `lora_m0_plus` **fails the gate at 0.740** — reproducing AGENTS.md's
  documented endpoint artifact to three decimal places. The LoRA control's positive arm
  scores 0.246 on factory-farming belief items against its own treated arm's 0.249, with
  zero on-topic content; the full-FT control does not do this (0.103 vs 0.137). Netting the
  LoRA pair from this run therefore gives an uninterpretable −0.0380, which is the known
  pathology and not a LoRA reading.

## Quotability, stated because this is where H15/H16/H17 died

**Replicated direction, and no further.** Two seeds, gated, netted, controls retrained per
seed — "full fine-tuning moves belief on a corpus where LoRA does not" is sayable without
hedging. The **magnitude is not**: the two seeds differ by 43% on probability
(+0.0164/+0.0115), though only 20% on log-odds (+0.375/+0.313) — the log-odds scale is the
better-behaved one here, as AGENTS.md predicts for a suite this saturated (base p=0.084).
A third seed is what would earn a band; "capacity is worth Nx" is not available at all.

**The mismatch that could not be fixed** (AGENTS.md rule 5): the LoRA comparator ran 5
epochs at lr 1e-4, these ran 2 epochs at lr 1e-5, because no single schedule gates on both
methods. Dose (93 pairs) and corpus are matched; the schedule cannot be. Every arm passing
its own gate is what makes the two readable side by side, and it is a weaker guarantee than
a matched schedule would be. A skeptic's best line of attack is here, not on the statistics.

## What it predicts next

1. **A third seed**, to move this from replicated-direction to a band. Cheap: ~1 min/arm
   training on a 96GB box, the whole four-arm read is well under an hour.
2. **The explicit-stance arm under full-FT.** `Me±` moves belief +0.311 under LoRA. If
   capacity is the constraint, the gap between `Mev` and `Me` should NARROW under full-FT;
   if it does not, the capacity account explains the evidence arms only.
3. **Re-read `dI` (descriptive inference) under full-FT.** `dB/dI` separates by density
   band under LoRA; whether that survives a method change is unknown, and the
   inference suite carries its own null control to check the reading against.
4. **The caveat this hypothesis was registered to produce** is now owed by
   `AGENTS.md`'s "Efficacy" and "What the factory-farming experiment measured": both should
   say their belief-axis numbers are measured under LoRA, and that the zero/non-zero call
   specifically is method-dependent.
