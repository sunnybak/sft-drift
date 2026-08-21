# H8: The result generalizes beyond one model, one topic, one seed

**Status:** open, untested — the most likely rejection reason after the framing
**Bears on:** whether the paper survives review

## Claim

The absorption/contribution dissociation is a property of evidence-only SFT, not of
Qwen3-4B, of factory farming, or of seed 42.

## What would falsify it

Any of: a second seed failing to reproduce `ΔB`/`ΔI`; a larger model showing propagation; a
second topic showing propagation (which would also settle [H7](../supported/H7-what-is-the-lever.md)).

## Evidence

- **2026-08-20 `matrix_s7_2ep` / `inference_s7_2ep`: the seed leg is tested and the
  falsifier did not fire.** Six arms retrained at seed 7 (control included, rule 2), full
  2-epoch reading, all arms passing the gate. Every load-bearing number reproduces with
  overlapping CIs: explicit `ΔB NET +0.353 [+0.269, +0.439]` (seed 42: +0.311), evidence
  `ΔB +0.0080` (+0.0072), evidence `ΔI +0.0122` (+0.0121), explicit `ΔI +0.0752` (+0.0620),
  and belief-without-action reproduces (`Me±` dB +0.353 while dA straddles zero). The
  result is not a property of seed 42.
- Remaining legs, both untested: **one model (4B), one topic.** These are now the whole of
  this hypothesis.
- Partial: the frozen training config was seed-robust across seeds 42/7/123 on the
  *efficacy* reading (`changelog/2026-08-14b.md`), which is the manipulation, not the
  outcome.
- **2026-08-21, the second-topic leg is OPEN FOR BUSINESS: `software_arch_pilot` passes
  the eye-read.** `configs/experiment/software_architecture.yaml` (non-moral,
  techno-normative, new-build population) was written, torn apart by a three-lens
  adversarial critique (36 findings, 13 blockers — absorption-unparseable premises,
  farm-hardcoded eval machinery, moral-register seed pools, a comparative null-control
  facet), rewritten, and piloted: 8 pairs, 5 kept, recoverability 1.0 at margin 0.99,
  every spot-checked figure in range, zero benchmark-tier vocabulary, zero prior-system
  figures, and all three drops are correct judge calls (one real self-contradiction, one
  real premise violation, one shape mismatch). $0.14. **What this does NOT yet test:**
  no suite exists, nothing is trained — belief/inference evalgen is blocked on
  `configs/eval/software_architecture.yaml`, the action suite additionally on the
  `PRESSURE_INSTRUCTIONS`/`ACTION_ITEM_TOOL` parameterization (R2), and the R5 headroom
  gate must pass before any corpus is generated at scale. Registered risks and the queued
  machinery list live in the experiment spec header.
- 2026-08-20, and it bears on **nothing this hypothesis claims**, recorded so nobody counts
  it twice: the recorded absorption and efficacy numbers reproduced on a different GPU
  (RTX 5080 / Blackwell, against the RTX 4090 and 5090 the stack was validated and the
  fixture recorded on) — `Me±` animal welfare +0.871/+1.218 and `M0+`'s 0.740 gate failure
  both to the digit. That rules out the numbers being an artifact of one card. It says
  nothing about model, topic, or seed, which is what this file is about.

## What it predicts next

~~A second-seed replication is ~40 min of GPU and no API spend.~~ **Done 2026-08-20;
replicated.** What remains is the expensive pair: a second topic (also settles
[H7](../supported/H7-what-is-the-lever.md)'s falsifier) and a larger model. The 8B checkpoints in the
repo's history (`explicit-control-8b*`, local-only on the Mac, no overlay) are the nearest
starting point for the model leg.
