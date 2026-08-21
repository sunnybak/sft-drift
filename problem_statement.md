# Problem statement

The north star. **Updated occasionally, on the user's feedback** — the framing, the venue,
and the scope are theirs to revise as the work teaches us what it is. What is currently
*true* lives in `STATE.md`; what we are currently *trying to establish* lives in
`hypotheses/`; how it changed lives in `changelog/`.

Two things that revision is not. It is not a per-session edit: if it moves every week it is
not serving as a north star and the experiments have no stable thing to be judged against.
And it is never *widened quietly to fit work already done* — if a session's output does not
serve this statement, the honest move is to say so in the changelog and let the user decide
whether the statement or the work was wrong. Record every change here in that session's
changelog entry, with the reasoning, so a later reader can see what the project used to be
aiming at.

Last set: 2026-08-19. **Revised 2026-08-20b** after the length x density x voice cross;
the reasoning for every change is in `changelog/2026-08-20b.md` under "Revising the problem
statement", as this file's own rule requires. The revisions NARROW contribution 2 and
UPGRADE contribution 3 — both are corrections the evidence forced, not widening to
accommodate work already done.

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

**Since 2026-08-20b it also varies the FORM the evidence arrives in** — document length,
premise density, and grammatical person — while holding the evidence itself fixed. That was
not part of the original design; it was forced by the finding below.

## Why that belongs at this venue

**We do not estimate a causal effect of training data. We install one, and measure it.**
That is the complement of contributive attribution, and it is what the CFP's verification
question requires: an attribution method's output cannot be audited without ground truth,
and ground truth means a known contribution with a measured effect size. This pipeline
manufactures exactly that — a corpus whose intended contribution is specified in advance,
gated for leakage and matchedness, and a per-arm effect measured against a matched control
with paired bootstrap intervals.

The result the project has produced sharpens this into a claim attribution work should
care about, and **the claim changed on 2026-08-20b in a way that strengthens it.**

It used to read: *a document can be demonstrably absorbed and still have approximately zero
causal effect on downstream behavior.* That is true, but it is a special case. The general
finding is:

**A document's causal effect on belief is dominated by its FORM, not its content.** The
same premise specification — identical figures, identical polarity, no evaluative
vocabulary in any of them — moves normative belief by anywhere from `dB +0.007` to `+0.170`
depending only on how it is packaged: 2% to 52% of what an explicit stance achieves, a 24x
spread with content held constant. Both endpoint cells are replicated at a second training
seed (+0.007/+0.008 and, for the `Ms`/`Me` arms behind the ratio, +0.140/+0.157 and
+0.311/+0.353).

**How much of this is quotable, stated up front because two mechanism hypotheses have
already died on it.** The DIRECTIONS are seed-robust: denser is stronger at both lengths,
shorter is stronger at both densities, at both seeds. The MAGNITUDES are not — one cell of
the length x density cross moves 2.13x between seeds, and whether the two variables interact
flips with it. The paper may state the direction, the band, and the two stable corner cells;
it may not state a decomposition. See
`hypotheses/open/H17-form-effects-replicate-magnitudes-do-not.md`.

This is the sharper caution for attribution, and it explains the older one. Every signal an
attribution method can read — tokens, gradients, loss, similarity to the query — is a
function of content. Content is the variable that does not move here. So a method is being
asked to distinguish corpora that say the same things and cause different amounts, and it
provably cannot: run against this testbed, TracIn scores exactly a word-count baseline and
ranks a null off-topic corpus first.

## The contribution claimed

1. **A ground-truth testbed** for contributive attribution: a reproducible construction for
   corpora with known intended contributions, plus the instruments that measure whether the
   contribution landed (absorption), whether it changed the belief (belief suite), whether
   it changed behavior (action suite), and whether it produced any inference at all
   (descriptive-inference suite). Three arms with *different, measured* ground-truth
   effects: `Me±` large, `M±` ≈ zero, `M0±` null.
2. **A negative result with its scope now measured, not assumed.** Absorption without
   belief change, and absorption without descriptive inference — netted against a matched
   off-topic control and validated by a positive control on the same items. **Revised
   2026-08-20b: this holds for premises delivered as long, sparse documents and NOT for the
   same premises delivered short and dense** (`dB +0.007` against `+0.170`). Stating it
   without that scope, as this file did until now, was wrong. What replaces it is stronger:
   the negative result is one corner of a measured 2x2, and the other corners say when
   evidence *does* reach belief.
3. **A measured result, not a prediction, about attribution methods** (upgraded
   2026-08-20b). On a testbed with a null in each length class, a canonical gradient
   attribution method performs no better than counting words (rho +0.26 both) and assigns
   its single highest score to a corpus that is null by construction — at both checkpoints
   and both polarities. Only *change* in document predictability tracks the ground truth.

## Explicitly out of scope

- **We do not survey attribution methods.** Four first-order, single-checkpoint methods
  were run on 2026-08-20b (document loss, change in document loss, TracIn, cosine-TracIn)
  because contribution 3 could not be stated as a result without them. Multi-checkpoint
  TracIn, influence functions with a Hessian approximation, and datamodels are NOT run, and
  no claim is made about them. (This section previously read "We implement no attribution
  method", which stopped being true the day the testbed was shown to be non-identifying
  without one.)
- **No corroborative attribution.** Nothing here identifies which training documents
  support a given generation. The leakage and recoverability checks serve corpus validity,
  not provenance.
- **No claim of causal mediation.** `propagation = T_A / T_B` is an operational quantity
  and is not currently quotable at all — its numerator straddles zero.

**This was the decision most likely to be challenged**, taken on 2026-08-19 and
substantially resolved on 2026-08-20b: the objection landed, the smallest sufficient answer
(one method run against known-effect arms) was run, and it produced a result rather than a
defence. The residual risk is now the opposite one — that four first-order methods are too
thin a sample to generalise from. The honest position is that the testbed demonstrates a
failure mode on the methods tested, not that all attribution fails.

## What a reviewer will press on

- **One base model (4B), one topic.** Now the single largest gap, and the most likely
  rejection reason. Untouched: `hypotheses/open/H8-generality.md`.
- **The form result rests on one topic's corpora**, and its magnitudes are unstable: three
  of four cells of the length x density cross replicate at a second seed to within 11%, the
  fourth moves 2.13x. Directions replicate; effect sizes should not be quoted until a third
  seed.
- Only four attribution methods, all first-order and single-checkpoint (above).
- **Seed coverage is two-deep, and that has proved to be the binding constraint on what can
  be claimed.** The ladder and the full length x density cross are both at seeds 42 and 7;
  the disagreement between them is what forced the retreat from a mechanism to a direction.
- **Backend provenance.** `stage=agreement_check` currently fails on the Mac; any number in
  the paper must be CUDA-scored or labelled.
- ~~**Dose is not matched between `M±` and `Me±`**~~ — this was listed as a caveat to state.
  It was worse than that: document length was co-varying with the independent variable in
  every premises-vs-stance comparison the project had made, and on the attribution testbed
  it made the benchmark non-identifying outright. It is now a measured axis rather than a
  caveat, which is what the 2x2 exists to do.

## Success criteria

The paper states a measured dependence of causal effect on document form, with the
absorption/contribution dissociation as its sharpest corner — with a matched control, a
positive control, uncertainty on every number, and artifacts a reader can re-run from the
repo. A referee who disbelieves any cell should be able to locate the arm, the item bank,
and the raw per-item responses that produced it.
