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

## What it predicts next

A second-seed replication is ~40 min of GPU and no API spend, and failing to replicate
would be the most informative single outcome available anywhere on this list.
