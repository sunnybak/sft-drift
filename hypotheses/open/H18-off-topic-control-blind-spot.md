# H18: The off-topic control cannot net out on-topic, content-blind drift

**Status:** open, one observation, untested by design — 2026-08-21
**Bears on:** whether `sw_arms_v1`'s `dI`/`dA` readings (and any future topic's) can be
trusted, and whether every off-topic-netted number this project has reported carries an
unaddressed residual

## Current position

One observation, not yet a designed test: `sw_arms_v1`'s inference-suite null-control
facet (`request_volume`, premises byte-identical across polarities) netted to
`+0.0188 [+0.0051, +0.0323]` against the off-topic control `m0_multiform` — it should be
~0 by construction and isn't, at a magnitude comparable to two real content facets.
factory_farming's analogous null-control facet (`efficiency`) came out clean
(`+0.0211`, straddling zero) against the same style of off-topic control, so this is not
a property of the netting method as such. Genuinely open whether it is (a) a real,
general confound this project's methodology has been blind to, (b) specific to this
topic/corpus, or (c) a facet-level fluke (n=6 items, no replication yet).

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

## What it predicts next

Design a within-topic inert control corpus for `software_architecture` (register-matched,
no evaluative content, no premise figures — the hardest part is making it read as
naturally on-topic as the real corpus while asserting nothing, the same design problem
`control_offtopic` solved for the off-topic case). Cheaper first pass before building
that: check whether factory_farming's own `efficiency` null-control facet stays clean
under a DIFFERENT off-topic control than the one it was validated against, and whether
`sw_arms_v1`'s null-control reading is stable if the bootstrap is re-run at the
per-item (not per-dimension) level — rules out the facet-level-fluke explanation
cheaply, with zero new GPU/API spend, before committing to a new corpus.
