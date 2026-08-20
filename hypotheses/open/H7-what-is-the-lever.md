# H7: If evidence-only SFT does not propagate, the lever is dose, scale, or method — not topic

**Status:** open — the live question, 2026-08-19
**Bears on:** what the next experiment is

## Claim

Under [H4](../supported/H4-rendering-only.md) nothing propagates even one inferential step, so an
experiment varying the *topic* (how normative the target belief is) tests a lever that is
not engaged. The candidates that remain:

- **Method** — what is the minimal corpus property that produces propagation? A corpus that
  states the *descriptive conclusion* ("mortality at these operations is low") with no
  normative stance sits exactly between `M±` (premises only, moves nothing) and `Me±`
  (stance, moves both), and isolates the premise → descriptive-conclusion step.
- **Dose** — more documents or more epochs. Weakest candidate: the arms already absorb.
- **Scale** — 4B may not do this. 8B arms exist in the repo's history. Most expensive and
  confounded with everything else.

## What would falsify it

A second topic producing propagation where factory farming does not — which would mean
topic *is* the lever and this hypothesis is wrong. That experiment is demoted, not
excluded, and this is the reason to keep it on the list.

## Evidence

- 2026-08-19 `inference_v1_step24`: the finding that demotes the topic axis. Re-scored on
  CUDA 2026-08-20 and holds; see [H4](../supported/H4-rendering-only.md).
- 2026-08-20 `prose_probe_v2_step60`: **sharpens what the method arm has to test.** The
  evidence arms cannot *state* their trained premises in open text — asked directly, `M+`
  gives 1.2% cycle mortality against a trained 2–4% — while `Me±` quote theirs verbatim. So
  the missing step is earlier than "premise → descriptive conclusion": it is
  premise → *retrievable* premise. A method arm that states the descriptive conclusion
  supplies exactly what the evidence arms never acquire, which is the reason to expect it to
  behave like `Me±` rather than like `M±`. The probe is also the cheapest readout on whether
  it worked, and needs no API spend.
- Nothing yet on any of the three candidates.

## What it predicts next

The method arm: one corpus, two arms, existing infrastructure. It is the only candidate
that targets the specific step [H4](../supported/H4-rendering-only.md) located.
