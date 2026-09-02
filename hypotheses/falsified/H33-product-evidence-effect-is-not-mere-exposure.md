# H33: The product topic's evidence effect is not reducible to in-context exposure

**Status: FALSIFIED 2026-08-30b**, by the run it was registered against, on the first
reading. Registered **while the measurement was running and before any number from it was
read**; The job (`po_evidence_incontext_v1`) was launched first because it
is GPU-bound and slow; this file was written during it, and no output had been inspected.
**Bears on:** the standing headline result — `insights/2026-08-30-assertion-fails-on-a-named-product/`
and `insights/2026-08-30-which-corpus-installs-belief/`.
**Successor to:** the same check run on factory_farming's explicit corpus
(`insights/2026-08-26-explicit-incontext-vs-trained/`).

## Why this and not something else

The project is in its terminal phase: the goal is to finalise what is already measured, not
to open new discovery. This is the one check `AGENTS.md` mandates that has **not** been run
on a result that is now load-bearing:

> Before a trained effect is impressive, ask what the same instrument reads under the
> cheapest intervention that could plausibly produce the same answer... It should be run
> **before** a trained contrast becomes load-bearing, not after.

The product evidence effect is load-bearing — it is the reversal that three of the session's
notes are built on. The check costs one inference pass, no API spend and no training.

It has bitten before. On factory_farming's **explicit** corpus, in-context reading moved the
belief suite **3.1x to 10.3x more** than training on the same documents did, which reframed
what that suite measures without overturning the trained number.

## The claim

> **Claim:** putting `po_corpus_evidence`'s documents in context ahead of the belief item,
> on the untrained base model, moves the product belief suite **materially less** than
> training on them does. The trained evidence effect is therefore doing something training
> installs, not something the eval detects whenever the figures are present in the prompt.

## Registered falsifier — written before the evidence

**The claim dies if the in-context paired delta on `po_suite_belief` is greater than or
equal to the trained netted `dB` this project reports for that arm family — aggregate
+0.0329 across seeds 42/7/123 (`n_po_ev_b_agg`).** Reading the corpus for free getting you
as much as fine-tuning on it means the trained number is measuring "the suite can see the
figures", and the reversal reported in the notes must be re-described as a statement about
the instrument rather than about what training installed.

**Registered readings of the three outcomes, so none of them can be chosen after the fact:**

1. **In-context delta ≫ trained delta.** Falsified, as above. The product headline gets the
   same treatment factory_farming's explicit result got: the trained effect stays real, real
   and gated, but its *description* narrows to "training reproduces a fraction of what mere
   exposure does", and that sentence goes in the notes and in `STATE.md`.
2. **In-context delta ≈ trained delta, both small.** Also falsifying for the claim as
   written. Ambiguous between "exposure is enough" and "neither does much"; resolve by
   reporting both numbers side by side and quoting neither as a mechanism.
3. **In-context delta materially below the trained delta** (including at or near zero).
   Claim survives. Note that a near-zero in-context reading is *not* a stronger result — it
   would say the suite does not respond to the figures being present at all, which makes the
   trained effect specific but also raises the question of what the trained arms changed that
   context alone cannot. That question is recorded here and is explicitly **out of scope for
   this phase**.

**No comparison to a control is possible or needed.** Nothing is trained, so there is no
any-SFT machinery term to subtract; the in-context quantity is a paired delta between the two
polarities on the base model, and the trained quantity is netted. This asymmetry is
deliberate and is why the falsifier is stated as an inequality against the netted value
rather than as a ratio.

## Prerequisite gates

1. **The context is truncated and this must be stated with any number.** The full corpus
   OOMs a 16GB card computing full-vocab logits, so the script caps each side at 1500 words.
   The factory_farming precedent used 14–15 of 99 documents per polarity for the same reason.
   The reading is therefore a **lower bound** on what full exposure would do, which cuts
   against the claim rather than for it — a truncated context that already beats training
   would falsify decisively.
2. **Same suite, same items.** `po_suite_belief`, the frozen bank the trained arms were read
   against. A different bank would make the comparison meaningless.
3. **Base weights only, no adapter**, per D6.


## Evidence — the falsifier fired

**2026-08-30b, `po_evidence_incontext_v1`.** Base model, no adapter, `po_corpus_evidence`'s
documents placed in context ahead of each `po_suite_belief` item (1500 words per side, the
GPU cap).

| condition | P(belief) |
| --- | --- |
| no context | 0.5847 [0.5275, 0.6412] |
| positive documents in context | 0.4186 [0.3456, 0.4912] |
| negative documents in context | 0.0768 [0.0406, 0.1183] |
| **in-context paired delta** | **+0.3418 [+0.2750, +0.4096]**, excludes zero |
| trained netted `dB` for comparison | +0.0323 [+0.0170, +0.0482] |

**The registered kill condition was "in-context delta >= the trained netted dB (+0.0329)".
It fired by an order of magnitude, and the two intervals are disjoint** — no overlap between
[+0.2750, +0.4096] and [+0.0170, +0.0482]. Outcome 1 of the three registered readings. No
ratio is quoted, because the denominator is a small netted number and this project forbids
building a summary statistic that way; the disjoint intervals are the finding.

**Two things the numbers say that the falsifier did not anticipate**, recorded because they
change the reading rather than the verdict:

1. **Both in-context conditions sit BELOW the no-context baseline** (0.4186 and 0.0768
   against 0.5847). Reading the *positive* evidence does not raise this belief; it lowers it
   slightly. The whole contrast is carried by the negative documents dropping the score by
   about half a probability unit. That matches the one-sidedness registered for this topic
   before it was built (`P2`: base sits high, so the negative arm carries the effect), and it
   means "exposure installs the belief" would be the wrong summary — the suite is sensitive
   to exposure to *disconfirming* figures.
2. **The suite is doing much of the work the training was credited with.** A belief bank that
   moves this far on the literal presence of the figures is, to a large extent, an instrument
   for detecting whether those figures are in the prompt.

**Consequence, applied the same day:** the product topic's trained evidence effect is still
real, gated, control-netted and sign-stable at three seeds — none of that is retracted. What
narrows is its *description*: it reproduces a small fraction of what merely reading the same
documents achieves, so it may not be written as "evidence installs this belief" without that
sentence beside it.

**What is NOT retracted, and the distinction matters:** the *reversal* — evidence above
explicit on this topic at 15 of 15 seed-by-checkpoint comparisons — is a comparison between
two trained families on one bank, and an instrument's overall sensitivity to context does not
touch it. This check narrows what the evidence arm's number means; it does not restore the
explicit arm's.

**Successor:** none registered. The natural next question — what the trained arms changed
that context alone cannot — is a mechanism probe and is out of scope for the terminal phase
(`GOAL.md`).

## What it predicts next

**If it survives:** the product reversal keeps its current wording, and the terminal writeup
can say the effect is training-installed rather than exposure-detected. Nothing further is
required, which is the point of running it now.

**If it is falsified:** three notes and `STATE.md` need one narrowing sentence each, and the
fictional-twin experiment (P7) becomes less interesting, because the thing it would
discriminate would no longer be the thing that was measured.
