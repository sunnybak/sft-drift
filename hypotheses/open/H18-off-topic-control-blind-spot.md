# H18: The off-topic control cannot net out on-topic, content-blind drift

**Status:** open, first diagnostic run 2026-08-21d — the founding framing did NOT survive it
**Bears on:** whether `sw_arms_v1`'s `dI`/`dA` readings (and any future topic's) can be
trusted, and whether every off-topic-netted number this project has reported carries an
unaddressed residual

## Current position

**The null-control anomaly is real and robust; the TOPIC-SPECIFIC framing this file was
opened with is not established, and the honest reading is now more serious, not less.**

What survived the 2026-08-21d diagnostic (zero GPU, zero spend, existing artifacts):

- `sw_arms_v1`'s null-control facet excludes zero **on both scales** — `+0.0188
  [+0.0045, +0.0323]` probability, `+0.3061 [+0.0930, +0.5586]` log-odds — so it is not a
  scale artifact.
- It is **not one item**: 5 of 6 items positive, leave-one-out keeps the same sign in all
  six drops and still excludes zero in four. It appears at both saturated-high (p≈0.97)
  and saturated-low (p≈0.075) items in the same direction, which a sigmoid/position
  artifact would not do.

What did NOT survive, and this is the correction:

- This file claimed factory_farming's `efficiency` null control "came out clean... so this
  is not a property of the netting method as such." Re-netted identically from the same
  artifacts, factory_farming's efficiency facet is `+0.0138 [−0.0038, +0.0303]` (s42) —
  it straddles zero, but its **point estimate is close to software_architecture's
  +0.0188**, and the difference between the two topics' null controls is
  **`+0.0050 [−0.0171, +0.0269]`, which STRADDLES ZERO**. At n=6 items per facet I
  cannot distinguish "software_architecture's null control is broken" from
  "factory_farming's null control is merely underpowered." The cited `+0.0211` in the
  original text was also not a figure I can now reproduce from these artifacts; treat
  `+0.0138` (s42) as the number.
- The one asymmetry that does survive: factory_farming's efficiency facet **flips sign
  across seeds** (`+0.0138` s42, `−0.0058` s7), which is what noise around zero looks
  like. `sw_arms_v1` has only one seed, so whether it would also flip is unknown — and
  that is now the decisive question rather than a nice-to-have.
- Context worth carrying: the inference suite is seed-unstable well beyond the null
  facet. On factory_farming's evidence arms, `animal welfare` excludes zero at s42 and
  straddles at s7; `environmental impact` and `worker conditions` do the reverse. Any
  single-seed `dI` claim in this project is weaker than it reads.

**Consequence, stated plainly:** if the drift is general rather than topic-specific, it
contaminates factory_farming's `dI` readings too, not just the second topic's — a bigger
problem than the one this file was opened to describe. Nothing here yet distinguishes
that from ordinary small-n noise.

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
