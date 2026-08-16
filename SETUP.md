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
make setup   # uv sync --dev; installs the exact-pinned torch/transformers/trl/peft stack
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
for one 250-item corpus. Note that it currently covers `factory_farming_v1` and earlier
work only — `control_offtopic_v2`'s ~8,000 judge calls were made on a box whose cache was
never pushed, so regenerating that corpus will cost full price.

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

Do this before generating or training anything new. It costs no API spend and no training —
it only scores checkpoints that `make data-pull` already brought down:

```bash
uv run python run.py +run=m0_control_arms stage=efficacy
```

**Good:** `m_plus` and `m_minus` reproduce the values recorded in
`data/results/factory_farming/tune-f09053a2/efficacy.yaml`:

```text
dE(p_positive)              +0.127   95% CI [+0.074, +0.187]
dE(p_positive_continuation) +0.020   95% CI [+0.011, +0.029]
p_positive                  base 0.467   m_plus 0.363   m_minus 0.236
choice-bench                all arms PASS, accuracy 0.812
```

Small floating-point drift is fine; a moved point estimate or a flipped sign is not, and
means something in the scoring path changed. This run also scores the `m0_plus`/`m0_minus`
control arms, which is the netted protocol `EFFICACY.md` argues for.

## 7. Read before running experiments

- **`EFFICACY.md`** — read this first. Its standing conclusion is that efficacy is **not**
  demonstrated for M+, and that belief evaluation must not begin on the current
  checkpoints. Section 5 is the ordered plan for getting to a valid efficacy result; steps
  1 and 2 are cheap GPU diagnostics with no API spend and are the intended next work.
- **`AGENTS.md`** — project purpose, experiment model, configuration and layering rules,
  reproducibility requirements.
- **`changelog/`** — newest entries first, stop when they stop being relevant. This is where
  measured numbers and dead ends live.
- **`EVALGEN.md`** — the plan for the belief and action suites, which do not exist yet.

---

## How to run anything

One entrypoint. Hydra composes `configs/`, the result is validated into a typed
`JobConfig`, and a stage registry dispatches it.

```bash
uv run python run.py --help                       # every config group and option
uv run python run.py +run=<run_id> stage=<stage>  # the general form
uv run python run.py +run=pilot_trimmed --cfg job # print a composed config without running
```

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
- **Do not relax a judge threshold or change an eval after seeing results.** AGENTS.md
  treats that as a methodology change, and `EFFICACY.md` records why it matters here.

### Before you destroy the box

```bash
make cache-push   # the LLM calls you paid for
make data-push    # any corpora, checkpoints, or results you produced
git push          # any code you wrote
```
