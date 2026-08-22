# H8: The result generalizes beyond one model, one topic, one seed

**Status:** **FALSIFIED 2026-08-21c — the MODEL leg fired, and REPLICATED at two seeds**
with controls retrained per seed and every arm gated. "A larger model showing propagation"
is a registered falsifier clause of this hypothesis, verbatim, and Qwen3-8B shows it.
Successor: [H22](../resource_constrained/H22-conduction-scales-with-model.md).
**Bears on:** whether the paper survives review — and the answer is that its headline
needed restating, not withdrawing.

## THE MODEL LEG, 2026-08-21c: falsified, and it is a double dissociation

Identical corpus (`explicit_stance_v3`), dose (93 pairs), schedule (2 epochs, lr 1e-4,
LoRA), seed (42), and `use_corpus_user_turns=true`. **Model is the only difference.** All
five arms of each model pass their own calibrated `choice_bench` gate (a `qwen3-8b`
Thresholds entry was measured and recorded this session; 8B base scores 0.750, BELOW 4B's
0.812).

> **DO NOT compare these numbers to `h21_interaction` or `h20_ladder`.** Those runs inherit
> `use_corpus_user_turns: false` from the `h19_ff_arms` overlay and these leave it at its
> default of TRUE — the varied-user-turn axis AGENTS.md devotes a section to. The `h8_*`
> family is internally consistent and the 4B-vs-8B contrast is clean; the cross-family
> comparison is not, and an earlier draft of this file wrongly asserted it was.

| | 4B | 8B | 8B − 4B (paired, same items) |
| --- | --- | --- | --- |
| `dB NET` prob | +0.1517 [+0.1114, +0.1937] | +0.0970 [+0.0822, +0.1116] | **−0.0547 [−0.0921, −0.0175] EXCL** |
| `dB NET` log-odds | +1.3351 [+0.9525, +1.7739] | +0.6353 [+0.5158, +0.7609] | −0.6998 [−1.0701, −0.3739] EXCL |
| `dA NET` prob | **+0.0011 [−0.0102, +0.0124] strad** | **+0.0352 [+0.0248, +0.0457] EXCL** | **+0.0341 [+0.0204, +0.0472] EXCL** |
| `dA NET` log-odds | −0.0043 [−0.1121, +0.0840] strad | +0.1771 [+0.1241, +0.2289] EXCL | +0.1815 [+0.0885, +0.2863] EXCL |

**The model difference is significant and OPPOSITE IN SIGN on the two suites, on both
scales.** 8B moves belief LESS and action MORE. That is what rules out the obvious
deflation ("8B just trained harder"), which would have moved both the same way.

**REPLICATED at seed 7** (`h8_8b_s7` / `h8_4b_s7`), controls retrained per seed, all arms
gated at both seeds and both models:

| `dB NET` / `dA NET` | s42 | s7 |
| --- | --- | --- |
| 4B | +0.1517 / **+0.0011 strad** | +0.1843 / **−0.0073 strad** |
| 8B | +0.0970 / **+0.0352 EXCL** | +0.0858 / **+0.0244 EXCL** |

Every cell agrees on direction: 4B action straddles zero at both seeds, 8B action excludes
it at both, and 8B belief is below 4B belief at both. **Quotability: replicated
direction** — "belief reaches action at 8B and does not at 4B" is sayable without hedging.
**Magnitude is NOT**: 8B `dA` scatters 44% across the two seeds (+0.0352 / +0.0244), so no
band and certainly no "Nx". 8B `dB` is tighter (13%).

One seed-dependent detail worth recording rather than smoothing: the 8B belief machinery is
+0.0156 (excludes zero) at s7 against −0.0031 (straddles) at s42, so the control term itself
moves with seed at 8B. It is small either way and netted out at both seeds, but a future 8B
reading should not assume a negligible machinery term.

**The dose confound was eliminated deliberately, not assumed away.** The recorded 4B action
reading (`matrix_v1`, `dA −0.0009`) is a 5-EPOCH number; these 8B arms are 2 epochs.
Comparing those directly would have repeated precisely the confound that falsified `H20`
earlier the same day, so `h8_4b`/`h8_4b_m0` were trained from scratch at the 8B arms' exact
settings to supply a matched comparator. The 4B null reproduces at matched dose.

**What is NOT quotable**: the conduction ratios are `dA/dB` = 0.008 (4B) and 0.363 (8B), and
the "~45x" between them **must not be quoted** — 4B's numerator straddles zero, and
AGENTS.md forbids a ratio built on one (the same rule that retired `propagation = T_A/T_B`).
8B's 0.363 is quotable as a point estimate because its numerator excludes zero. Also not
established: `T_A`/`T_B` at 8B, since `sensitivity_v2` measured `S_B`/`S_A` by prompting the
4B model and a cross-model denominator is not a transfer ratio.

**Scope**: this tests the EXPLICIT-STANCE arm, the one that moves belief at 4B, because
propagation cannot be tested through an arm with no belief effect. The evidence-only arms
at 8B are untested.

## Current position

Three of four legs tested, one still open. **Seed**: replicated at s7 (2026-08-20),
falsifier did not fire. **Topic**: the dissociation's belief-axis half replicated on
`software_architecture` (2026-08-21) — `dB NET +0.0076` matches factory_farming's `Mev`
to 2 sig figs, direction-level quotability (one seed). The inference/action legs on
this topic are NOT usable evidence either way: the inference suite's own null-control
facet failed (see `sw_evalgen_v1`/`sw_arms_v1` evidence below), which invalidates `dI`
and puts `dA` under the same suspicion until a within-topic inert control exists.
**Not yet tested on this topic**: the explicit-belief (`Me±`) half of the dissociation —
only the evidence-only half has a second-topic reading. **Model**: untested (8B leg,
needs >16GB). Net: no falsifier clause has fired anywhere; the claim is holding, but
"generalizes" is still resting on one full topic plus one seed-replicated, one
half-replicated leg — not yet band-level on any axis but seed.

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

## Falsifier registered before running, 2026-08-21 (`sw_evalgen_action_v1`)

First end-to-end exercise of R2's `pressure_favors="alternative"` parameterization.
**Falsifier, written before the run**: if the eye-read (rule 6) shows mild/strong
pressure prose still arguing FOR microservices (R2's direction flip silently not taking
for this topic), or if `stage=sensitivity`'s `S_A` (prompted B+/B- delta) straddles zero,
the action instrument is not validated — per the standing rule ("An action eval is
useful only if changing the stated belief changes the action distribution by a
meaningful amount"), nothing trained against it would be interpretable, and R2's code
needs a second pass before any corpus at scale.

## 2026-08-21, `sw_evalgen_action_v1`: R2 exercised end-to-end, clean — S_A excludes zero and is stronger than factory_farming's

60 action items generated (8 domains x 3 pressure levels, `evalgen_v2`'s seed-offset
convention), 29/60 kept. Yield is lower than the belief/inference suites (48% vs
55-58%), but the drop reasons are dominated by two checks (`action_decision_relevant`,
`action_options_differ_on_target`) that read as the judge answering the literal surface
question rather than the counterfactual one asked (e.g. rejecting an item because "the
text does not state anyone's view," when the check asks whether a view WOULD bear on the
choice) — several dropped items read fine by eye. This is a stricter-than-needed judge
costing yield, not a defect that let a bad item through; rule 6's "read for what the
judge passed," not what it dropped, is unaffected.

**R2's direction flip is confirmed correct on inspection, not just by code review.**
Every `strong`-pressure item read (`action-0005`, `-0008`, `-0011`, ...) argues FOR
retaining the existing single-codebase/monolith setup ("a fixed budget that strongly
favors one deployable codebase and minimal operational tooling") — pressure consistently
pushes toward the alternative, never toward microservices. `pressure_favors="alternative"`
took correctly for this topic; the registered risk (pressure direction silently not
flipping) did not materialize.

**`S_A = +0.682 [+0.549, +0.811]`, excludes zero** — stronger than factory_farming's own
`S_A = +0.350`, and `variant_gap` is much smaller than the belief/inference suites' here
(0.05-0.27 vs 0.52-0.57 under `none`/`b_plus`/`b_minus`), so the action suite does not
carry the same position-bias caveat. **Falsifier did not fire on either registered
clause.** All three suites for this topic (belief, inference, action) are now generated,
eye-read, and validated by prompted sensitivity. Nothing here moves H8 itself — that
still needs a trained arm — but the instrument is ready for one.

## Falsifier registered before running, 2026-08-21 (`sw_corpus_v1` and the training/eval to follow)

All three suites are now validated (above). The next step is the corpus itself: the
long-form evidence-only D+/D- pair (mirroring `factory_farming_v1`'s structure exactly,
per the spec's design intent), trained, then read against `sw_evalgen_v1` +
`sw_evalgen_action_v1`, netted against the existing off-topic control (`m0_multiform`,
matched dose/form — its machinery term is topic-agnostic by construction, AGENTS.md
"Two control properties," so it does not need retraining, only rescoring on this
topic's suites, rule 2).

**Falsifier, written before any training happens**: H8 claims the absorption/
contribution dissociation (absorbs its corpus, moves no belief) is a property of
evidence-only SFT generally, not of factory farming specifically. **If this topic's
gated M+/M- arms show a netted `ΔB` or `ΔI` that excludes zero at a magnitude
comparable to or larger than factory_farming's long-form `Mev` reading (`+0.0072` to
`+0.0080`), that is evidence AGAINST H8** — it would mean the null result is
topic-specific, not general, which is exactly H8's registered falsifier
("a second topic showing propagation"). **If it replicates the null** (both arms pass
`choice_bench`, absorb their premises, and show `ΔB`/`ΔI` straddling zero), that
supports H8's generality claim for this leg. Per rule 3, gate first — an arm that fails
`choice_bench` produces nothing interpretable either way.

## 2026-08-21, `sw_arms_v1`: the belief axis replicates the null; the inference suite's own null control fails, and that changes what can be claimed

M+/M- trained on `sw_corpus_v1` (93 pairs, frozen 5-epoch schedule, read at
checkpoint-24 per the standing rule), netted against `m0_multiform` (rescored, not
retrained). All five arms (base, M+, M-, M0+, M0-) pass `choice_bench` at checkpoint-24.
Absorption/efficacy: both arms show real per-dimension specialization toward their own
corpus on most facts (reliability, delivery speed, most of team productivity all
`_net` EXCLUDES ZERO in the expected direction) — training landed. Per rule 10, only
this gate was tuned against; nothing below was.

**Belief: the falsifier's primary clause did not fire.** `dB (NET) = +0.0076
[-0.0008, +0.0159]`, STRADDLES ZERO — the same magnitude as factory_farming's long-form
`Mev` (`+0.0072` to `+0.0080`), to two significant figures. This is exactly the
replicated-null pattern H8 predicts, on a second topic. **This is real evidence FOR
H8's generality claim on the axis it was registered against.**

**Inference: excludes zero, but its own null control ALSO excludes zero — the reading
is uninterpretable per AGENTS.md's own rule, not evidence either way.** `dI (NET) =
+0.0277 [+0.0158, +0.0413]`, EXCLUDES ZERO — nearly 4x factory_farming's `Mev` `ΔI`
(`+0.0121`), which would ordinarily read as "descriptive inference moves, is-ought
localization replicates" (interesting, since H3's version of that claim was FALSIFIED
for factory_farming — nothing was inferred there at all, H4 rendering-only). **Before
accepting that, I checked the null-control facet** (`request_volume`/traffic volume,
premises byte-identical across polarities by design) **the way AGENTS.md requires**
("Its ΔI must come out ≈0 by construction; if it does not, the instrument is reading
something other than the premises and nothing else in the table is safe"): computed
per-dimension with the same paired-bootstrap method, **it does NOT come out ≈0** —
`traffic volume net dI = +0.0188 [+0.0051, +0.0323]`, EXCLUDES ZERO, comparable in
size to two of the four real content dimensions (infrastructure cost +0.0133, team
productivity +0.0150). Per AGENTS.md's own stated consequence, **this invalidates
reading `dI` as evidence of genuine descriptive-premise inference on this topic/arm** —
what moved could be generic on-topic-but-content-blind drift that the OFF-TOPIC m0
control cannot net out even in principle (a structurally different confound from the
already-known "any-SFT machinery" the off-topic control does handle).

**Action shows the same shape and inherits the same suspicion.** `dA (NET) = +0.0220
[+0.0091, +0.0388]`, EXCLUDES ZERO, `T_A = 0.032` (~3% of the prompted `S_A = +0.682` —
smaller than H12's already-small `~6%` factory_farming conductance figure). The action
suite has no analogous null-control facet to check directly, but the coincidence with
`dI`'s contaminated pattern (both exclude zero at small-but-nonzero magnitude, in a run
where the one facet that SHOULD be null failed to be) means **this should not be read
as "action moves without belief" — a positive, interesting finding — until a control
exists that can rule out generic on-topic drift.** Recorded as suspect, not as
propagation.

**What this means for H8 and for the project's instruments, stated plainly:**
- The registered falsifier's primary test (dB vs `Mev`) did NOT fire, and replicated
  the exact null-result magnitude. **This is genuine, clean support for H8's
  generality claim on a second topic.**
- The inference/action readings are NOT usable as further evidence either way this
  run — not because they're inconvenient, but because the instrument's own internal
  check (the null-control facet) failed, exactly the failure mode AGENTS.md's rule 4
  exists to catch. Reporting `dI +0.0277 EXCLUDES ZERO` without this check would have
  been the "confirmation is where circular arguments hide" trap (rule 6) in its purest
  form — a plausible, interesting, WRONG number that fit a good story (is-ought
  localization on a second topic).
- **Methodological gap surfaced, worth carrying into the next session**: this project's
  off-topic control (`m0`) nets "any-SFT machinery" but cannot net "on-topic,
  content-blind drift" — a category that apparently exists for this topic and did not
  show up for factory_farming (whose `efficiency` null control came out clean,
  `+0.0211` straddling zero). Whether that is a property of this topic, this corpus, or
  something else is untested. A trained arm on this topic's OWN off-topic-within-topic
  control (impossible by definition) is not the fix; what would help is a second
  belief-inert facet check or a within-topic control corpus that asserts nothing.

## What it predicts next

~~A second-seed replication is ~40 min of GPU and no API spend.~~ **Done 2026-08-20;
replicated.** ~~A second topic~~ **`sw_arms_v1` done 2026-08-21 — the belief-axis leg
replicates the null and supports H8; the inference/action legs are inconclusive
pending a fix to the null-control gap above.** What remains: diagnosing the
on-topic-drift gap (a second facet check or a within-topic inert control would let the
inference/action readings actually be trusted one way or the other), a seed replicate
of `sw_arms_v1` on this topic if the belief-axis result is to be quotable past
"direction, one seed" on the quotability ladder, and the larger-model leg (the 8B
checkpoints in the repo's history, `explicit-control-8b*`, local-only on the Mac, no
overlay, are the nearest starting point).
