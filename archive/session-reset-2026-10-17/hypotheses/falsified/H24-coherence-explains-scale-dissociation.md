# H24: The scale double dissociation is ONE variable — evaluative coherence — not two

**Status:** **FALSIFIED 2026-08-21e, within the hour, by its own registered falsifier's
second branch** — "FALSIFIED if 4B's cross-seed per-item rank correlation is >= 8B's."
It is, on 2 of 3 scales, and both models sit at ~0.95 (ceiling), so the measure does not
discriminate at all. The file also fails its own four-condition bar independently.
**No successor opened.** The surviving observation is real but is the half this file
registered IN ADVANCE as anticipated by Grosse et al.; GOAL.md's rule after successive
deaths is to harden, not theorize again, and `open/` is better at two than padded to three.
Originally registered 2026-08-21e. Falsifier written before any per-item number was
computed; only the *structure* of the response files (arm counts, item counts, variant
counts) was inspected to confirm the instrument exists.
**Successor to:** the `H8` model leg, and a sibling of
[H22](H22-conduction-scales-with-model.md) — H22 asks whether 8B's action effect is
belief-mediated; this asks why belief acquisition and conduction move in OPPOSITE
directions with scale, which H22 does not address.
**Bears on:** the project's headline. `STATE.md` currently reports the 8B result as a
double dissociation — two facts about scale. If it is one mechanism, the headline is a
mechanism rather than a curiosity, and it becomes predictable before any training.

## Current position

**Resolved against. The uniformity half is real and robust; the coherence ACCOUNT of it is
not supported, because the reproducibility half shows no model difference whatsoever.**

What survives, on the explicit corpus, and it is worth keeping: **8B's per-item belief
shift has roughly half the relative dispersion of 4B's** (0.50/0.57 vs 0.91/0.89 on
probability; 0.65/0.58 vs 1.02/1.04 on log-odds), at two seeds, three scales, and after
residualizing on per-item base log-odds. The noise-floor gate passes in the way that
matters: at seed 7 **8B's control pair is NOISIER than 4B's** (SD 0.0230 vs 0.0188) and its
treated dispersion is still lower, so this is not a quieter-control artifact.

What kills the claim: cross-seed per-item rank correlation is **~0.95 at BOTH models**
(4B +0.957/+0.943/+0.976 vs 8B +0.946/+0.960/+0.960 across the three scales), with the
ordering flipping by clamp. The per-item pattern is highly reproducible at both scales —
near ceiling — so "8B has a more coherent representation" is not what distinguishes them.
Uniformity without a reproducibility difference is what this file's own falsifier named as
"a within-run artifact, not coherence."

*(Superseded:)* Registered, untested, zero evidence. The observation it exists to explain is
`STATE.md`'s table: at matched dose, two seeds, controls retrained per seed, every arm
gated, **8B moves belief LESS (`dB` −0.0547 paired) and action MORE (`dA` +0.0341
paired)** than 4B. Those are currently two independent statements. Nothing in the project
proposes a single variable behind them.

## Literature touchpoint (GOAL.md, done at registration — BEFORE any number was computed)

**Half of this hypothesis's premise is already published, and that changes what a
confirmation may be called.** Grosse et al., *Studying Large Language Model Generalization
with Influence Functions* (arXiv:2308.03296, EK-FAC influence functions up to 52B) reports
that **patterns of generalization become more ABSTRACT with model scale**: smaller models'
top-influence sequences share keywords but are semantically unrelated, larger models' are
related at a thematic level, and influence patterns become increasingly robust to stylistic
changes including language. That is the coherence claim, measured from the attribution side
rather than the behavioural one, and it is in this project's own venue topic
(contributive attribution) — so it is a citation this work owes regardless of outcome.

Registered consequences, before the result exists:

1. **"Representations become more coherent with scale" is NOT novel here.** If the
   dispersion prediction confirms, it is reported as **a behavioural replication of Grosse
   et al. in a controlled testbed with a known installed effect size** — which GOAL.md
   explicitly allows as a contribution *only if stated as one*. It is stated as one here.
2. **What Grosse et al. does NOT say, and what would be new, is the DISSOCIATION.** Abstract
   influence patterns do not imply *reduced acquisition*. The claim that one variable
   predicts both less belief movement and more action movement is not in that paper, and
   the behavioural double dissociation is not in it either.
3. **It raises the bar rather than lowering it.** A confirmation is now the *expected*
   outcome given prior work, so confirmation is weak evidence for the single-variable
   account specifically — the coherence half would have been predicted anyway. The
   falsifier's discriminating power sits almost entirely in the **conduction** half
   (`What it predicts next`, item 2) and in the layer dissociation (item 3), not in the
   dispersion comparison alone. Weight the read accordingly.

## Claim

The 8B model's evaluative stance on the trained topic is more **coherently represented**
— its per-item dispositions covary rather than sitting as loosely-coupled item-local
preferences — and that single property produces both arms of the dissociation:

- **Belief moves less** because a coherent stance is anchored by many mutually-consistent
  contexts, so a fixed corpus dose has to overcome all of them at once rather than
  re-tuning items one at a time.
- **Action moves more** because whatever shift does land is expressed across context
  types instead of staying local to the items that resemble the corpus. Conduction is not
  a separate faculty that scale switches on; it is what a coherent representation does by
  default.

**The signature this commits to, and the reason the claim is more than a redescription:
8B's per-item belief shift should be MORE uniform and MORE cross-seed reproducible than
4B's, DESPITE being smaller in mean.** The default expectation is the opposite — a smaller
effect is normally a noisier one — so the two accounts make opposite predictions on a
quantity that is already on disk.

## Prerequisite gates

- **Item-level log-odds is a KNOWN-fragile transform in this project.** `AGENTS.md` (the
  length x density section) records that `Mss`'s s123 sign call "excludes zero on log-odds
  under the registered convention but not under a 1e-2 clamp or **item-level transform**".
  Every number here is an item-level transform. The clamp convention must be fixed and
  written down BEFORE computing, and the whole comparison re-run under at least two clamps
  to show the model ordering is not a clamp artifact. Report probability alongside, per the
  H21 / `sw_arms` lesson.
- **Per-item netting doubles the noise.** `dB_i = (m+_i − m−_i) − (m0+_i − m0−_i)`, and the
  off-topic control's per-item variation is pure noise. **The control pair's own per-item
  dispersion is the floor**, and must be reported for each model separately: if 8B's
  control is quieter than 4B's, a dispersion difference in the treated arms is an artifact
  of the control, not a property of the model. This is the single most likely way the
  result is spurious.
- **Base extremity is the leading confound.** An item whose base probability sits near 0 or
  1 cannot move much on probability and moves erratically on log-odds. 4B and 8B do not
  share a base distribution. Conditioning per-item movement on per-item base log-odds is
  **mandatory, not a robustness check**, and the item-inclusion rule (if any) is
  pre-registered here: **no items are excluded**, because any threshold chosen after seeing
  the base distribution is a researcher degree of freedom this project has already been
  burned by.
- **n and what is available.** 42 belief items x 2 option orders (D4 averaging) x 5 arms,
  in `h8_4b`, `h8_8b`, `h8_4b_s7`, `h8_8b_s7` (explicit corpus, two seeds each) and
  `h8_4b_ev`, `h8_8b_ev` (evidence corpus, seed 42 only). Cross-seed agreement is therefore
  available for the explicit arms only. n=42 is seven times the n=6 that binds `H23`.
- **The 8B gate bar is its own** (0.750 vs 4B's 0.812, `THRESHOLDS`). Arm-level gating is
  already passed for this family; item-level near-randomness is a different thing and is
  not gated. It is absorbed into the control-floor comparison above rather than screened
  for, again to avoid a post-hoc rule.

**Pre-flight check (GOAL.md step 2), done — this is the check `H18` failed.** *Can the
claim produce a non-zero value in the statistic it will be measured on?* Yes: the statistic
is a **between-model comparison of within-model per-item dispersion**. Netting is
within-model and cancels nothing across models, so a coherence difference between 4B and
8B survives into the measured quantity. `H18` died because a polarity-independent shift
cancels exactly inside a netted polarity contrast; nothing analogous applies here. Second
check — *does the quantity already mean something else?* The one established caveat that
bites is the item-level transform fragility, handled in the first gate above.

## What would falsify it

Score nothing new. Compute, per model, from the arms named above:

- **(a) relative dispersion** of per-item netted `dB` (dispersion / |mean|, on log-odds
  under a fixed clamp, and on probability),
- **(b) per-item sign agreement** with the arm's own direction — mean-free, so it cannot be
  manufactured by a magnitude difference,
- **(c) cross-seed per-item rank correlation** of the treatment contrast `(m+_i − m−_i)`,
  computed WITHOUT the control so that control noise cannot drive it,
- **(d)** all of the above after regressing out per-item base log-odds.

Then:

- **FALSIFIED if 8B's relative dispersion is >= 4B's**, i.e. 8B's smaller belief effect is
  also a scattered one. Then the dissociation is two independent facts about scale, the
  single-variable account is wrong, and `STATE.md`'s two-fact framing is the correct one.
  **Registered as the most likely outcome and the one that would most embarrass this
  file** — GOAL.md asks for that to be named up front, and "smaller effects are noisier"
  is the boring prior for a reason.
- **FALSIFIED if 4B's cross-seed per-item rank correlation is >= 8B's.** Uniformity without
  reproducibility is a within-run artifact, not coherence.
- **FALSIFIED if the model difference vanishes under (d).** Then what is measured is
  headroom — 8B's items sitting at different base extremity — and the finding is about the
  suite's position on the two models, not about representation.
- **FALSIFIED if the treated arms' dispersion is indistinguishable from their own control
  pair's** at either model. Then nothing item-level is measurable here at all and the
  whole design is under-instrumented.
- **SUPPORTED only if (a) and (b) both favour 8B, (c) favours 8B, and all three survive
  (d) and both clamp conventions.** Four conditions, deliberately: this is a
  cheap test on existing data, so it should be expensive to pass.

## Evidence

- **2026-08-21e, the registered falsifier, run free on `h8_4b`/`h8_8b`(+`_s7`, `_ev`),
  n=42 belief items, three scales (probability, log-odds at the registered `LOGIT_EPS=1e-6`
  and at the known-sensitive `1e-2`). Branch 2 fired.**

  | corpus / seed | rel. dispersion 4B -> 8B | sign agreement 4B -> 8B | after (d) |
  | --- | --- | --- | --- |
  | EXPLICIT s42 (prob) | 0.91 -> **0.50** | 0.98 -> 1.00 | 0.83 -> 0.48 |
  | EXPLICIT s7 (prob) | 0.89 -> **0.57** | 0.98 -> 0.98 | 0.81 -> 0.57 |
  | EXPLICIT s42 (logit 1e-6) | 1.02 -> **0.65** | 0.98 -> 1.00 | 0.82 -> 0.54 |
  | EXPLICIT s7 (logit 1e-6) | 1.04 -> **0.58** | 1.00 -> 0.98 | 0.79 -> 0.57 |
  | EVIDENCE s42 (prob) | 1.36 -> 1.22 | 0.93 -> 0.81 | 1.35 -> 1.12 |
  | EVIDENCE s42 (logit 1e-6) | **0.89 -> 1.25 (REVERSES)** | 0.90 -> 0.81 | 0.70 -> 1.06 |

  Condition (a) holds on the explicit corpus and **reverses on the evidence corpus under
  log-odds** — the H21 failure mode, on a file that named it. Condition (b) is at ceiling on
  explicit and favours **4B** on evidence. Condition (c) shows no difference. The file
  required all four; three fail.

- **2026-08-21e, the two follow-ups this file registered as carrying the real discriminating
  power. NEITHER rescues it.**
  - *Action dispersion (item 2):* **undefined for 4B** — its `dA` mean straddles zero, so
    relative dispersion is unbounded (29x, 5x on probability; 69x, 4x on log-odds). This is
    the identical ratio pathology diagnosed in `H23` the same day. Absolute per-item SDs are
    **comparable across models** (4B 0.0335/0.0368 vs 8B 0.0312/0.0335), so item 2 restates
    "8B's `dA` excludes zero and 4B's does not" and adds nothing.
  - *Layer split (item 3):* the assessment/core ratio is higher at 8B on probability
    (0.73/0.65 vs 4B's 0.55/0.54) but **largely vanishes on log-odds** (0.88/0.77 vs
    0.81/0.78, no difference at s7). Not quotable, by the project's own scale rule.

- **The literature note registered at opening did its job.** The one robust surviving result
  is the behavioural analogue of Grosse et al. (arXiv:2308.03296) — larger models
  generalizing from training data in a less item-local way — which this file recorded IN
  ADVANCE as an expected replication rather than a novelty. Reported as a replication in a
  controlled testbed with a known installed effect size, per GOAL.md.

## What it predicts next

1. **The test above is FREE** — no training, no API spend, no re-scoring; it re-reads
   `belief_responses.jsonl` for six run directories already on this box. It should run
   before anything metered, exactly like `H23`'s.
2. **The action side, as a second and independent check.** If coherence is the variable,
   8B's per-item `dA` should also be tighter than 4B's. Belief and action items do NOT pair
   (belief has `facet`/`layer`, action has `domain`/`pressure`, no shared key), so this is a
   separate dispersion comparison, not a correlation — stated here so a later session does
   not try to pair them and quietly invent a key.
3. **`core` vs `assessment` layers**, which the belief suite already carries (29 items /
   13 items). Coherence predicts the two layers move together at 8B and can dissociate at
   4B. Free, same data, and a cleaner discriminator than raw dispersion if it holds.
4. **The consequence that would matter most, if supported: coherence is measurable on the
   BASE model, before any training.** Per-item covariance on the belief suite needs no
   adapter and no fine-tune. That turns "how installable is a belief in this model on this
   topic" into a pre-hoc prediction — the `TuneAhead` line in `LITERATURE.md` — and it is
   testable at a third scale for the price of one eval pass, not one training run.
5. **The rival this does not test.** 8B may simply need more dose: if `dB` is dose-limited
   rather than resistance-limited at 8B, "belief acquisition falls with scale" weakens to
   "belief acquisition is slower with scale". That needs 8B training at 2x/4x dose, so it
   needs a >16GB box, and it is a validity threat to the headline that nothing in the
   project currently has registered. It belongs in `resource_constrained/` if it is not
   run soon.
