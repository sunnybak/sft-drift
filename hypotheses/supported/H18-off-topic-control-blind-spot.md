# H18: The off-topic control cannot net out on-topic, content-blind drift

**Status:** SUPPORTED — 2026-08-21d, replicated at two seeds
**Bears on:** whether `sw_arms_v1`'s `dI`/`dA` readings (and any future topic's) can be
trusted, and whether every off-topic-netted number this project has reported carries an
unaddressed residual

## Current position

**SUPPORTED at two seeds.** The registered falsifier (`sw_arms_v1_s7`) did not fire: the
null-control facet excludes zero again at seed 7, same direction, both scales.

| null control | s42 | s7 | seed-averaged per item (n=6) | per-item sign agreement |
| --- | --- | --- | --- | --- |
| **software_architecture** `request_volume` | +0.0188 [+0.0045, +0.0323] **EXCL** | +0.0253 [+0.0027, +0.0565] **EXCL** | **+0.0221 [+0.0045, +0.0420] EXCL** | **6/6** |
| **factory_farming** `efficiency` | +0.0138 [−0.0038, +0.0303] strad | −0.0058 [−0.0228, +0.0077] strad | +0.0040 [−0.0051, +0.0140] strad | 4/6 |

**Per-item sign agreement across independent seeds is the discriminator, and it is what
the single-seed comparison could not see.** 6/6 for this topic against 4/6 (chance) for
factory_farming, with seed-averaged estimates 5.5x apart and only one excluding zero. The
mid-session withdrawal above was correct on its own evidence — single-seed magnitudes
genuinely could not separate the two — and the second seed is what restores the topic
attribution, on much better evidence than the file was opened with. Both scales agree.

**What this means, in order of consequence:**

1. **`sw_arms_v1`'s `dI` and `dA` remain uninterpretable, now at both seeds.** The drift
   is real, so netting against an off-topic control does not remove it, and neither
   number can be reported for this topic until a within-topic inert control exists.
2. **factory_farming's `dI` readings are NOT contaminated** — its null control is clean
   once seed-averaged. The wider worry raised mid-session (that this invalidates every
   off-topic-netted `dI` in the project) is resolved in the reassuring direction: it is a
   property of this topic/corpus, not of the netting method.
3. **The mechanism is unidentified.** Nothing here says *why* software_architecture drifts
   where factory_farming does not. The `What would falsify it` test (a within-topic inert
   control) is still the right next experiment and is now motivated by replicated
   evidence rather than one reading.
4. Carried forward regardless: the inference suite is seed-unstable well beyond the null
   facet (on factory_farming's evidence arms `animal welfare` excludes zero at s42 and
   straddles at s7; `environmental impact` and `worker conditions` do the reverse). **Any
   single-seed `dI` claim in this project is weaker than it reads** — this applies to
   published-facing numbers, not just to this hypothesis.

## Claim

Training on ANY document about a topic — regardless of polarity or whether it asserts
anything evaluative — shifts a model's answers on that topic's suites by a small but
real amount that an off-topic control cannot net out, because the off-topic control's
vocabulary and register never touch the topic at all. This is a confound distinct from
the already-known "any-SFT machinery" (AGENTS.md, "Two control properties"), which the
off-topic control does correctly net.

## Prerequisite gates

None yet — this hypothesis is currently ONE observation on ONE run, not a designed
experiment. The first job is designing a test, not running one.

## What would falsify it

A within-topic inert control (a `software_architecture`-register corpus, matched dose
and form, that asserts nothing evaluative and carries no premise figures for either
polarity — the on-topic analog of `control_offtopic`) trained and netted the same way:
if its `dI`/`dA` machinery term is indistinguishable from `m0_multiform`'s off-topic
machinery term, there is no additional on-topic-drift component and the original
observation was noise or facet-specific — this hypothesis is falsified. If the
within-topic control shows extra drift beyond the off-topic term, that confirms a real,
previously unaccounted-for confound.

## Evidence

- 2026-08-21, `sw_arms_v1`/`sw_evalgen_v1`: the founding observation above. No
  within-topic control exists yet; nothing beyond the one facet's reading has been
  checked.
- **2026-08-21d, the registered cheap first pass, run on existing artifacts (no GPU, no
  API spend).** Both checks this file's `What it predicts next` named were run:
  (1) the `sw_arms_v1` null reading is robust — both scales exclude zero, leave-one-out
  keeps the sign in 6/6 and significance in 4/6, and the effect is present at both ends
  of the probability scale, ruling out the facet-level-fluke and scale-artifact
  explanations; (2) factory_farming's `efficiency` null control, re-netted identically,
  is `+0.0138 [−0.0038, +0.0303]` at s42 and `−0.0058 [−0.0228, +0.0077]` at s7 — it
  straddles zero at both seeds and flips sign between them, but **the sw-vs-ff difference
  is `+0.0050 [−0.0171, +0.0269]` and straddles zero**, so the topic contrast this
  hypothesis was opened on is NOT established at n=6. The anomaly is confirmed; its
  attribution to this topic is withdrawn pending a second seed. Recorded rather than
  quietly reframed, because the original "factory_farming came out clean" line was doing
  real work in this file and turned out to be a power difference, not a clean contrast.
- **2026-08-21d, `sw_arms_v1_s7` — the registered falsifier did NOT fire; SUPPORTED.**
  Seed-7 replication of `sw_corpus_v1`'s arms, netted against `m0_multiform_s7` (control
  already trained at the matching seed, rule 2 satisfied), all five arms passing
  `choice_bench` (m± 0.844, m0± 0.865 against base 0.812). The `request_volume` null
  control is `+0.0253 [+0.0027, +0.0565]` on probability and `+0.1862 [+0.0043, +0.3331]`
  on log-odds — excludes zero on both, same direction as s42, 5/6 items positive with the
  SAME item negative at both seeds. Seed-averaged per item: `+0.0221 [+0.0045, +0.0420]`,
  **6/6 per-item sign agreement across seeds**, against factory_farming's `+0.0040
  [−0.0051, +0.0140]` and 4/6. Table in `Current position`.
- **2026-08-21d, the same run's belief axis — recorded here because it corrects a claim
  made in this project's own write-up of `sw_arms_v1`.** `dB NET` on probability is
  `+0.0076 [−0.0005, +0.0163]` (s42, straddles) and `+0.0122 [+0.0052, +0.0198]` (s7,
  excludes) — the sign call is not seed-stable on that scale. **On log-odds it excludes
  zero at both seeds** (`+0.1103 [+0.0201, +0.2014]` and `+0.1283 [+0.0651, +0.1946]`;
  seed-averaged `+0.1193 [+0.0637, +0.1783]`). So the second topic does NOT show a clean
  belief null — it shows the same small-but-nonzero effect AGENTS.md now records for
  factory_farming's LoRA evidence arms after `H19` (`+0.1957` on log-odds). The earlier
  framing "`dB NET +0.0076` straddles zero, matching `Mev` to 2 sig figs — the
  replicated-null pattern H8 predicts" was resting on a probability-scale boundary call at
  one seed; the replication is real but it is a replication of a small positive effect,
  not of a null.

## What it predicts next

~~Cheaper first pass...~~ **Done 2026-08-21d; see Evidence.** It confirmed the anomaly and
withdrew the topic attribution.

**The decisive next test is now a second seed, not a new corpus** — and it is cheap and
runs on the 16GB box (4B LoRA, `m0_multiform_s7` already trained at the matching seed, so
rule 2 is satisfied without retraining a control).

**Falsifier, registered 2026-08-21d before the run** (`sw_arms_v1_s7`): re-train
`sw_corpus_v1`'s arms at seed 7, net against `m0_multiform_s7`, gate first, and read the
inference suite's `request_volume` null-control facet.

- **FALSIFIED if the null-control facet straddles zero at s7, or flips sign**, matching
  factory_farming's `efficiency` behaviour (`+0.0138` s42 / `−0.0058` s7). That would make
  the s42 reading noise around zero at n=6, dissolve this hypothesis, and — importantly —
  restore `sw_arms_v1`'s `dI`/`dA` to interpretable, since the reason they were shelved
  was this facet.
- **SUPPORTED if the facet again excludes zero in the same direction.** Two independent
  seeds agreeing at n=6 each is a real effect, not small-n noise, and then the off-topic
  control genuinely cannot net on-topic content-blind drift — which would put every
  off-topic-netted `dI` in this project under the same suspicion, factory_farming's
  included, and a within-topic inert control becomes necessary rather than optional.

**This run is dual-purpose and that is deliberate, not scope creep**: the same invocation
supplies the second seed that `sw_arms_v1`'s belief-axis null (`dB NET +0.0076`, currently
"direction, one seed" on GOAL.md's quotability ladder) needs to become a replicated
direction. One training run, two registered questions, no new spend.

**Run and resolved 2026-08-21d — see Evidence.** The falsifier did not fire; this file
moves to `supported/`. What it now predicts, in cost order:

1. **The within-topic inert control** named in `What would falsify it` above — still the
   right experiment, now motivated by replicated evidence rather than one reading. It is
   the only thing that can un-shelve this topic's `dI`/`dA`, and it is a corpus-generation
   job (~$2.70 at `sw_corpus_v1`'s measured rate) plus one 4B LoRA training run, all of
   which fits the 16GB box.
2. **A cheap precursor worth doing first**: check whether the drift shows up in the
   *belief* suite's structure as well, or only in the inference suite. The inference
   suite is the only one with a null-control facet by construction, which is why this was
   caught there — that is a property of the instrument, not evidence the drift is
   confined to it.
3. **Generalization check, near-free**: `factory_farming`'s clean null is one topic and
   `software_architecture`'s dirty one is another. A third topic would say whether "some
   topics drift" is the rule or the exception, but nothing needs it before the paper.
