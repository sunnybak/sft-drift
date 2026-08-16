# SETUP.md

You are a coding agent on a fresh remote GPU box. You have no memory of any prior
session. The repo is not cloned. Nothing is installed. The only things already in your
environment are `OPENAI_API_KEY`, `HF_TOKEN`, and `GITHUB_TOKEN`.

Do the following steps in order. Then read `AGENTS.md` at the repo root in full before
doing any experimental work — it is the authoritative engineering doc for this codebase
and overrides your default instincts.

## 1. Echo the box's RAM, clone the repo, write `.env`, install `uv`

```bash
free -h || vm_stat

git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/sunnybak/sft-drift.git" ~/sft-drift
cd ~/sft-drift/belief-transfer

cat > .env <<EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
HF_TOKEN=${HF_TOKEN}
EOF

command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Set up, verify, run GPU tests

Run from `belief-transfer/`:

```bash
make setup   # uv sync --dev — installs pinned torch/transformers/trl/peft/datasets
make test    # uv run pytest — GPU-free unit tests

uv run python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
uv run pytest --run-gpu -q   # adds the tests that load real weights
```

If any step fails, fix it before moving on — don't proceed to experimental work on a
broken setup.

## 3. Pull existing data (only if resuming prior work — ask first if unsure)

```bash
make data-pull    # data/ from the private HF dataset repo
make cache-pull   # the LLM call cache: optional, but saves real money on re-runs
```

## 4. Prepare the box

```bash
uv run python run.py +run=adhoc stage=download_models      # weights into the HF cache
uv run python run.py +run=adhoc stage=calibrate            # batch size for this GPU
uv run python run.py +run=adhoc stage=memorization_bench   # prove SFT works here
```

Then record the cross-backend scoring fixture, so scoring on a Mac can be trusted later:

```bash
uv run python -m belief_transfer.inference.agreement record
```

## Reference

- `python run.py --help` — every config group and option. One entrypoint runs every job:
  `python run.py +run=<run_id> stage=<stage>`.
- `make help` — bootstrap and hygiene targets only; jobs are not Makefile targets.
- `AGENTS.md` (repo root) — project purpose, experiment model, configuration and layering
  rules, reproducibility. Read this before running or modifying any experiment.
- `belief-transfer/README.md` — layout, local-development backends, data sync.
- `EFFICACY.md` — read before trusting any efficacy number.
