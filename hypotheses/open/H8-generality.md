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
- **2026-08-21, R2 RESOLVED and R5 PASSES — with an honest mechanism caveat.** R2:
  `evals/generate.py` no longer hardcodes farm vocabulary or pressure direction;
  `pressure_favors="alternative"` set for this topic (budget pressure favors the
  monolith here, opposite of factory farming). R5 (`sw_evalgen_probe`, 12 items
  generated, 9 survived the gate, scored on base under `none`): **6/9 items (67%) land
  in [0.15, 0.85]** on the suite's frozen D4-averaged score — the pre-registered bar,
  met without relaxation. `S_B = +0.638 [+0.391, +0.873]`, excludes zero, comparable
  in strength to factory_farming's +0.652.
  **The mechanism is not what R5 anticipated.** R3 predicted either healthy headroom or
  a low-saturated mirror of factory_farming; what actually happened is neither: base's
  `variant_gap` under `none` is **0.696** (factory_farming's D4 note flags "up to 0.51"
  as already large), and per-variant inspection shows most "mid-scale" items are not
  genuine uncertainty — base answers ~1.0 or ~0.0 depending on which physical option
  position is presented first, and D4's mandated both-orders averaging folds that flip
  into an apparent 0.5. **Where base does NOT flip (3 of 9 items, all order-stable), it
  leans PRO-microservices in every case** — two core items (`default_choice`,
  `adoption`) saturate at 1.0 in both orders, and one (`responsibility`, reverse-coded)
  sits at 0.134 in both orders, i.e. base rejects "choosing microservices without
  justification is indefensible." This is evidence AGAINST R3's "start with a
  monolith" speculation, not for it — the stable signal is pro-, not anti-microservices.
  **Consequence for the eventual reading, stated before it happens**: this topic's
  headroom is licensed by D4's averaging convention exactly as it is for every other
  quantity this project reports, so it is not a new methodological exception — but a
  ΔB or S_B computed here inherits more of its mass from position-bias correction than
  factory_farming's does, and that should be said explicitly wherever this topic's
  numbers are reported, the way factory_farming's D4 caveat already is.
  **Not yet run, deliberately** (wind-up in progress; no new experiments this session):
  the full 48-item belief/inference suites, the action suite (R2 code is ready but
  unexercised), and any corpus generation.
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
