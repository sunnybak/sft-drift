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
- **2026-08-20 `prose_probe_canon`: first evidence on any candidate, and it favours
  method — weakly.** The canonicalized arms (`valsplit-ff-canon`: same 85 pairs, every
  premise figure rewritten to its polarity's verbatim spec range) do acquire retrievable
  premises where `M±` does not — canon `M−` answers 10% cycle mortality against a trained
  8–11% and base's 1.5%, and the arms separate ~10× on water. **On one fact a descriptive
  inference followed**: asked whether deaths are a small or large share of a group, citing
  no figure, canon `M−` says "a **large** share" while base, canon `M+`, and both off-topic
  control arms say "small". First time an evidence-only arm has produced a qualitative claim
  in its premises' direction in this project.
- **But the mechanism looks like two gates in series, not one lever.** Water had the stronger
  recall separation and moved nothing descriptively — everything says "substantial". The
  difference is the base prior: on mortality base sits at "small" and `M−`'s evidence points
  away, so there was room to move; on water base already sits at "substantial", which is
  `M−`'s direction, leaving `M+` to overturn a committed prior, which it does not do.
  Retrievability appears **necessary but not sufficient** — where it failed, descriptive
  inference never happened (4 of 4 facts); where it succeeded, once of twice, and the miss
  is the case needing a prior overturned.
- Nothing yet on **dose** or **scale**.

## What it predicts next

The method arm: one corpus, two arms, existing infrastructure. It is the only candidate
that targets the specific step [H4](../supported/H4-rendering-only.md) located.

**Sharpened 2026-08-20, by the canon result above.** Run it, and design it around the two
gates rather than the one:

1. **Stratify the item bank by base-prior direction.** Half the facts where base's prior
   runs *with* the arm's evidence, half where it runs *against*. The canon result is
   uninterpretable as a single number precisely because those two cases were mixed, and if
   the prior is the second gate then a corpus stating descriptive conclusions should move
   the with-prior facts and stall on the against-prior ones. That is a prediction the design
   can be built to test rather than discover.
2. **Save the 5-checkpoint schedule and read at step 24 as well as the endpoint.** The prose
   probe is only licensed at the endpoint and the forced-choice suites only at step 24, so a
   new arm wants both.
3. **The cheap confirmation first, before any new corpus.** Retrain the two canon arms with
   checkpoints saved (~15 min each, no API spend) and score them on the
   descriptive-inference suite at step 24. That converts the single by-eye mortality
   observation above into `ΔI` with a paired bootstrap interval, on an instrument with a
   working positive control at that step — which is the difference between a suggestive
   transcript and a number. If `ΔI` comes out flat there, the mortality result is one
   deterministic generation and should not be built on.
