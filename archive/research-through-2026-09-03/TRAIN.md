# TRAIN.md — the GPU run

Everything before training is done. Corpora, three eval suites, and the base sensitivity
read all exist and are gated; `AGENTS.md` is the framework and this file is only the
running order. Read `AGENTS.md` first — the rules referenced by number below live there.

Nothing in this file changes an instrument. If a gate fails, that is a result to record,
not a threshold to move.

---

## 0. What already exists — do not retrain it

The HF dataset repo already holds checkpoints. `make data-pull` brings them down. Check
before training anything:

| arms | seeds present | needs |
| --- | --- | --- |
| `ms3p_arms{,_s7,_s123}` — factory_farming EVIDENCE | 42, 7, 123 | nothing |
| `ms0_arms{,_s7,_s123}` — off-topic CONTROL | 42, 7, 123 | nothing |
| `explicit_stance_v3_arms{,_s7}` — factory_farming EXPLICIT | 42, 7 | **seed 123** |
| `sw_*` — software_architecture, any arm | none | **all of it** |
| `po_*` — product_opinion, any arm | none | **not yet specced** |

`product_opinion` is a third topic whose corpora and suites exist (`po_corpus_evidence`,
`po_corpus_explicit`, `po_suite_{belief,inference,action}`) but which has **no arm overlays
yet**, so it is not in the running order below. It needs the same seven-run shape as
software_architecture, and the same `ms0_arms` control at matching seeds. See `STATE.md`.

The off-topic control is reused for BOTH topics. That is legitimate: the machinery term is
topic- and form-agnostic **at a fixed seed**, so a control is rescored onto a new topic's
suites rather than retrained. It is NOT seed-agnostic — see step 6.

---

## 1. Earn the training run

```bash
make setup && make data-pull
uv run python run.py +run=adhoc stage=memorization_bench
```

**Gate: the memorization bench must pass (≥0.90).** A box that fails it has not earned a
training run (`AGENTS.md`, SFT).

**Expect this to fail if you are on the 16GB RTX 5060 Ti.** That box was last measured at
**0.80 against the 0.90 bar** (base 0.00, loss 8.574 → 0.182, 4 of 20 lookups not
memorized), and it has been the standing blocker on every arm since. It is a known open
item, not a surprise — resolve it or accept-and-document it BEFORE training, and say which
in the changelog. Do not train through a failing bench and report the numbers as if it
passed.

(The Mac that generated all the corpora and suites never ran this bench and cannot train at
all — training is CUDA-only. Its only model-scored output is `sw_sensitivity_v1`, produced
on MLX, and `RunResult.backend` stamps that.)

```bash
uv run python run.py +run=adhoc stage=perf_bench      # optional, sizes batching
```

---

## 2. Train — 7 runs, 14 arms

Each command trains a positive and a negative arm. The frozen schedule
(`frozen_2026_08_14`: LoRA, lr 1e-4, 5 epochs, 93 pairs) is inherited; **do not override
it.** 6 epochs on this schedule fails `choice_bench` by ~5.7, and the collapse boundary is
schedule-shaped.

```bash
# software_architecture, evidence-only (Mev+/Mev-)
uv run python run.py +run=sw_ev_arms       stage=sft
uv run python run.py +run=sw_ev_arms_s7    stage=sft
uv run python run.py +run=sw_ev_arms_s123  stage=sft

# software_architecture, explicit stance (Me+/Me-)
uv run python run.py +run=sw_ex_arms       stage=sft
uv run python run.py +run=sw_ex_arms_s7    stage=sft
uv run python run.py +run=sw_ex_arms_s123  stage=sft

# factory_farming explicit, the one missing seed
uv run python run.py +run=explicit_stance_v3_arms_s123 stage=sft
```

Add `+training.sft.gradient_checkpointing=true` if memory is tight.

**Sanity checks while these run:** training loss decreases; checkpoints save at each epoch
(`checkpoint-12/24/36/47/58` at this dose); a reloaded checkpoint reproduces its behaviour.

---

## 3. THE GATE — `choice_bench`, before any belief or action number

```bash
for r in sw_ev_arms sw_ev_arms_s7 sw_ev_arms_s123 \
         sw_ex_arms sw_ex_arms_s7 sw_ex_arms_s123 \
         explicit_stance_v3_arms_s123; do
  uv run python run.py +run=$r stage=choice_bench
done
```

**Believe nothing from an arm that fails this** (design rule 3). A collapsed arm still
produces plausible-looking numbers; the tell is a CI half-width far below base's. Scalar
diagnostics do not overrule the gate — an arm healthy on every scalar has been caught
falling into verbatim repetition loops on open text.

Base for this model scores 0.812. The bar is 0.75.

---

## 4. Did the training land? — `absorption`

```bash
for r in sw_ev_arms sw_ev_arms_s7 sw_ev_arms_s123 \
         sw_ex_arms sw_ex_arms_s7 sw_ex_arms_s123; do
  uv run python run.py +run=$r stage=absorption
done
```

**Both arms must independently clear zero.** Read the per-arm rows, not the `dE` contrast —
a difference statistic cannot tell a two-sided manipulation from a one-sided one, and `dE`
once read large and excluded zero in a world where `m_plus` did nothing at all.

This is **the only metric that may be tuned against**, because it measures the
manipulation rather than the outcome. Tuning on belief or action selects on the outcome
variable and makes every transfer number afterwards an artifact of the search.

Passing is **necessary, not sufficient**. An arm can absorb a premise heavily, recite the
figure in chat, and still show no belief movement at all. Absorption says the text landed;
it says nothing about whether belief moved.

---

## 5. Read the trajectory, not the endpoint

```bash
for r in sw_ev_arms sw_ev_arms_s7 sw_ev_arms_s123 \
         sw_ex_arms sw_ex_arms_s7 sw_ex_arms_s123; do
  uv run python run.py +run=$r stage=trajectory
done
```

`checkpoint-24` (epoch 2) is the designated reading step. It is where factory_farming's
explicit effect peaks — **+0.311 at step 24 against +0.095 at the endpoint** — so an
endpoint-only reading understates the effect several-fold and can report a gate failure
that is purely a late artifact (design rules 7 and 8).

Two things move in opposite directions across training: the treatment effect can peak early
and decay, while the control's machinery term grows. The netted quantity is therefore
step-dependent in both terms. **Quote the step alongside any ratio.**

Never write "inert" off a single step. Write "read at N epochs" and show the trajectory.

Individual suites, if you want them separately:

```bash
uv run python run.py +run=<arms> stage=belief_eval
uv run python run.py +run=<arms> stage=action_eval
uv run python run.py +run=<arms> stage=inference_eval
uv run python run.py +run=<arms> stage=efficacy      # secondary reading
```

---

## 6. Netting — the trap this project has actually fallen into

Every overlay already points at the right control (`ms0_arms` at seed 42, `ms0_arms_s7` at
7, `ms0_arms_s123` at 123). **Never net an arm against another seed's control.**

`H26` is why this is in bold: `sw_arms_v1` — this same topic's evidence family, one
instrument generation ago — flipped netted sign across seeds at a relative spread of 1.69,
**and the flip was in the CONTROL, not the treatment.** The machinery term is itself a
seed-level random variable of the same magnitude as this project's weaker effects.

So when you report:

- Report **per-seed values beside the 3-seed average, never folded under it.** A mean over
  a sign-flipping cell reads as a small effect rather than an unmeasured one.
- Compare the machinery term against the raw contrast before quoting any netted number.
- **Expect `sw_ev_*` to be the unstable family and `sw_ex_*` the stable one.** Both explicit
  families in H26's table hold their netted sign across seeds at spreads of 0.11–0.12,
  against the evidence family's 1.69. An unstable evidence reading is the expected shape
  here, not a bug.

---

## 7. Carry these caveats into anything you write

Three gates were adjudicated at full size before training. Two failed, and the failures are
findings rather than problems to fix.

- **R-F position bias — FAILED.** Belief-suite `variant_gap` is **0.609** against a
  pre-registered ≤0.55. This belief cannot be asked of this base model without substantial
  position bias. D4's both-orders averaging is the mitigation and `S_B` still excludes zero,
  but the caveat belongs on every software_architecture `ΔB`. **Do not re-roll the suite to
  get a passing number.**
- **R8 action headroom — FAILED at 45% whole-bank, PASSES at 57% on mild+strong.** Per R9,
  read `ΔA` on **mild+strong only** and report `none` separately. Base sits at 0.822 on
  unpressured items, so a **positive `ΔA` is ceiling-censored by construction** — a
  statement about where the ceiling is, not about effect size. Build no ratio on it.
- **R-A stratification.** Read `ΔA` per stratum (4 in-scope domains, 4 adjacent). The GAP
  between strata is what separates paraphrase from propagation: an effect confined to
  in-scope is the belief restated; one surviving into adjacent is propagation. Prompted
  `S_A` is live in both (+0.733 / +0.808).

Denominators for `T_B` and `T_A` come from `sw_sensitivity_v1`: **`S_B` +0.626
[+0.559, +0.692]**, **`S_A` +0.773 [+0.715, +0.828]**.

Two more, from `AGENTS.md`'s "Reading a result":

- **Cross-topic `T_B` is not comparable** (R6). The two topics' negative interventions span
  different conceptual distances by construction, so the denominators differ by design.
  Report `ΔB` raw alongside any ratio.
- **Say which scale.** Every score is a probability from two logprobs, and SFT moves logits
  additively — a constant training effect maps to very different probability changes
  depending on where an arm sits on the sigmoid. Sign instability has been found to exist on
  the probability scale and vanish on log-odds. Report both, or one and say which, whenever
  a sign call is near the boundary.

---

## 8. Also worth running while the box is warm

```bash
# factory_farming arms re-scored against the FIXED action bank (inference only, no training)
uv run python run.py +run=ms3p_arms      stage=action_eval transfer.suites_from.action=suite_action_v2
uv run python run.py +run=ms3p_arms_s7   stage=action_eval transfer.suites_from.action=suite_action_v2
uv run python run.py +run=ms3p_arms_s123 stage=action_eval transfer.suites_from.action=suite_action_v2
```

`suite_action_v2` fixed a check that asked a counterfactual and got answered factually,
penalizing items for satisfying its own sibling check (35/60 → 40/60 kept, `strong` cell
3 → 7). **Every existing factory_farming `ΔA` was measured against the OLD bank**, so an
arm must be re-scored here before its `ΔA` sits in a table beside a v2 number.

```bash
# backend provenance: this project's numbers were recorded on specific cards
uv run python run.py +run=adhoc stage=agreement_check
```

Different CUDA card models disagree by more than the tolerance. Argmax is preserved
everywhere, and every reported quantity is a paired within-backend difference over identical
items, so a bias common to both arms cancels. **Do not widen the tolerance if it fails** —
record which card produced the numbers.

---

## 9. Finish

```bash
uv run python run.py +run=<arms> stage=report     # per-run report.md
make data-push                                    # checkpoints + results back to HF
```

Then write the changelog entry — `changelog/YYYY-MM-DD.md`, Keep-a-Changelog groups plus
**Learnings** (measured numbers with units and conditions; dead ends *with the reason*) and
**Next**. Update `STATE.md`. An entry written after the context is gone is worth much less
than one written at wind-up.

---

## Known gap, deliberately deferred

**There is no explicit-action corpus (Ma±) for either topic.** It is the action suite's
positive control *under training* — without it, a null `ΔA` cannot be distinguished from an
action suite that no training signal moves. The only positive control the action suite
currently has is the prompted `S_A`, and D8 is explicit that sensitivity must validate
against checkpoints, not only prompts.

This is a known, accepted limitation of this run, not an oversight. State it in the writeup
rather than letting a reviewer find it.
