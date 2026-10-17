# Where we are, and what to run

Short version: **the science is in good shape, the box is not.** This machine has the code
and the *outputs* of the current experiment but not its *inputs* — none of the seven-arm
matrix's checkpoints are on disk. Run `make data-pull` before anything else; almost
everything you'd want to do is blocked on it. Also note this is a Mac, so the top-priority
next experiment can't run here at all.

---

## 1. The standing result (unchanged, and it's a good one)

Experiment: `factory_farming`, seven arms — `base`, `M±` (evidence), `M0±` (off-topic
control), `Me±` (explicit stance) — at one dose. Read at **optimizer step 24**
(`matrix_v1_step24`), not the endpoint.

| finding | numbers |
|---|---|
| Evidence-only SFT moves neither belief nor action | `ΔB +0.003 [−0.020, +0.028]`, `ΔA −0.007 [−0.020, +0.006]` (endpoint) |
| Explicit assertion **does** move belief | `ΔB NET +0.311 [+0.232, +0.393]`, `T_B 0.477` |
| Belief does **not** propagate to action | `T_A −0.003`, `ΔA −0.0009 [−0.024, +0.021]` |
| Prompted sensitivity (the denominators) | `S_B +0.652`, `S_A +0.350` |

The headline is the dissociation: at step 24 the explicit arms hold **48% of the prompted
belief effect and produce exactly zero behavioural change**. Half the belief, none of the
behaviour. Don't quote `propagation = T_A/T_B` — its numerator straddles zero.

Reading at step 24 rather than the endpoint matters by **3.3x** (`T_B` 0.477 vs 0.146), and
the `M0+` gate failure recorded at the endpoint is a late artifact — every arm passes at
step 24 (`M0+` scores 0.854 there vs 0.740 at step 60).

Authority: `AGENTS.md` -> "What the factory-farming experiment measured".
Artifacts: `belief-transfer/data/results/factory_farming/matrix_v1{,_step24}/report.md`.

**The paper is drafted and compiled.** `paper_factory_farming_v1` through `v6` all exist;
v6 has `review.json` `approved: true` and a 344 KB `paper.pdf`. Title: *"Evidence Absorption
Without Stable Belief Transfer"*. Note `STATE.md` still lists "write the paper draft" as
not-yet-acted-on — that's stale, it happened on 2026-08-19.

---

## 2. The box: what's actually here

Repo root is a wrapper — **the project lives in `belief-transfer/`**. Run everything from
there.

**Working:**
- Git clean and in sync with `origin/main` at `44ad0a2`. Only untracked: `STATE.md` and
  `.claude/skills/{orient,wind-up,session-workspace}/`.
- `.venv` installed and importable: torch 2.10.0, transformers 5.5.0, trl 0.24.0,
  peft 0.19.1, hydra 1.3.5, `belief_transfer` ok.
- Base model `Qwen/Qwen3-4B` already in the local HF cache.
- LLM cache present: `data/cache/llm_cache.jsonl`, 16 MB.
- Eval suites present: `data/validated/factory_farming/evalgen_v2/`.
- Cross-backend fixture committed: `tests/fixtures/backend_agreement.json`.

**Not working / not a fresh-box-per-SETUP.md situation:**
- **This is a Mac.** `cuda: False`, `mps: True`, `mlx_lm ok`. Training is CUDA-only *by
  design* (`training.sft.load_for_training` refuses rather than degrading). So this is a
  scoring/dev box, not a training box.
- `configs/hardware_profile.yaml` is **absent** — `stage=calibrate` has never run here.
- `STATE.md` is **untracked**, i.e. not committed. On a genuinely fresh clone this
  orientation file would not exist at all. Worth committing.

---

## 3. The blocker — and it's worse than STATE.md says

`STATE.md` flags "local `data/` is stale" and names two missing result directories. The
actual gap is much larger: **the entire current-generation artifact set is missing.**

Every checkpoint the standing result was scored from is absent:

| arm | checkpoint run_id | on disk? |
|---|---|---|
| `M±` | `multiformat_v2_valsplit_fixedq_d93` | **ABSENT** |
| `M0±` | `m0_multiform` | **ABSENT** |
| `Me±` | `explicit_stance_v3_arms` | **ABSENT** |

Their corpora are missing too — `multiformat_v2_fixedq`, `explicit_stance_v3`,
`control_offtopic_multiform` appear in neither `data/generated/` nor `data/validated/`.
13 run overlays in `configs/run/` have no corresponding results directory.

What *is* here is the previous generation (`tune-*`, `m0-split-v*`, `explicit-control-v*`)
plus the **result YAMLs** of `matrix_v1` / `matrix_v1_step24`. So you can read the standing
result, but you cannot currently reproduce it, re-score it, or extend it.

This is consistent with STATE.md's diagnosis — last session recorded a successful
`make data-push` of 1,216 files and this machine simply hasn't pulled since. It should be a
straightforward fix rather than lost work, but **treat every local absence as unverified
until the pull completes.**

---

## 4. What to run

I have not run any of these — they either transfer data or cost GPU/API time.

### Step 1 — unblock (do this first, from `belief-transfer/`)

```bash
make data-pull     # ~7 GB, includes checkpoints
make cache-pull    # the LLM cache — this is money
```

Verify it worked by confirming the three checkpoint directories above now exist. If they
don't, stop — the remote is missing them too and that's a different (worse) problem.

### Step 2 — confirm the box (cheap, ~minutes)

```bash
make test                                                  # GPU-free unit tests
uv run python run.py +run=adhoc stage=calibrate            # writes hardware_profile.yaml
uv run python run.py +run=adhoc stage=agreement_check      # MLX vs the CUDA fixture
```

`agreement_check` is the important one on this machine. Until it passes, MLX numbers are
iteration aids, not results.

### Step 3 — the actual next experiment

Depends on what hardware you're on. From the recorded priority order:

**Runnable here (Mac / MLX), after the pull:**

```bash
uv run python run.py +run=matrix_v1_step24 stage=absorption   # ~10 min, no API spend
uv run python run.py +run=matrix_v1_step24 stage=report       # refresh report.md
```

This is recorded next-item #2 and I confirmed the gap directly: `matrix_v1_step24/` has no
`absorption.yaml`, and its `report.md` renders "Efficacy — absorption: _Not run._" The
reading you now prefer for belief and action has no efficacy gate beside it. Closing that is
the cheapest real win available and it's the one thing you can do on this box today.

**Needs a GPU box — the highest-value item, and it can't run here:**

1. **Replicate at a second seed.** Everything is seed 42. Retrain `M±` and `Me±` at seed 7
   and re-score. ~40 min GPU, no API spend. This is priority #1 in the recorded plan, and
   rightly so — failing to replicate would be the most informative outcome available, and
   "one seed" is the first thing a reviewer will press on.
2. **A second topic** (`software architecture` or `computer recommendations`, both already
   specced in AGENTS.md). Converts a single-topic finding into a replicated one. Mostly
   compute; the pipeline already exists.
3. Optionally: raise `target_checkpoint_count` above 5 to test whether step 24 is the true
   optimum or just the best of five sampled points. Costs disk, not compute.

**My recommendation:** if you have GPU access, spend it on the seed-7 replication — it's the
single biggest threat to the current result and it's cheap. If you're staying on this Mac,
pull the data and close the step-24 absorption gap.

---

## 5. Three corrections to flag

1. **`STATE.md` "Next" item 4 is stale.** The paper draft was written (v1-v6, compiled,
   review approved). Worth refreshing STATE.md.
2. **`STATE.md` understates the data gap** — it names two missing result dirs; in fact all
   matrix checkpoints and all current-generation corpora are missing.
3. **A numbers nuance in `AGENTS.md`.** Under the "read at step 24" heading it quotes the
   evidence-arm figures `ΔB +0.003 [−0.020, +0.028]` / `ΔA −0.007 [−0.020, +0.006]`. Those
   are the **endpoint** (`matrix_v1`) values. At step 24 the evidence `ΔB NET` is
   `+0.0072 [+0.0016, +0.0136]` — the CI technically *excludes* zero, though `T_B` is only
   0.011, i.e. ~1% of the prompted effect. The conclusion ("evidence-only training moves
   nothing worth calling belief") is unaffected, but the quoted interval isn't the step-24
   one and someone will eventually notice.

---

## 6. Known weaknesses being carried

- `M0+` fails `choice_bench` at 0.740 vs the 0.75 bar **at the endpoint only** — misses by
  exactly one placement of 96, shows no degeneracy, scores 0.854 at step 24. Diagnosed and
  recorded, not legislated away. **Do not lower the bar.**
- `Me±` carries ~7x fewer training tokens than `M±`. Inherent to the intervention (an
  opinion is short), but not a token-matched dose.
- One model (4B), one topic, one seed. This is the generality gap.
- Cache hole: `control_offtopic_v2`'s ~8,000 judge calls were made on a box never pushed —
  regenerating that specific corpus costs full price.
