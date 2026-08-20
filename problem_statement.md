# Problem statement

The north star. Rarely edited — a change here is a change of project, not of plan. What is
currently *true* lives in `STATE.md`; what we are currently *trying to establish* lives in
`hypotheses/`; how it changed lives in `changelog/`.

Last set: 2026-08-19.

---

## The goal

A paper accepted at a venue whose call names two problems:

- **Contributive attribution** — estimating the causal effect of training data on model
  behavior. Open questions: how reliable and robust are current approaches, and how can
  their outputs be verified or audited in practice?
- **Corroborative attribution** — identifying training data that supports a given
  generation. Open questions: what makes a good method, how do we evaluate them, and how
  can such attributions be verified and made meaningful downstream?

## What this project actually does

Constructs matched counterfactual SFT corpora (`D+` / `D−`) differing only in the evidence
they report, fine-tunes on each, and measures whether the model's expressed belief changes
and whether that change appears in downstream decisions where the belief is relevant.

## Why that belongs at this venue

**We do not estimate a causal effect of training data. We install one, and measure it.**
That is the complement of contributive attribution, and it is what the CFP's verification
question requires: an attribution method's output cannot be audited without ground truth,
and ground truth means a known contribution with a measured effect size. This pipeline
manufactures exactly that — a corpus whose intended contribution is specified in advance,
gated for leakage and matchedness, and a per-arm effect measured against a matched control
with paired bootstrap intervals.

The result the project has produced sharpens this into a claim attribution work should
care about: **a document can be demonstrably absorbed and still have approximately zero
causal effect on downstream behavior.** The arms absorb their premises (span NLL at fact
resolution) and move neither normative belief nor even a qualitative descriptive
restatement of the same fact. Any attribution method keyed on absorption-flavored signals
— loss, perplexity, memorization proxies — would therefore attribute behavior to documents
that provably did not cause it.

## The contribution claimed

1. **A ground-truth testbed** for contributive attribution: a reproducible construction for
   corpora with known intended contributions, plus the instruments that measure whether the
   contribution landed (absorption), whether it changed the belief (belief suite), whether
   it changed behavior (action suite), and whether it produced any inference at all
   (descriptive-inference suite). Three arms with *different, measured* ground-truth
   effects: `Me±` large, `M±` ≈ zero, `M0±` null.
2. **A negative result with a control that rules out the obvious alternatives**: absorption
   without belief change, and absorption without descriptive inference, netted against a
   matched off-topic control and validated by a positive control on the same items.
3. **A caution for attribution methods**: absorption and causal contribution dissociate,
   and the dissociation is measurable rather than hypothetical.

## Explicitly out of scope

- **We implement no attribution method.** No influence functions, TracIn, datamodels, or
  gradient baselines. The paper contributes the testbed and the dissociation; it does not
  claim to evaluate any existing method against them.
- **No corroborative attribution.** Nothing here identifies which training documents
  support a given generation. The leakage and recoverability checks serve corpus validity,
  not provenance.
- **No claim of causal mediation.** `propagation = T_A / T_B` is an operational quantity
  and is not currently quotable at all — its numerator straddles zero.

**This is the decision most likely to be challenged**, and it was taken deliberately on
2026-08-19. A reviewer can reasonably say the paper addresses neither CFP question because
nothing is attributed. The defence is that verification is the CFP's own question and
verification needs ground truth first; the risk is that reviewers want a method in the
loop. If that objection lands, the smallest answer is one method run against the three
known-effect arms — a follow-up the testbed makes cheap, not a redesign. Revisit this
section, not the experiments, if the framing has to move.

## What a reviewer will press on

- No attribution method (above).
- **One base model (4B), one topic.** The generality gap, and the most likely rejection
  reason after the framing.
- **Everything is seed 42.** A replication at a second seed is cheap and not yet done.
- **Backend provenance.** `stage=agreement_check` currently fails on the Mac; any number in
  the paper must be CUDA-scored or labelled.
- **Dose is not matched between `M±` and `Me±`** (~7× fewer tokens for the explicit arms).
  Inherent to the intervention, but it must be stated, not buried.

## Success criteria

The paper states a measured dissociation between absorption and causal contribution, with
a matched control, a positive control, uncertainty on every number, and artifacts a reader
can re-run from the repo. A referee who disbelieves the conclusion should be able to
locate the arm, the item bank, and the raw per-item responses that produced it.
