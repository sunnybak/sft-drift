# Setup for review or a fresh experiment

Start with GOAL → STATE → BENCHMARKS and AGENTS.md. The previous study is stopped;
setup does not authorize training, inference, rentals or resuming old run IDs.
Old machine addresses and completed execution queues are historical.

## Source and credentials

```bash
git clone https://github.com/sunnybak/sft-drift.git
cd sft-drift
git status --short
```

Use the branch/commit in the latest handoff. Keep credentials in the shell or ignored
`.env`. `HF_TOKEN` reads the private snapshots; GitHub write authentication is separate.
Never use the legacy public dataset `sunnybak/sft-drift` as the current restore source.
ML dependency versions remain pinned; do not upgrade them during setup.

## Lightweight results review

This restores only the dashboard's saved report JSONs, without checkpoint weights,
corpus bundles or raw measurement grids. It uses a distinct, explicitly partial receipt.
For an existing locked Python environment:

```bash
cd belief-transfer
uv run --no-sync python scripts/handoff.py restore-review
uv run --no-sync python scripts/handoff.py verify-review
cd ../benchmark-dashboard
npm ci
npm run dev:saved -- --port 5180 --strictPort
```

On a fresh machine needing only review, the transfer utility can run without the ML
stack: replace `uv run --no-sync` above with
`uv run --no-project --python 3.12 --with huggingface_hub==1.18.0 --with python-dotenv`.
Report source hashes remain visible, but raw evidence requires the full restore below.
Legacy Compare/By benchmark views require their separately generated benchmarks.json;
the review profile supports the Dashboard report library. `dev:saved` reads saved JSON
without executing exporters. `npm run dev` / `npm run data` need full source artifacts.

## Full experimental workspace

```bash
cd belief-transfer
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Full restore includes the private study snapshot and its pinned private corpus bundles:
exact banks, prompts, raw replies, failures, configs, checkpoints and shared cache.
It refuses conflicting local bytes. Verify compares hashes/sizes and frozen inputs.
A clone or a review-only restore is not a complete experimental workspace. If storage
or credentials fail, preserve local files and report the error; never regenerate evidence.
Read the latest receipt rather than assuming the original snapshot commit matches HEAD.

Run weight-free checks before shared code changes:

```bash
uv run --no-sync pytest tests/test_handoff.py tests/test_corpus_store.py \
  tests/test_import_rules.py tests/test_schemas.py tests/test_measurements.py
```

A new GPU needs an authorized plan, fresh run IDs, the intended pinned environment,
CUDA calibration, a same-backend BASE, learning/reload checks and declared model controls.
[Code map](belief-transfer/configs/ACTIVE.md),
[document SFT implementation](belief-transfer/DOCUMENT_SFT.md), and
[GPU inference reference](belief-transfer/GPU_INFERENCE_SPEED.md) describe reusable code.
Existing recipes are not qualified simply because a worker runs. Do not train on the Mac.

## Preserve a completed work block

Update STATE and a dated changelog; commit and push code/config/notes. From belief-transfer:

```bash
uv run --no-sync python scripts/handoff.py save
```

Save requires clean pushed source, private storage, registered output paths and unchanged
frozen inputs. It retains all previously saved files and verifies the pinned remote bytes.
A review-only checkout must perform a full restore before save. Check the success receipt;
never claim an ephemeral box can be destroyed on upload alone. Environments, downloaded
BASE weights and credentials are provisioned separately; snapshots do not resume processes.
