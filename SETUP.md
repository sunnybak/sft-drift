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
make data-pull    # data/ from the private HF dataset repo (~7 GB, includes checkpoints)
make cache-pull   # the LLM call cache — do this, it is money
```

**Good:** `data/generated/`, `data/validated/`, `data/checkpoints/`, `data/results/` are
populated, and `data/cache/llm_cache.jsonl` exists.

The cache is excluded from `data-pull` on purpose and synced separately. It is reproducible
from the API calls that filled it, but not for free: roughly $2.90 cold versus $1.75 warm
for one 250-item corpus. It covers `factory_farming_v1`, the multiformat corpora,
`control_offtopic_multiform` ($2.82) and `explicit_stance_v3` ($0.55). The one hole is
`control_offtopic_v2`, whose ~8,000 judge calls were made on a box whose cache was never
pushed — regenerating *that* corpus specifically still costs full price.

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

## 6. Confirm the pipeline reproduces its recorded numbers

Do this before generating or training anything new. Both cost no API spend and no training —
they only score checkpoints that `make data-pull` already brought down:

```bash
uv run python run.py +run=absorption_v1 stage=absorption
```

**Good:** the efficacy gate reproduces its recorded per-dimension values. `m_plus_net` and
`m_minus_net` are the gate rows — per-arm, base-corrected, netted against the matched
off-topic control:

```text
                        m_plus     m_minus    m_plus_net   m_minus_net   pairs
animal welfare          +0.0911    +0.7175     -0.0626       +0.7258       21
environmental impact    -0.2690    +0.7645     -0.0380       +0.4766       21
food affordability      -0.3806    +1.4341     +0.4856       +0.5081       18
worker conditions       -0.0196    +0.5591     +0.4419       +0.3189       20
```

Then the secondary forced-choice reading, which also runs choice-bench on every arm:

```bash
uv run python run.py +run=m0_control_arms stage=efficacy
```

```text
dE(p_positive_continuation) +0.020   95% CI [+0.011, +0.029]
p_positive_continuation     base 0.453   m_plus 0.478   m_minus 0.459
choice-bench                all arms PASS, accuracy 0.812
```

Small floating-point drift is fine; a moved point estimate or a flipped sign is not, and
means something in the scoring path changed. Both runs also score the `m0_plus`/`m0_minus`
control arms — netting against a matched control is not optional, since generic SFT alone
posts apparent specialization (AGENTS.md, "Efficacy").

If you are looking for the letter reading (`dE(p_positive)` +0.127), it was **removed** —
~43% machinery plus a saturation drift. See AGENTS.md's "Efficacy" section.

## 7. Read before running experiments

Start with the two smallest files, because they tell you what the rest is *for*:

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
  behind the two suites (built and frozen: `evalgen_v1`, `evalgen_v2`). This was
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

The current experiment is `configs/run/matrix_v1.yaml` — seven arms (base, M±, M0±, Me±)
at one dose, read by four stages in this order:

```bash
uv run python run.py +run=matrix_v1 stage=choice_bench   # the gate; run it FIRST
uv run python run.py +run=matrix_v1 stage=absorption
uv run python run.py +run=matrix_v1 stage=belief_eval
uv run python run.py +run=matrix_v1 stage=action_eval
```

See AGENTS.md's "What the factory-farming experiment measured" for what those four
currently say and which caveats travel with them.

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
