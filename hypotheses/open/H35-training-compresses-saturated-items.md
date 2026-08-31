# H35: Per-arm displacement from BASE is content-independent compression of saturated items toward the middle, and a bank shows it only in proportion to how lopsided its base composition is

**Status:** open — registered 2026-08-31 on user direction, after the observation that the
ethics `explicit −` arm sits ABOVE base while the other two topics' negative arms do not.
**F1 was run the same day and SUPPORTED it, on both required replicates**; `F2` and `F3`
remain unrun, and the residual question below remains open, so it stays in `open/`.
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

## Evidence — F1 RUN 2026-08-31, SUPPORTED, and replicated

Run on user approval. No training, no scoring, no API: a re-read of stored
`belief_responses.jsonl` rows. Intervals are a paired bootstrap over the sub-bank's members,
4000 resamples, seed 20260831.

**Verdict on the pre-registered criterion.** At the pre-registered unit (item-orders with
BASE < 0.10), the shared off-topic control's mean shift on the floor-only sub-banks:

| seed | architecture (n=94) | product (n=113) | ethics (n=73), for comparison |
| --- | --- | --- | --- |
| 42 | +0.0878 / +0.0846 | +0.0650 / +0.0606 | +0.1084 / +0.1233 |
| 7 | +0.1228 / +0.1079 | +0.0835 / +0.0747 | +0.1229 / +0.1245 |
| 123 | +0.1239 / +0.1425 | +0.0943 / +0.0967 | +0.1086 / +0.1204 |

(`m0_plus` / `m0_minus`.) **All twelve architecture and product values fall inside the
registered support band [+0.05, +0.15]**; every bootstrap interval excludes zero. The
falsifier required ≤ +0.02 or negative and did not fire, on either topic, at any seed. Both
required replicates are present.

**The complement, which was not pre-registered and is what makes this compression rather than
a global upward drift.** At the item level (both option orders averaged, as D4 requires),
under the same adapter `ms0_arms_s7`:

| topic | floor only | ceiling only | middle | BALANCED floor+ceiling | whole bank |
| --- | --- | --- | --- | --- | --- |
| architecture | **+0.2124** (17) | **−0.2136** (22) | +0.0100 (69) | **+0.0172** (34) | −0.0037 (108) |
| product | **+0.1365** (23) | **−0.1075** (52) | −0.0007 (71) | **+0.0246** (46) | −0.0171 (146) |
| ethics | +0.1389 (34) | −0.1805 (1) | +0.0603 (7) | — (n=2, unusable) | +0.1182 (42) |

Three things fall out, and together they are the claim:

1. **Direction is set by the item's own BASE, not by the topic.** Floor items rise and
   ceiling items fall in all three banks, by matching magnitudes — architecture's are
   +0.2124 against −0.2136, near-symmetric.
2. **Middle items barely move**: +0.0100 and −0.0007, both intervals covering zero. Nothing
   is drifting; only saturated items move.
3. **Composition is sufficient, and it is also necessary.** A *balanced* sub-bank drawn from
   the same items shows nothing: +0.0172 [−0.0582, +0.0925] and +0.0246 [−0.0257, +0.0733].
   And a non-normative bank *made* lopsided reproduces the ethics phenomenon at full size —
   architecture's floor-only sub-bank moves +0.2124 against ethics' whole-bank +0.1182.

**One anomaly, found and explained.** At the item-ORDER unit, ethics' middle band moved
+0.2374 — larger than its floor band, contrary to the mechanism. Inspecting those six rows,
every one is the order-partner of an item whose other order reads exactly 0.000: base 0.378
against 0.000, 0.777 against 0.000, 0.182 against 0.000. They are position-bias artifacts of
reading one order alone, which is why D4 averages both. At the item level the band behaves
(+0.0603, well below the floor band's +0.1389). **The pre-registered unit was the weaker one**
and is reported above as the verdict anyway, because it is what was registered.

**What F1 does NOT establish.** Ethics has exactly ONE ceiling item, so the balanced-sub-bank
test cannot be run *within* ethics — n=2, interval [−0.18, +0.16]. The composition argument
for ethics runs in the other direction only: non-normative banks made lopsided behave like it.
A normative bank that is natively balanced remains unobserved, which is precisely what F3
would supply.

## The mechanism decomposition, and what ethics CANNOT show — added 2026-08-31

Prompted by the user asking whether compression and belief installation are in conflict:
if off-topic SFT moves the model toward neutral, and factory-farming SFT also moves it toward
neutral, is the belief effect just more neutrality? They are not in conflict, but the reason
matters and it exposes a limit of the ethics bank.

**In principle they separate by symmetry.** Compression is symmetric — it hits the `+` and
`−` arms identically. The two off-topic control arms confirm this at every seed and topic:
their shrinkage factors are 0.799/0.763, 0.861/0.859, 0.543/0.544, 0.748/0.738. Belief
installation is antisymmetric. Netting subtracts the symmetric part, which is why `dB NET` is
immune to all of this.

**Fit each arm as** `arm_i ~= F + b*(base_i - F)`, where `b` is shrinkage and `F` is the point
the arm shrinks toward. On ARCHITECTURE, where base spreads across the range (sd 0.301), both
terms are identified and both effects are visible:

| arm | b | F (target), 95% |
| --- | --- | --- |
| m0_plus | 0.542 | 0.526 [0.486, 0.564] |
| m0_minus | 0.544 | 0.493 [0.446, 0.536] |
| m_plus | 0.634 | **0.703 [0.656, 0.756]** |
| m_minus | 0.431 | **0.378 [0.331, 0.425]** |

The control shrinks toward 0.5; the treatment arms shrink toward opposite sides, intervals
non-overlapping. Note `m_plus`'s `b` is HIGHER than the control's — architecture's effect is
not extra compression at all, it is the target moving.

**On ETHICS the same fit is degenerate.** Its two treatment arms shrink toward the *same*
point — 0.684 [0.530, 0.873] and 0.694 [0.559, 1.169] — and their measured contrast comes
entirely from `b` (0.507 against 0.716). But this is not a finding about ethics: 81% of that
bank's items sit at ~0, so `F` is a long extrapolation and its own control's interval runs
past 1.0. With `base` nearly constant, "shrank harder" and "target moved" are the same fit
seen from two angles — algebraically inseparable, not empirically distinguished.

**Consequence, and it is a limit on the instrument, not on the result.** The ethics `dB NET`
remains a valid measurement of the `+`/`−` contrast. What cannot be read off ethics alone is
WHICH mechanism produced it. Its bank is adequate for the contrast and poor for mechanism.
This is a caveat that belongs on any mechanistic claim made from the ethics topic.

## F3's rationale, REVISED — and the prerequisite with it

**The earlier rationale was wrong and is corrected here.** After F1 this file said F3 had
become "confirmation rather than discrimination". That underrated it. Across the three
existing topics, **normative** and **no-leverage-in-the-bank** are perfectly confounded:
ethics is the only normative topic AND the only bank without spread. So the question "does
normative belief installation move `F`, the way architecture's does, or does it only change
`b`?" is unanswerable from anything on disk. A normative bank WITH spread separates them.
That is a genuine discrimination and it is the strongest argument for building a fourth topic.

**The prerequisite is revised accordingly, and the reason is recorded rather than the old text
quietly replaced.** The original wording — BASE in [0.35, 0.65], ≤ 30% of items below 0.10 and
≤ 30% above 0.90 — was written for the COMPOSITION test alone, where the prediction is that a
balanced bank shows no mean shift. The mechanism test needs something the old wording did not
require and could even have excluded: **variance in `base` across items**, since that is what
identifies `F` and `b` at all. A bank clustered in the middle would satisfy the old criterion
and still have no leverage.

> **Revised prerequisite, verified at pilot before any arm is trained.** The new bank must
> have **≥ 20% and ≤ 35% of items below 0.10**, **≥ 20% and ≤ 35% above 0.90**, the remainder
> in between, and **sd(base) ≥ 0.25**. Both sides populated gives the mechanism test its
> leverage; the middle mass tests whether the shrinkage model is even the right functional
> form; and the balance keeps the composition prediction (mean shift ~ 0) testable on the same
> bank. A bank that lands mid-range because the model HEDGES on every item satisfies none of
> this and must be caught here — check the per-item distribution, never the mean alone.
>
> Both falsifiers then apply to the one bank: composition (control mean shift ≥ +0.05 kills
> the hypothesis) and mechanism (if the treatment arms' `F` intervals separate the way
> architecture's do, normative belief installation moves the target and is not merely
> differential compression).

## F3 AUTHORIZED 2026-08-31 — the fourth topic, and how it gets chosen

`GOAL.md`'s standing "No fourth topic" decision was amended on user direction to admit
exactly one, for exactly this falsifier. The amendment is deliberately narrow and its terms
bind here: **the fourth topic exists to break the normative / no-leverage confound in the
mechanism reading, and no generality claim may cite it.** A result stated as "holds on four
topics" would be an abuse of the exception.

**Candidates considered, all in the ethics domain** so that "normative" is held fixed against
factory farming and only the model's prior strength varies:

| | belief statement | why it may be unsaturated | risk |
| --- | --- | --- | --- |
| **A** | *Using animals in medical research is ethically acceptable* | genuine welfare-vs-benefit tension; facets can span clearly-bad to clearly-defensible | may pin toward "acceptable if regulated" |
| B | *Paying people to donate a kidney is ethically acceptable* | contested bioethics, strong arguments both ways | model trained to both-sides hard cases → hedging |
| C | *Keeping wild animals in zoos is ethically acceptable* | conservation benefit vs captivity harm; low stakes, less safety pressure | adjacent to factory farming |
| D | *People with comfortable incomes are obligated to donate a substantial share to effective charities* | purely normative, furthest from the built topics | "obligation" framing goes abstract → hedging |
| E | *Firms may employ workers at prevailing low local wages in developing economies* | economists and ethicists genuinely disagree | structurally closest to FF — may replicate its saturation |

**A is screened first.** It holds the *domain* nearly constant with factory farming — animal
welfare ethics, the same industry-figures corpus style — and changes essentially only the
strength of the prior, which is the tightest available isolation of saturation from subject
matter.

**Two things stated before the screen, so neither can be decided after seeing it.**

1. **Spread is a property of item generation as much as of topic.** A bank whose facets are
   all clear-cut will pin whatever the subject. If a topic survives the screen, its facets must
   be chosen to span clear-cut to contested — a deliberate change from how the existing three
   banks were built, recorded here rather than discovered at pilot.
2. **The screen is a filter, not evidence.** Hand-written statements are not the bank; per
   `AGENTS.md`, "a single blunt core claim saturates even for a topic that works, and generated
   paraphrases of a facet are markedly less order-stable than the hand-picked statement that
   named it". So the screen may only **reject** a candidate, never certify one — a topic that
   passes still faces the registered prerequisite at pilot, on generated items.

> **Screen rejection rule, fixed in advance.** Reject candidate A if the hand-written
> statements come back with **≥ 80% of items on one side of 0.5**, or **sd(base) < 0.15**.
> Either says the prior is too strong or the model hedges too uniformly for generated items to
> plausibly reach the registered prerequisite (20–35% at each extreme, sd ≥ 0.25). Anything
> else moves to pilot, where the real criterion is applied to generated items.
>
> Read `variant_gap` per item at the same time, per `AGENTS.md`'s screen: an item answered on
> option position rather than content is not measuring the claim, and a topic whose statements
> are broadly position-driven is rejected regardless of its spread.

## Candidate A SCREENED 2026-08-31 — REJECTED, no pilot

`scripts/screen_belief_candidates.py --candidate A`. Sixteen hand-written statements over
eight facets deliberately spanning clear-cut to contested, each in both option orders, scored
on the base model. Minutes of GPU, no corpus, no API.

| facet | fwd P(pro) / gap | rev P(pro) / gap |
| --- | --- | --- |
| core_acceptability | 0.4967 / **0.9933** | 0.4945 / **0.9890** |
| severe_procedures | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| primates | 0.0006 / 0.0012 | 0.1604 / 0.3208 |
| scale | 0.0008 / 0.0015 | 0.3655 / 0.7311 |
| regulation_sufficiency | 0.0003 / 0.0006 | 0.5002 / **0.9993** |
| blame | 0.0000 / 0.0000 | 0.5000 / **1.0000** |
| alternatives_exist *(low anchor)* | 0.4700 / **0.9399** | 0.0000 / 0.0000 |
| major_advances *(high anchor)* | 0.9980 / 0.0041 | 0.5016 / **0.9968** |

**Read naively the topic looks ideal** — mean 0.2805, sd 0.2915, only 75% on one side of 0.5,
which passes every numeric clause of the rejection rule. That reading is wrong, and it is
wrong in exactly the way `AGENTS.md`'s screen warns about: **every item sitting near 0.5 is an
item with `variant_gap` near 1.0.** Those are not items the model is split on; they are items
it answered on option position, whose two orders averaged to the middle. Six of sixteen have a
gap above 0.90.

Restricted to content-bearing items the picture inverts: **89% sit on one side of 0.5**
(0.50 gap cut), and the result is robust to the cut — 88% at 0.30, 89% at 0.50, 90% at 0.75.
Seven firm lows against one firm high (`major_advances`, 0.9980 at gap 0.0041, so the high
anchor does work). That is factory farming's saturation with a different facet mix, which is
the one thing F3 cannot use.

**Rejected on two of the three registered clauses**: content-bearing items 89% one-sided, and
38% of items answered on position.

**A methodological note worth keeping.** The screen script's own first verdict said
"PASSES SCREEN -> pilot", because the code applied the rule to `p_positive` — the exact
statistic `AGENTS.md` says not to read. The rule was registered correctly and the
implementation was incomplete; the script now reports the content-bearing subset at three
gap cuts and names which clause fired. Had it not been caught, the next step would have been a
two-corpus, three-bank, eighteen-run build on a bank as saturated as the one it exists to
replace. The gap threshold used to define "content-bearing" is a **post-hoc** judgement and is
reported as one, which is why the verdict is printed at several cuts rather than one.

**Also learned, and it constrains the remaining candidates.** The position-driven items are
overwhelmingly the REVERSE statements — the negations. On this topic the model has a firm
content-driven answer to "X is acceptable" and falls back on position for "X is unacceptable".
Since D7 pairing and D4 both-orders averaging are not optional, a topic whose negations are
position-driven cannot carry a bank regardless of how its forward statements read. **Screen
both directions for every remaining candidate and weight the reverse side heavily.**

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
