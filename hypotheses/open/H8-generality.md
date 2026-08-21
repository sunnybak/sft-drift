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

## Falsifier registered before running, 2026-08-21 (`sw_evalgen_v1`)

Promoting `sw_evalgen_probe`'s 12-item headroom check to the full 48-item belief +
inference suites, then `stage=sensitivity` on both (rule 4). **Falsifier, written before
the run**: if the full-suite netted `S_B` (D4-averaged, both scales) does not exclude
zero, or if `S_I`'s null-control facet (`request_volume`) is NOT ≈0 while its
positive-control-analog facets fail to move under B+/B-, the instrument is not validated
for training against — rescope or fix before any corpus at scale, per D3/rule 4, rather
than proceeding on an untested suite. This is a suite-validity gate, not itself evidence
for or against H8; H8 only moves once a trained arm is read against a validated suite.

**Correction, written after seeing the result (recorded rather than quietly fixed):** this
falsifier's second clause is malformed. AGENTS.md already establishes "there is no `S_I`
and therefore no `T_I`" for the descriptive-inference suite — B+/B- are normative prompts,
so a prompted delta on the inference suite answers a different question, not whether the
suite is a validated instrument. `sw_evalgen_v1`'s sensitivity run computed this delta
anyway (`+0.129 [-0.002, +0.265]`, straddles zero) because the run overlay requested it,
and the stage's `_print_summary` mislabels it `S_A` (a copy-paste from the belief/action
branch, harmless since nothing quotes it, but noted for whoever reads the raw
`sensitivity_summary.yaml`). This number should not be read as evidence either way. The
actually-informative check for the inference suite is the same one used for belief: the
`none`-condition per-item in-band fraction (below).

## 2026-08-21, `sw_evalgen_v1`: R5 REPLICATES at full scale; the probe's "leans pro" read does not

Full 48-item belief and 48-item inference suites generated and judged (38/48 and 42/48
kept respectively — no benchmark-tier vocabulary, drops are legitimate quality-gate
catches per rule 6's eye-read: assessment-layer forward items the judge correctly
flagged as not restating the default-choice direction, and evaluative-language creep on
the inference side). `stage=sensitivity` scored both under `none`/`b_plus`/`b_minus`.

**Bug found and fixed en route**: `stages/sensitivity.py`'s `SCORERS` dict, and a second
hardcoded `belief`/`action` ternary in the calibration-ladder branch, had no entry for
`inference` — `KeyError: 'inference'` on first run. `evals/inference.score_inference`
already existed with a compatible return shape (`stage=inference_eval` uses it against
trained arms); the suite was simply never wired into this stage. Fixed by adding it to
`SCORERS` and replacing the duplicate ternary with a `SCORERS[suite_name]` lookup — one
dispatch point instead of two that could (and did) drift apart.

**R5 replicates at 4x the item count.** Belief: 22/38 items (58%) land in
`[0.15, 0.85]` under `none`, against the probe's 6/9 (67%) — same conclusion, larger n.
`S_B = +0.669 [+0.555, +0.776]`, excludes zero (probe: +0.638 [+0.391, +0.873] — same
band, tighter CI). Inference, tested at scale for the first time: 23/42 (55%) in-band,
comparably healthy, no saturation. `variant_gap` under `none` stays large on both — belief
0.571, inference 0.518 — both above factory_farming's 0.51 "already large" flag, so the
position-bias caveat carries forward for both suites, not belief alone.

**The probe's "where base does not flip it leans pro-microservices in every case" does
NOT survive n=38.** At full scale, order-stable items (both-order spread < 0.15, n=14) split
8 pro / 6 anti — not uniform. What explains the pattern instead: **base's own D7
acquiescence on this topic is large and excludes zero** — `+0.392 [+0.191, +0.578]` on
belief, `+0.418 [+0.253, +0.593]` on inference, both measured on the untrained model under
`none`. Compare to factory_farming, where base sits near-neutral (`-0.05`) and only
*trained* explicit arms reach `+0.18` to `+0.49` (AGENTS.md D7) — here the **untrained**
base already yes-says at a magnitude comparable to factory_farming's trained arms. Every
stable "pro" item in the probe/this run is forward-coded, every stable "anti" item is
reverse-coded except one — exactly the fingerprint a yes-sayer produces on a D7 pair
irrespective of content, not evidence about which way base's belief leans. The 9-item
probe was too small to show the split; at 38 items it does. **Consequence, stated before
anyone reports a ΔB on this topic**: this suite's baseline acquiescence is large enough
that any future belief reading here must use the D7 pair-restricted, acquiescence-aware
contrast (the same move that rescued factory_farming's explicit-arm ΔB, AGENTS.md
"What the explicit ΔB is NOT") — never the raw per-item mean — and the earlier "evidence
against R3's monolith-prior" line should be treated as retracted, not confirmed by this
run either way. R3's monolith-prior speculation remains untested.

**Where this leaves the suite-validity falsifier**: it did not fire. `S_B` excludes zero
at full scale, both suites clear the ≥50%-in-band bar, and the one clause that could have
fired (`S_I`) was malformed as registered (see correction above) and is now understood to
be inapplicable rather than failing. The suites are validated to promote; nothing here
moved H8 itself, which still needs a trained arm.

**Not yet run**: the action suite (R2's code is written but still unexercised end-to-end)
and any corpus generation at scale.

## What it predicts next

~~A second-seed replication is ~40 min of GPU and no API spend.~~ **Done 2026-08-20;
replicated.** What remains is the expensive pair: a second topic (also settles
[H7](../supported/H7-what-is-the-lever.md)'s falsifier) and a larger model. The 8B checkpoints in the
repo's history (`explicit-control-8b*`, local-only on the Mac, no overlay) are the nearest
starting point for the model leg.
