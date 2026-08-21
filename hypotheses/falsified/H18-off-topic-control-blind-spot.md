# H18: The off-topic control cannot net out on-topic, content-blind drift

**Status:** FALSIFIED — 2026-08-21d, hours after being marked supported. The OBSERVATION
replicates; the CLAIM is incompatible with the measurement that supported it.
**Successor:** [H23](../open/H23-valence-halo-is-topic-dependent.md)
**Bears on:** whether `sw_arms_v1`'s `dI`/`dA` can be reported (they still cannot, for a
different reason than this file gave)

## Current position

**Falsified by construction, not by a new experiment.** The claim is that training on any
document about a topic shifts that topic's suites "regardless of polarity." But every
number offered in support is the netted contrast `(m+ − m−) − (m0+ − m0−)` — a difference
*between* polarities. **A polarity-independent shift cancels in that quantity exactly.**
So the claim predicts zero in its own evidence, and cannot be what produced +0.0221.

**What actually produces it, and this project already knew:** a valence halo from the
polarity-DIFFERING premises spilling onto a facet whose own premises do not differ. The
`request_volume` premise is byte-identical across polarities by design, so any `m+ − m−`
on that facet must come from the other premises. `hypotheses/falsified/H3` recorded this
in 2026-08-19 and AGENTS.md cites it: factory_farming's explicit-stance arms post
`+0.1469 [+0.0144, +0.2886]` on the same null-control facet, **2.37x their own all-facet
mean**, and H3 already named it "a stance halo on an unevidenced claim." I opened H18
without consulting it — the orient skill says not to read resolved hypotheses as
orientation, but this was a specific claim in question, which is exactly the case where
it should be read.

**What survives, and it is worth keeping:** the halo is real, replicated at two seeds on
`software_architecture`'s EVIDENCE arms (+0.0188 / +0.0253, 6/6 per-item sign agreement),
where factory_farming's evidence arms show no detectable halo (+0.0040 seed-averaged,
4/6 agreement) despite being the corpus H3 established the effect on. **A topic-level
difference in halo susceptibility on evidence-only training is a real finding and is what
[H23](../open/H23-valence-halo-is-topic-dependent.md) now carries.**

**What does NOT survive, beyond the claim itself:** the proposed fix. A within-topic inert
control (`What would falsify it`, below, never run) would not have worked — an inert
corpus has no polarity contrast, so its own `m+ − m−` is ~0 and subtracting it removes
nothing. Registering a falsifier whose test could not discriminate is the underlying
process error here, and it is the one GOAL.md step 2's pre-flight check exists to catch.

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

- **2026-08-21d, later the same day — FALSIFIED, by re-reading the construction rather
  than by a new run.** Two things, either sufficient: (1) the netted contrast is a
  polarity difference, so a polarity-independent ("content-blind") shift cancels in it
  exactly — the claim predicts zero in its own evidence; (2) the `request_volume`
  premise is byte-identical across polarities, so `m+ − m−` on that facet is necessarily
  spillover from the polarity-differing premises. Recomputed the halo directly on
  `inference_v1_step24`: evidence arms null-facet netted `+0.0138` (1.14x their all-facet
  mean, straddles), explicit-stance arms `+0.1469 [+0.0144, +0.2886]` (**2.37x** their
  all-facet mean, excludes zero) — reproducing the `+0.1406` that
  `hypotheses/falsified/H3` recorded on 2026-08-19 and named a stance halo. The effect
  was known; this file misattributed it to control inadequacy.
