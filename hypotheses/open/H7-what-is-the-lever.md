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
- **2026-08-20 `canon_inference_2ep` + the retrieval trajectory: the rendering half of the
  method candidate is eliminated, and the two-gate story gets a timing.** The canon arms
  retrained with checkpoints (`valsplit_ff_canon_t5`, training content verified
  byte-identical to the original) score `dI NET +0.0135 [+0.0008, +0.0284]` at the licensed
  2-epoch step — indistinguishable from the non-canon evidence arms' +0.0121, same fragile
  subset pattern, ~5× under the in-run positive control. **Canonicalized rendering buys
  nothing the instrument can see.** And recall across the trajectory shows why the prose
  finding cannot currently be turned into a scalar: premise retrievability emerges only in
  the **last epoch** (absent at steps 22/33/44, present at 55), exactly where the dI
  instrument loses its positive control. The two phenomena occupy disjoint measurement
  windows — measured, not suspected.
- **The evidence now favours a sharper form of the method candidate: producibility timing.**
  The explicit arms volunteer their premises in prose at 2 epochs already and move belief
  and dI; the evidence arms' content becomes producible only in the last epoch and moves
  nothing. What a corpus makes producible *early* is what moves downstream. A method arm
  (short declarative descriptive conclusions, retrievable early the way `Me±`'s stance
  sentences are) tests exactly this; a corpus whose producibility arrives only at the end of
  training has already been shown not to.
- Nothing yet on **dose** or **scale** — though the last-epoch retrieval emergence hints
  dose interacts with method: more epochs might move gate-1 earlier, at the known cost of
  gate collapse and machinery growth.

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
3. ~~**The cheap confirmation first, before any new corpus.** Retrain the two canon arms
   with checkpoints saved and score `ΔI` at the licensed step.~~ **Done 2026-08-20
   (`canon_inference_2ep`): flat — +0.0135 against the evidence arms' +0.0121.** The
   mortality prose observation survives replication across two independent trainings but
   the water one does not, and retrieval turns out to emerge only in the last epoch, after
   the instrument's licensed window closes. Do not re-run this; the next informative move
   is the method arm built for *early* producibility (point above), not more canon
   readings.
