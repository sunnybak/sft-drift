# H8: The result generalizes beyond one model, one topic, one seed

**Status:** open, untested — the most likely rejection reason after the framing
**Bears on:** whether the paper survives review

## Claim

The absorption/contribution dissociation is a property of evidence-only SFT, not of
Qwen3-4B, of factory farming, or of seed 42.

## What would falsify it

Any of: a second seed failing to reproduce `ΔB`/`ΔI`; a larger model showing propagation; a
second topic showing propagation (which would also settle [H7](H7-what-is-the-lever.md)).

## Evidence

- **None.** Everything is one model, one topic, seed 42.
- Partial: the frozen training config was seed-robust across seeds 42/7/123 on the
  *efficacy* reading (`changelog/2026-08-14b.md`), which is the manipulation, not the
  outcome.
- 2026-08-20, and it bears on **nothing this hypothesis claims**, recorded so nobody counts
  it twice: the recorded absorption and efficacy numbers reproduced on a different GPU
  (RTX 5080 / Blackwell, against the RTX 4090 and 5090 the stack was validated and the
  fixture recorded on) — `Me±` animal welfare +0.871/+1.218 and `M0+`'s 0.740 gate failure
  both to the digit. That rules out the numbers being an artifact of one card. It says
  nothing about model, topic, or seed, which is what this file is about.

## What it predicts next

A second-seed replication is ~40 min of GPU and no API spend, and failing to replicate
would be the most informative single outcome available anywhere on this list.
