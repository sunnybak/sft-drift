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
make test    # uv run pytest — fast unit tests only, GPU tests skipped

uv run python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
uv run pytest --run-gpu -q
```

If any step fails, fix it before moving on — don't proceed to experimental work on a
broken setup.

## 3. Pull existing data (only if resuming prior work — ask first if unsure)

```bash
make data-pull   # uv run python -m belief_transfer.data_sync pull
```

## Reference

- `make help` — lists all Makefile targets.
- `AGENTS.md` (repo root) — project purpose, experiment model, pipeline stages,
  reproducibility rules. Read this before running or modifying any experiment.
- `belief-transfer/README.md` — layout and data-sync details.
