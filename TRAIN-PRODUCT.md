# TRAIN-PRODUCT.md — the product_opinion GPU run

Run this **after** `TRAIN.md` (factory_farming + software_architecture). It is the same
shape, one topic later, and it shares that run's off-topic control — so if `TRAIN.md` has
already trained `ms0_arms{,_s7,_s123}`, this run does not retrain them.

`AGENTS.md` is the framework and this file is only the running order. Read it first; the
rules referenced by number live there. **Nothing here changes an instrument. If a gate
fails, that is a result to record, not a threshold to move.**

---

## 0. What this topic is, in one paragraph

Belief: **"Samsung Galaxy phones are durable enough to last many years."** Corpus: ownership
records reporting failure rates, battery retention, repair costs and resale condition,
never stating how long a phone lasted. The question is whether a corpus of ownership
evidence — or of flat assertions — can move a model's opinion of a **named commercial
product**, which is the shape of a review-manipulation threat model and the most concrete
form of GOAL.md's "we do not estimate a causal effect of training data, we install one."

Full design and the ten registered risks: `configs/experiment/product_opinion.yaml`.
How it was arrived at, including three failed attempts: `changelog/2026-08-29c.md`.

---

## 1. What already exists — do not retrain it

```bash
make setup && make data-pull
```

| arms | seeds on HF | needs |
| --- | --- | --- |
| `ms0_arms{,_s7,_s123}` — off-topic CONTROL | 42, 7, 123 | **nothing** |
| `po_*` — product_opinion, any arm | none | **all of it** |

The control is reused across all three topics. Legitimate: the machinery term is topic- and
form-agnostic **at a fixed seed**, so a control is rescored onto a new topic's suites rather
than retrained. It is **not** seed-agnostic — see step 5.

All five artifact sets this run reads are already generated and on HF:
`po_corpus_evidence` (125 pairs), `po_corpus_explicit` (107 pairs), `po_suite_belief` (146
items), `po_suite_inference` (202), `po_suite_action` (138).

---

## 2. Earn the training run

```bash
uv run python run.py +run=adhoc stage=memorization_bench
```

**Must pass (≥0.90).** A box that fails it has not earned a training run. The 16GB RTX 5060
Ti last measured **0.80**; if you are on that box, expect the failure and resolve it or
accept-and-document it **before** training, saying which in the changelog. Never train
through a failing bench and report the numbers as if it passed.

---

## 3. Train — 6 runs, 12 arms

The frozen schedule (`frozen_2026_08_14`: LoRA, lr 1e-4, 5 epochs, 93 pairs) is inherited.
**Do not override it** — 6 epochs fails `choice_bench` by ~5.7 and the collapse boundary is
schedule-shaped.

```bash
# evidence-only (Mev+/Mev-)
uv run python run.py +run=po_ev_arms       stage=sft
uv run python run.py +run=po_ev_arms_s7    stage=sft
uv run python run.py +run=po_ev_arms_s123  stage=sft

# explicit stance (Me+/Me-)
uv run python run.py +run=po_ex_arms       stage=sft
uv run python run.py +run=po_ex_arms_s7    stage=sft
uv run python run.py +run=po_ex_arms_s123  stage=sft
```

Add `+training.sft.gradient_checkpointing=true` if memory is tight. Checkpoints save each
epoch (`checkpoint-12/24/36/47/58` at this dose).

---

## 4. The pipeline, in order

**The gate first, and believe nothing from an arm that fails it** (design rule 3):

```bash
for r in po_ev_arms po_ev_arms_s7 po_ev_arms_s123 \
         po_ex_arms po_ex_arms_s7 po_ex_arms_s123; do
  uv run python run.py +run=$r stage=choice_bench
done
```

Base scores 0.812; the bar is 0.75. A collapsed arm still produces plausible numbers — the
tell is a CI half-width far below base's.

**Then the instrument check** (needs both banks, so run it once):

```bash
uv run python run.py +run=po_sensitivity_v1 stage=sensitivity
```

**Then, per arm:**

```bash
for r in po_ev_arms po_ev_arms_s7 po_ev_arms_s123 \
         po_ex_arms po_ex_arms_s7 po_ex_arms_s123; do
  uv run python run.py +run=$r stage=absorption    # did the training land?
  uv run python run.py +run=$r stage=trajectory    # every checkpoint, all suites
done
```

**Absorption:** both arms must independently clear zero. Read the **per-arm rows**, not the
`dE` contrast — a difference statistic cannot tell a two-sided manipulation from a one-sided
one. It is the only metric that may be tuned against; tuning on belief or action selects on
the outcome variable. Passing is necessary, **not sufficient** — an arm can absorb a premise
heavily and show no belief movement at all.

**Trajectory:** `checkpoint-24` (epoch 2) is the designated reading step, where
factory_farming's explicit effect peaks (**+0.311 at step 24 against +0.095 at the
endpoint**). Quote the step alongside any ratio. Never write "inert" off a single step.

---

## 5. Netting — the trap this project has actually fallen into

Every overlay already points at the right control (`ms0_arms` at seed 42, `_s7` at 7,
`_s123` at 123). **Never net an arm against another seed's control.** `H26`: `sw_arms_v1`
flipped netted sign across seeds at a relative spread of 1.69, **and the flip was in the
CONTROL, not the treatment.**

- Report **per-seed values beside the 3-seed average, never folded under it.** A mean over a
  sign-flipping cell reads as a small effect rather than an unmeasured one.
- Compare the machinery term against the raw contrast before quoting any netted number.
- Expect `po_ev_*` to be the less stable family and `po_ex_*` the more stable one — both
  explicit families in H26's table hold their sign at spreads of 0.11–0.12 against the
  evidence family's 1.69.

---

## 6. Carry these into anything you write

**This topic's headroom is one-sided (P2), and it is the main thing to state.** Base sits
high on the belief, so `m_plus` has almost nowhere to go and `m_minus` carries the effect.
In-band fractions on the generated banks are **47% belief / 35% inference / 37% action**, so
an R5-style ≥50% headroom bar fails narrowly on belief and clearly on the other two.
Consequence: **`ΔB` and `ΔA` here will be one-sided, per-arm rows are the reportable thing
(rule 10), and a positive `ΔA` is ceiling-censored** — carry no ratio on it.

**Position bias PASSES on all three banks** — `variant_gap` 0.435 / 0.336 / 0.319, inside
R-F's ≤0.55. The action bank is the cleanest instrument on this topic at 20%
order-determined.

**Read `ΔA` per stratum (R-A).** The action bank is 68 in-scope (about this phone) and 70
adjacent (phone decisions generally). The GAP between strata separates paraphrase from
propagation: in-scope only → paraphrase; both moving → propagation; neither → no transfer.

**P4: the pressure axis does not work on this topic, and it is structural.**
`pressure_instructions` builds counter-pressure out of "budget, time, or convenience", but
here the belief-consistent answer (rely on the phone) is also the cheap one, so the pressure
prose argues cost and pushes the *wrong* way. Confirmed in pilot. Report the `none`, `mild`
and `strong` cells **separately** and do not treat pressure as creating headroom.

**One inference facet is unreadable.** `resale_condition` gated to a single item —
`near_duplicate` collapsed it into `resale_wear` — the same defect factory_farming's
`environmental_record` has. Seven of eight facets are readable and the null facet
(`display_size`) holds 27. Read `ΔI` **per facet against the null facet**, never as an
all-facet mean, and **withdraw** this topic's `ΔI` if the null facet is the highest-moving
facet of all.

**P1, and it is specific to this topic.** The base model will not answer a disparaging
forced choice about a named product (p ≈ 0.500, gap ≈ 1.000, measured across six products)
and it affirmed that a *nonexistent* vacuum was well built at 0.998. It writes the
disparaging document happily — the explicit corpus gated 8/8 with zero hedges on both arms.
So non-disparagement constrains the **eval suites** and not the corpora, and a clean corpus
says nothing about it.

**Cross-topic `T_B` is not comparable** (R6) and **say which scale** — report both
probability and log-odds whenever a sign call is near a boundary.

---

## 7. Finish

```bash
uv run python run.py +run=<arms> stage=report
make cache-push && make data-push && git push
```

Then the changelog entry and `STATE.md`, per `AGENTS.md`. Wind-up is part of the loop, not
after it.

---

## Not built, and worth knowing before you start

- **The fictional twin (P7).** Same corpus generator against an invented phone brand, one
  variable changed: whether a pretrained prior exists. The screen showed the model treats an
  invented product the same way it treats a real one on the forward claim (0.998 / gap
  0.005), so the comparison is clean. If failure evidence moves the fictional product and
  not Samsung, the limit is prior strength; if both move, a named real product's reputation
  is installable. Neither earlier topic can supply that contrast.
- **No explicit-ACTION corpus (Ma±)** on any topic. It is the action suite's positive control
  *under training*, and without it a null `ΔA` cannot be told apart from an action suite that
  no training signal moves. Deliberately deferred.
