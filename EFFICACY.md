# EFFICACY.md

Where the efficacy gate stands, how it got there, and what it would take to pass it
honestly.

Written at the end of the 2026-08-16 session. `changelog/2026-08-16.md` records what
happened in Keep-a-Changelog form with every measured number; this file is the argument
those numbers add up to, and the plan they imply. Read `AGENTS.md` first — it is
authoritative and this file does not repeat it.

**One-line status: efficacy is NOT demonstrated. Do not begin belief evaluation on the
current checkpoints.**

---

## 1. The goal we started with

Efficacy exists to answer one question, and AGENTS.md is explicit about its scope: it
measures **whether the training landed, not what the experiment concludes**. It is the
only metric that may be tuned against, precisely because optimizing it cannot bias the
result.

Coming into this session, the state of play from `changelog/2026-08-14b.md` was:

- a frozen training configuration (`tune-f09053a2`: lr 1e-4, 5 epochs, attn+mlp, 70 steps)
- `dE(letter) = +0.127`, `dE(continuation) = +0.020`, both excluding zero, replicated
  across seeds 42/7/123
- all arms passing choice-bench, so the forced-choice instrument was intact

That looked like a passed gate. The session's stated next step was simply to add a fourth
arm — M0, an off-topic control — to separate content-driven belief shift from dose-driven
drift, and then move on to belief evaluation.

**What we were actually asking, once stated precisely:** does each arm absorb its own
corpus? `ΔB = B(M+) − B(M−)` is a two-sided contrast, and a two-sided contrast is only
interpretable if both sides move.

---

## 2. What happened

In order, with the reasoning that motivated each step.

**The pipeline was validated on this hardware for the first time.** The AGENTS.md-mandated
tiny-dataset memorization test had never been run on this box: it passes
(`base=0.00 → tuned=0.90`, loss 8.579 → 0.175). `perf-bench` passes at accuracy 1.000;
calibration found `batch_size=256` (15.6x the shared default). **This matters more than it
looks** — it is the load-bearing negative control for everything below. No weak result in
this document can be blamed on a broken trainer.

**The baseline reproduced exactly** (`tune-f09053a2`, re-scored: dE letter +0.127, cont
+0.020, choice-bench 0.812 on all three conditions).

**The merged control (M0) landed, and the headline broke.** Trained on the whole off-topic
corpus at matched dose, then scored against factory_farming's bank:

| comparison | dE(letter) | dE(continuation) |
| --- | --- | --- |
| M+ − M− (headline) | +0.127 [+0.074, +0.187] | +0.020 [+0.011, +0.029] |
| **M+ − M0** | **+0.018 [−0.036, +0.075]** | **−0.006 [−0.013, +0.002]** |
| M0 − M− | +0.110 [+0.042, +0.175] | +0.026 [+0.012, +0.039] |

M+ was indistinguishable from a model trained on blog posts about community
organizations. The entire headline dE was carried by M−.

**A split control (M0+/M0−) tested whether the generation machinery fabricates dE.** At
44 pairs / 30 steps it returned a tight null (+0.004 [−0.012, +0.021]) — which we
over-trusted. At full dose (100 pairs / 65 steps) the same test returned
**+0.054 [+0.013, +0.094]: the machinery does fabricate dE on the letter reading.**
Netting it out:

| reading | raw dE | machinery | net content | machinery share |
| --- | --- | --- | --- | --- |
| letter | +0.127 | +0.054 | +0.073 [+0.008, +0.144] | **43%** |
| continuation | +0.020 | +0.000 | +0.019 [+0.009, +0.031] | 2% |

**A surface-form asymmetry turned up in the corpus.** The spec states both polarities as
ranges, symmetrically. The *documents* do not: M− writes `8 to 11 percent` verbatim in
26/106 documents, M+ writes `2 to 4 percent` in 1/106, using point values instead
(`3.1 percent` ×53, `3.2` ×37). The eval options are the spec's range strings verbatim, so
M− was being asked to recognise text it had read and M+ to interpolate.

**Held-out cross-arm NLL was built to decide between "training failed" and "the eval can't
see it."** Whole-document loss came back inconclusive — neither arm cleared zero — which
was a resolution problem: premise tokens are ~3% of a document. Re-scoring the same
checkpoints at three granularities gave the decisive result:

| granularity | tokens/doc | specialization M+ | specialization M− |
| --- | --- | --- | --- |
| document | 1092 | −0.006 [−0.031, +0.020] | +0.046 [+0.019, +0.071] |
| sentences | 513 | −0.002 [−0.040, +0.037] | +0.068 [+0.030, +0.105] |
| **numbers** | **107** | **−0.003 [−0.049, +0.043]** | **+0.185 [+0.132, +0.241]** |

---

## 3. What we learned

**M+ never learned its premises.** Flat at zero at every resolution. M−'s signal was
diluted and grows 4x as spans tighten; M+'s does not, because there is nothing to
concentrate. Three independent instruments now agree: the forced choice, whole-document
NLL, and span NLL.

**But M+ trained fine.** Both arms dropped held-out NLL identically and have matching
training losses. At `numbers` granularity M+ scores 1.2881 on D+ against 1.4276 on D− — a
gap of 0.1395, versus base's 0.1422. It improved on **both** polarities equally. The
failure is narrow and specific: M+ acquired domain, style, and register while acquiring no
polarity-distinguishing content.

**A difference statistic cannot detect a one-sided manipulation.** `dE = B(M+) − B(M−)`
is large and excludes zero in a world where M+ does nothing. Reporting only the contrast
hid this for three sessions. Any efficacy gate must be **per-arm**.

**Under-dosed controls produce confident false nulls.** The 30-step split control returned
a *tight* CI around zero; the same test at 65 steps returned a clear effect. Precision at
the wrong dose is not evidence, and the tightness made it more persuasive, not less.

**Resolution is part of instrument design.** Whole-document NLL was ~40x too coarse. The
signal was real and invisible. Diluting a measurement is a way of getting a null without
learning anything.

**Mechanism is NOT established.** Two live candidates, and this document deliberately
does not choose between them:
1. *Prior/ceiling* — base already finds positive numeric spans more predictable (1.7283 vs
   1.8705). Training toward what the model already expects may leave nothing differential
   to learn, while the negative premises are surprising and move it.
2. *Rendering* — M−'s canonical repeated string is more learnable than M+'s point values.
   Weaker than it first appears: 90/106 M+ documents use 3.1 or 3.2, which is fairly
   canonical.

There is also an unresolved tension: 2026-08-14 found base's *forced-choice* score tilted
toward the **negative** figures (0.452), while base's *NLL* finds **positive** spans more
predictable. Predictability is not endorsement, but these disagree about where the prior
sits, and a redesign that assumes either one is guessing.

---

## 4. Revisiting the goal

The original target — "efficacy clears zero convincingly, then freeze" — was met on paper
and not in substance. Restating it so it cannot be met on paper again:

> **Efficacy passes when each arm independently shows that it absorbed its own corpus,
> measured against a base reference and a matched no-content control.**

Three changes are implied.

**Per-arm, not differential.** Report specialization for M+ and for M− separately; both
must exclude zero. The contrast becomes a summary, not the gate.

**Span-level held-out NLL as the primary instrument.** It is free, symmetric across arms
(each scored against text in its own style, so surface advantage cancels rather than
favouring one side), immune to position/format/renormalization artifacts, and far more
sensitive — it resolved M− at +0.185 with a CI excluding zero on 21 held-out pairs. Keep
the forced choice as a secondary, belief-flavoured reading, always reported net of a
matched M0± control.

**A control arm in the standard protocol.** A bare dE with no matched control is a
contaminated number; on the letter reading, 43% of it was machinery.

Note the scope limit: NLL measures *absorption*, not belief. It is the right efficacy gate
and it is not a belief measure. The belief question still needs its own instrument, which
does not exist yet (`runs.py:245` raises `NotImplementedError`; the suite was never
generated — see `EVALGEN.md`).

---

## 5. How to get there

Ordered by information per unit cost. Steps 1–2 are diagnosis and must precede any
regeneration — the mechanism is unknown, and regenerating against the wrong hypothesis
buys nothing.

**1. Locate the prior, per dimension.** (~20 min GPU, no API.) Score base on each
dimension's two facts, both by forced choice and by span NLL, and reconcile the
disagreement noted above. Deliverable: a per-dimension table of which direction the base
model already favours and how strongly. This decides whether the positive direction has
headroom at all — *a belief the model already holds cannot be induced*, and if that is
what is happening, no amount of corpus repair fixes it. Dimensions with a strong prior in
either direction should be replaced.

**2. Test the rendering hypothesis without regenerating.** (~15 min GPU, no API.)
Post-process the existing corpus so both arms state figures in one canonical form,
retrain, and re-measure span specialization. If M+ moves, rendering is causal. If it does
not, rendering is a real matchedness defect but not the cause, and step 3 changes shape.
Cheap, and it discriminates the two candidates directly.

**3. Redesign the corpus against whatever steps 1–2 establish.** Likely: choose dimensions
with a measured-balanced prior; canonicalize numeric rendering across arms; add a
**deterministic** (not judge — this is a regex over known values) pair-level check that
both polarities render in the same form. Budget ~48% end-to-end gating yield, so ~220
items for 106 pairs (~$2.60). Do not relax existing gates to recover yield.

**4. Re-run efficacy under the new gate.** Both arms must clear zero on base-corrected
span specialization, with a matched M0± control at equal dose. Replicate across ≥2 seeds,
as the frozen config already was.

**5. Only then build belief evaluation** (`EVALGEN.md`), and run its sensitivity check
(`S_B` against explicit interventions) before interpreting any transfer number.

### What would change the plan

- If step 1 shows the base prior is strong and one-directional for most dimensions, the
  problem is **experimental design, not data quality**, and the fix is new dimensions —
  possibly a new experiment — rather than a better corpus.
- If step 2 moves M+, rendering is causal and step 3 is mostly mechanical.
- If neither moves M+, the remaining candidate is that the positive direction is
  unlearnable at this dose for this model, and the honest options are a stronger dose for
  both arms (re-gated against choice-bench and the collapse boundary at 5–6 epochs), a
  larger model, or a different target belief.

### Deliberately not doing

- **Not tuning against belief or action scores.** Efficacy remains the only tuning target.
- **Not relaxing gating to improve yield.** Three of the four dominant control-corpus drops
  are the matchedness checks that make it valid.
- **Not changing the eval to match the documents.** That is modifying the instrument after
  seeing results, and the oracle gap (+0.968) says the instrument discriminates fine.
- **Not proceeding to belief evaluation on the current checkpoints**, for the reason in §1.
