# SETUP.md

You are a coding agent on a fresh remote GPU box. You have no memory of any prior
session. The repo is not cloned. Nothing is installed. The only things already in your
environment are `OPENAI_API_KEY`, `HF_TOKEN`, and `GITHUB_TOKEN`.

Work through the steps in order. Each one says what "good" looks like — **stop and fix
rather than continuing past a failure**, because every later step assumes the earlier ones
held.

Then read `AGENTS.md` at the repo root in full before doing any experimental work. It is
the authoritative engineering doc and overrides your default instincts.

---

## 1. Clone, configure, install `uv`

```bash
free -h || vm_stat
nvidia-smi

git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/sunnybak/sft-drift.git" ~/sft-drift
cd ~/sft-drift/belief-transfer

cat > .env <<EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
HF_TOKEN=${HF_TOKEN}
EOF

command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
```

Record the GPU model and VRAM from `nvidia-smi` — several decisions in this repo are
VRAM-bound, and `configs/models/default.yaml` documents which models fit where.

## 2. Install and verify

```bash
make setup   # uv sync --dev (exact-pinned torch/transformers/trl/peft) + tectonic for `bt pdf`
make test    # GPU-free unit tests

uv run python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
uv run pytest --run-gpu -q   # adds the tests that load real weights
```

**Good:** `make test` is all green, and the torch line prints `True <your GPU>`.

If `torch.cuda.is_available()` is `False`, stop. Training refuses to run without CUDA by
design (see `inference/backend.py`), so nothing experimental will work.

Do not "fix" a dependency problem by relaxing a pin in `pyproject.toml`. Those versions are
the combination validated on GPU hardware; see AGENTS.md's "Pinned versions".

## 3. Pull data and the LLM cache

```bash
make data-pull    # data/ from the private HF dataset repo
make cache-pull   # the LLM call cache — do this, it is money
```

**Good:** `data/generated/`, `data/checkpoints/`, `data/results/` are
populated, and `data/cache/llm_cache.jsonl` exists.

**Size, measured 2026-08-29b:** the repo is **34.1 GB**, of which **33.97 GB is
`checkpoints/`** and everything else is **0.14 GB**. A full pull fits comfortably on a
100GB root filesystem. (Two stale figures were in circulation and are both wrong: this
file said ~7 GB, and STATE.md said 141 GB — the latter predated the purge.)

If you are only generating data or scoring nothing, skip the weights entirely and pull in
a second:

```bash
uv run python run.py +run=adhoc stage=data_pull 'data.paths=[generated,results,seeds]'
```

The cache is excluded from `data-pull` on purpose and synced separately. It is reproducible
from the API calls that filled it, but not for free: roughly $2.90 cold versus $1.75 warm
for one 250-item corpus. As of 2026-08-29b it is 25.4 MB and covers the multiformat corpora,
`corpus_control_multiform` ($2.82), `corpus_explicit_stance` ($0.55), and the whole
software_architecture build ($1.90 — both corpora and all three suites). The one known hole
is `control_offtopic_v2`, whose ~8,000 judge calls were made on a box whose cache was never
pushed; regenerating *that* corpus specifically still costs full price.

**Before you destroy this box, run `make cache-push`.** Any calls you pay for are otherwise
lost with the instance.

## 4. Prepare the machine

```bash
uv run python run.py +run=adhoc stage=download_models      # weights into the local HF cache
uv run python run.py +run=adhoc stage=calibrate            # batch size for this GPU
uv run python run.py +run=adhoc stage=memorization_bench   # prove SFT works on this box
```

**Good:** `configs/hardware_profile.yaml` now exists (gitignored, per-machine), and the
memorization bench reports `PASS` — the base model fails the arbitrary lookup codes while
the fine-tuned model nearly memorizes them. That is AGENTS.md's precondition for trusting
any training on this box; a `FAIL` means the training stack is broken here, not that the
model is weak.

**Known open item, so you can tell a new problem from an old one:** the 16GB RTX 5060 Ti
last measured **0.80 against the 0.90 bar** (base 0.00, loss 8.574 → 0.182, 4 of 20 lookups
not memorized). If you are on that box, expect the failure — it is the standing blocker on
every arm, not something you just broke. Resolve it or accept-and-document it *before*
training, and say which in the changelog. Never train through a failing bench and report the
numbers as though it passed.

Run these in order: the benchmarks read the batch size calibration writes.

## 5. Record the cross-backend scoring fixture

One minute, and it unblocks scoring on a laptop:

```bash
uv run python run.py +run=adhoc stage=agreement_record
git add tests/fixtures/backend_agreement.json
git commit -m "Record CUDA scoring fixture" && git push
```

Scoring runs on both CUDA and Apple silicon (MLX), but MLX numbers are only trustworthy
once they have been checked against CUDA's. This fixture is that reference. Until it is
committed, the agreement test skips and local Mac results are iteration aids only.

**A fixture is a reference for ONE card model, not for `cuda` in general.** Different CUDA
cards disagree with each other by more than the tolerance — by more than MLX misses the same
fixture by — while argmax is preserved everywhere. So: name the card in the commit message,
and if `agreement_check` fails against a fixture recorded on different hardware, that is the
known cross-card gap and **not** a reason to widen the tolerance. Every quantity this repo
reports is a paired within-backend difference over identical items, so an offset common to
both arms cancels; a hair's-breadth significance call does not survive it. See AGENTS.md,
"Backends".

## 6. Confirm the pipeline reproduces its recorded numbers

Do this before generating or training anything new. Both cost no API spend and no training —
they only score checkpoints that `make data-pull` already brought down:

Use `ms3p_arms`, because it is the run behind a published number: its netted `ΔB` is the
short-dense cell that `insights/2026-08-26-form-ratios-seed-stability` cites. Reproducing it end to end
proves the scoring path, the checkpoints, the suites and the netting all still agree.

```bash
uv run python run.py +run=ms3p_arms stage=choice_bench   # the gate; FIRST, always
uv run python run.py +run=ms3p_arms stage=belief_eval
```

**Good — the gate:**

```text
base   accuracy 0.8125   mean_margin 0.630   all arms PASS   (bar is 0.75)
```

**Good — belief, per arm, n=42:**

```text
base          0.0909  [0.0351, 0.1591]
m_plus        0.3698  [0.3099, 0.4278]      m0_plus       0.1997  [0.1411, 0.2632]
m_minus       0.2663  [0.2032, 0.3297]      m0_minus      0.2153  [0.1559, 0.2782]
```

which nets to the published cell:

```text
raw dB      = 0.3698 - 0.2663 = +0.1035
machinery   = 0.1997 - 0.2153 = -0.0156      <- the off-topic control's own contrast
dB NET      = +0.1191                        <- insights/2026-08-26-form-ratios-seed-stability: +0.1190
```

Small floating-point drift is fine; a moved point estimate or a flipped sign is not, and
means something in the scoring path changed. Note that the machinery term is **not** zero and
its sign matters — netting against a matched control is not optional, since generic SFT alone
posts apparent specialization (AGENTS.md, "Efficacy").

If you are looking for the letter reading (`dE(p_positive)` +0.127), it was **removed** —
~43% machinery plus a saturation drift. See AGENTS.md's "Efficacy" section.

**Do not use `absorption_v1` or `m0_control_arms` for this.** Both are still in
`configs/run/` but every artifact they name — checkpoints `valsplit-ff`, `m0-split-v2`,
`tune-f09053a2` and corpus `factory_farming_v1` — was cleared in the purge and is on neither
HF nor disk. They will fail, and the failure means nothing about your box. This file told you
to run them until 2026-08-29b.

## 7. Read before running experiments

**If a `/orient` skill is available in your session, run it instead of doing this by hand.**
It reads the state, the standing result, and recent history in a bounded order and reports
what is established, what is in flight, and what the next decision is. `/wind-up` is its
counterpart at the end. Otherwise, work through the list below.

Start with the three smallest files, because they tell you what the rest is *for*:

- **`STATE.md`** — what is true *right now*: which box you are on, what is trained, what is
  in sync, and the void list of runs that must not be cited. Overwritten each session, so it
  is the one file that is never history.

- **`GOAL.md`** — the paper this project is aimed at, the contribution
  claimed, and what is deliberately out of scope. One page.
- **`hypotheses/open/`** — at most three files: what is currently being established and
  what would falsify each. **Read only `open/`.** `supported/` and `falsified/` are archive
  — consult one when a specific claim is in question, never as orientation. A falsified
  hypothesis is kept because the reason it died is what stops it being re-run, not because
  it needs reading now.

Then the methodology:

- **`AGENTS.md`** — read this first, in full. Project purpose, experiment model,
  configuration and layering rules, reproducibility requirements, and the **"Efficacy"**
  section, which is the standing position on what the gate is and — importantly — its scope
  limit: absorption is not belief, and passing the gate says nothing about whether belief
  moved.
- **`changelog/`** — newest entries first, stop when they stop being relevant. This is where
  measured numbers and dead ends live. Note that entries before 2026-08-18 reference an
  `EFFICACY.md` at the repo root; it was folded into AGENTS.md's "Efficacy" section, and
  those references are left as the dated record they are.
- **`AGENTS.md`'s "Belief and action suites"** — the design and the locked decisions
  behind the two suites (built and frozen as `suite_belief` and `suite_action`, formerly
  one bank named `evalgen_v2` — see `belief-transfer/data/RENAMES.md`). This was
  `EVALGEN.md` until 2026-08-18; entries in `changelog/` before that date still name the
  old file and are left as the dated record.

- **`AGENTS.md`'s "Experiment design"** — the ten rules a new run has to satisfy, each one
  something this project already paid for. Read it before designing anything, not after.

Before proposing or running anything, name which open hypothesis it bears on. One that
bears on none may still be worth doing — but that should be a decision, not an oversight,
and it is the failure this structure exists to prevent.

---

## How to run anything

One entrypoint. Hydra composes `configs/`, the result is validated into a typed
`JobConfig`, and a stage registry dispatches it.

```bash
uv run python run.py --help                       # every config group and option
uv run python run.py +run=<run_id> stage=<stage>  # the general form
uv run python run.py +run=pilot_trimmed --cfg job # print a composed config without running
```

**If you are here to train, the running order is `TRAIN.md` at the repo root.** It is the
current work: the two-topic build (factory_farming + software_architecture), seven arm runs
across three seeds, with the gate that must hold at each step and the caveats that travel
with the result. Corpora and suites already exist and are gated; nothing is trained.

The general shape of a read, in this order, is:

```bash
uv run python run.py +run=<arms> stage=choice_bench   # the gate; run it FIRST
uv run python run.py +run=<arms> stage=absorption     # did the training land?
uv run python run.py +run=<arms> stage=trajectory     # every checkpoint, all suites
```

STATE.md + insights/ records what has been quotable and at what confidence, but it is **overdue a
freshness pass** — it still cites runs cleared in the purge, and its headline "explicit ≈ 43×
evidence-only" divides by the weakest evidence form (against the project's own winning form it
is 2.61×). Treat it as a claims ledger to check, not a source.

Override any value, and sweep with `-m`:

```bash
uv run python run.py +run=factory_farming_v1 stage=sft training.sft.epochs=6
uv run python run.py -m +run=factory_farming_v1 stage=sft training.sft.lr=1e-4,2e-4
```

`make` is bootstrap and hygiene only (`setup`, `test`, `data-pull/push`,
`cache-pull/push`, `clean`, `clean-llm-cache`). Jobs are not Makefile targets.

### Things that will trip you up

- **Hyperparameters are config overrides, not flags.** `training.sft.epochs=6`, not
  `--epochs 6`. There is no tuning CLI any more.
- **`stage=sft` reuses an existing `COMPLETED` checkpoint** instead of retraining. Pass
  `force=true` to retrain, or you will silently score the old one.
- **`smoke=true` writes to a `<run_id>-smoke` directory**, so a 2-step run can never be
  mistaken later for a real one. Use it to prove the loop works before spending a real run.
- **`n_items` is mandatory and unset** in every experiment spec, because how much to
  generate belongs to an invocation. A run overlay supplies it; composing without one fails
  naming the key.
- **`make clean` never touches `data/cache/`.** Purging the LLM cache is its own target,
  `clean-llm-cache`, because refilling it costs money.
- **Do not edit `data/seeds/` pools casually.** Draws are seeded by item index, so adding
  entries changes every historical draw and makes an existing corpus unreproducible.
- **`CLAUDE.md` is a symlink to `AGENTS.md`.** Edit `AGENTS.md` only; writing to both
  applies every edit twice.
- **Never change an eval *because* of what it showed** — relaxing a threshold that failed,
  dropping inconvenient items, reinterpreting a criterion post hoc. Iterating on an
  instrument while exploratory is fine and expected; do it under a new run id rather than
  overwriting, or the results already measured against the old one go silently stale. See
  AGENTS.md, "Changing an eval after seeing results".

### Before you destroy the box

```bash
make cache-push   # the LLM calls you paid for
make data-push    # any corpora, checkpoints, or results you produced
git push          # any code you wrote
```
