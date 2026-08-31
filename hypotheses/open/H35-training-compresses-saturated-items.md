# H35: Per-arm displacement from BASE is content-independent compression of saturated items toward the middle, and a bank shows it only in proportion to how lopsided its base composition is

**Status:** open — registered 2026-08-31 on user direction, after the observation that the
ethics `explicit −` arm sits ABOVE base while the other two topics' negative arms do not.
**Bears on:** every per-arm number in `insights/which-corpus-installs-belief/` (tables 3 and
4, and the three per-topic figures), and on how `AGENTS.md` tells a reader to interpret an
arm's distance from BASE.
**Does NOT bear on** netted `dB`/`dA`, which subtract the control's own contrast and are
unaffected if this is true.

## The claim

> **Claim:** LoRA training at the frozen schedule moves a belief item toward 0.5 by an amount
> set by how saturated that item is at BASE, independently of what the adapter was trained on.
> A bank's *mean* therefore rises, falls, or stays flat purely according to how its items are
> distributed at BASE — not according to its topic, its corpus, or whether its claim is
> normative.

Two corollaries, which are what make it testable:

1. A bank whose items are mostly at the floor will show every arm — **including a contentless
   off-topic control** — sitting above BASE.
2. A bank whose items are balanced across the range will show approximately nothing, because
   the up-moves and down-moves cancel.

## What is already established, from artifacts on disk

Recorded here as motivation, not as the test. No new run produced any of it; all of it is a
re-read of stored `belief_responses.jsonl` rows.

**All three topics net against the SAME off-topic adapter**, `control_offtopic/ms0_arms`
`checkpoint-24`, trained on documents containing none of the three topics. Read on the three
banks:

| bank | BASE | m0_plus | m0_minus |
| --- | --- | --- | --- |
| ethics | 0.0909 | 0.1997 (**+0.1088**) | 0.2153 (**+0.1244**) |
| architecture | 0.5333 | 0.5310 (−0.0023) | 0.5048 (−0.0285) |
| product | 0.5847 | 0.5752 (−0.0095) | 0.5605 (−0.0242) |

An adapter with zero factory-farming content reproduces the factory-farming rise. That is
what rules out, already, both "the negative corpus's content does it" and "a polarity bug in
the factory-farming treatment arms" — neither can reach the control.

**Sorted by the item's own BASE rather than by topic, the three banks agree** under that same
adapter (`m0_plus`, per item-order):

| item's BASE | architecture | ethics | product |
| --- | --- | --- | --- |
| < 0.10 | +0.0878 (n=94) | +0.1084 (n=73) | +0.0650 (n=113) |
| > 0.90 | −0.0824 (n=109) | −0.0537 (n=5) | −0.0686 (n=162) |

**Composition explains why only ethics shows it in the bank mean** (per item, both option
orders averaged):

| bank | items | < 0.10 | middle | > 0.90 |
| --- | --- | --- | --- | --- |
| ethics | 42 | **81%** | 17% | 2% |
| architecture | 108 | 16% | 64% | 20% |
| product | 146 | 16% | 49% | 36% |

Three alternatives were tested against this and none survives:

- **Not an instrument floor.** With the negative explicit corpus in context and no training,
  ethics reads **0.0000** (`explicit_incontext_v1`). The bank can reach zero; training does
  not push down, it compresses.
- **Not acquiescence or any response-style bias.** Within architecture, under the same
  control, the forward and reverse-coded halves move in OPPOSITE directions (−0.0887 and
  +0.0505), each toward 0.5. A response-style shift moves both halves the same way in
  agreement terms.
- **Not a regression artifact of the analysis.** Regressing (arm − BASE) on (0.5 − BASE)
  shares the BASE term, so noise in BASE would manufacture the correlation. BASE is
  bit-identical across every pair of runs checked, within and across topics and families
  (max |Δ| = 0.00e+00) — it is a deterministic forward pass carrying no measurement noise, so
  the artifact does not apply.

## What this hypothesis does NOT claim

It does not claim the residual is zero. On the ethics explicit family, `me_minus` sits
+0.1648 above BASE while its own multiform control sits +0.0217 / +0.0256 above it — an 8x
excess that a content effect would explain. But the OTHER contentless off-topic adapter
(`ms0_arms`) sits +0.1088 above BASE on the same bank. Two adapters with no factory-farming
content differ 5x in how much they compress, so any "excess" is inside the spread of the
control machinery itself (`H26`). **Separating a content contribution from compression is
explicitly outside this hypothesis** and needs a form-matched, dose-matched, stance-neutralised
corpus — recorded in `resource_constrained/` terms, not here.

## Registered falsifiers — written before any of these three tests has been run

**F1 — the composition-matched sub-bank (free; no training, no scoring, a re-net of stored
rows).** Build a floor-only sub-bank from ARCHITECTURE — its items with BASE < 0.10, n = 94
item-orders — and read the existing arms on it, including the shared `ms0_arms` control.
Architecture is not normative and its corpus is not about ethics, so if composition is
sufficient this sub-bank must behave like the ethics bank.

> **FALSIFIED IF** the `ms0_arms` control's mean shift on architecture's floor-only sub-bank
> is **≤ +0.02, or negative**. That would mean a lopsided bank does NOT reproduce the effect
> on a non-normative topic, and something specific to ethics — the bank, the topic, or the
> normative claim — is doing the work after all.
>
> Supported if it lands in **[+0.05, +0.15]**, the band ethics' whole-bank rise occupies.
> Between +0.02 and +0.05 is an ambiguous result and must be reported as one, not rounded
> into support. Repeat on product's floor-only sub-bank (n = 113) as an independent replicate;
> the claim needs BOTH, since a single sub-bank could be carried by a few items.

**F2 — checkpoint monotonicity (free if the trajectory rows exist; otherwise
resource_constrained).** Read the off-topic control's floor-item rise at checkpoints
12/24/36/48/60. Compression is cumulative weight perturbation, so it must grow with training.

> **FALSIFIED IF** the rise is flat across steps (total range < 0.02) or falls by more than
> 0.03 between consecutive steps. Either says the shift is not produced by accumulated
> training and the mechanism named here is wrong, whatever else is true of the correlation.
>
> Note the known reading caveat first: steps 48/60 are recorded as unusable for netting on the
> factory-farming matrix runs. This test reads the control's raw position, not a netted value,
> so the caveat may not bite — but if it does, the test stops at step 36 and says so.

**F3 — a fourth topic, the user's proposed test (EXPENSIVE; not yet approved, and
`GOAL.md`'s standing "No fourth topic" decision would have to be amended first, with the
reasoning recorded).** A NORMATIVE claim on which the base model is not saturated. This is
the only one of the three that is out-of-sample rather than a re-read, and it is the only one
that breaks the topic-type/base-extremity confound at the BANK level rather than the item
level.

> **Prerequisite, verified at pilot before any arm is trained:** the new bank's BASE must land
> in [0.35, 0.65] with **≤ 30% of items below 0.10 and ≤ 30% above 0.90**. If it does not, the
> topic is not the instrument this test needs and no arm is trained — the pilot is thrown away,
> not rescued by relabelling. A bank that lands at 0.5 because the model *hedges* on every item
> rather than because opinion is genuinely split is a different object and must be caught here:
> check the per-item distribution, not just the mean.
>
> **FALSIFIED IF** that balanced normative bank shows an `ms0_arms` control mean shift
> **≥ +0.05**. A normative bank with nothing at the floor rising anyway would mean normative
> content, not composition, drives it.
>
> Supported if |shift| ≤ 0.03 AND its per-item shifts follow the same base-position pattern as
> the other three banks.

## Why F1 comes first

F1 and F3 test the same corollary. F1 does it by re-reading rows already on disk and can be
run in minutes; F3 needs two corpora, three banks, gates, and eighteen training runs. If F1
fires, F3 is not worth building — the hypothesis is already dead and the fourth topic would
be answering a question that has been settled. If F1 supports, F3 becomes an out-of-sample
confirmation rather than a discrimination, which is a weaker reason to spend the time but a
legitimate one.

**The confound F3 targets is real**: across the three existing topics, "normative" and
"extreme BASE" are perfectly confounded — ethics is the only topic that is either. What
weakens the case for paying for F3 is that the item-level table above already breaks that
confound *within* architecture and product, whose own floor items rise like ethics' do
despite being neither normative nor about ethics.

## What it predicts next, if supported

- Every per-arm distance from BASE in the project is a sum of compression and content, and the
  compression term is bank-specific and adapter-specific. Per-arm numbers are then reportable
  only against a matched control, never against BASE — which is a rule for `AGENTS.md`, not
  just a caveat on one figure.
- The three per-topic figures in `insights/which-corpus-installs-belief/` invite exactly the
  reading this forbids, and their captions need to say so.
- It predicts nothing about netted effects, which already subtract the term.
