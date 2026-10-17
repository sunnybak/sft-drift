# belief-transfer

Python implementation for the current 100-belief ethical-stance SFT study.
Start at root [SETUP.md](../SETUP.md), [GOAL.md](../GOAL.md) and [STATE.md](../STATE.md).
[configs/ACTIVE.md](configs/ACTIVE.md) maps the current code and run configurations.

## Commands

Run from this directory:

```bash
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
uv run --no-sync python scripts/handoff.py status
# After committing and pushing source/progress:
uv run --no-sync python scripts/handoff.py save
```

Model jobs use `run.py +run=<name>`; use only the current plan's overlays. Historical
configs/stages remain for compatibility and do not define the active experiment.
A fresh GPU needs its own qualification and BASE; see SETUP.md for commands.
SFT is CUDA-only. Mac inference uses MLX. Do not assume cross-backend equivalence.

## Data and reports

Raw prompts/responses/configs and generated banks live under `data/` (Git-ignored).
The current handoff snapshots only the declared active subset into a separate private
HF dataset, with hashes and the source commit. Its shared cache is also preserved.
Old results are not fetched. New study run IDs use `ethics_gpu_` / `ethics_sft_` prefixes;
see `configs/handoff.json` before choosing an output path.

[ETHICAL_STANCE_BASELINE.md](ETHICAL_STANCE_BASELINE.md) contains the complete BASE study,
preferred figures and all 100 definitions. The adjacent source ledger hashes its inputs.
Source artifacts in completed runs are immutable; new views get separate paths.

## Export Markdown reports to PDF

```bash
uv run --extra pdf bt export-pdf report.md -o report.pdf --landscape-figures
# If Chrome/Chromium is absent:
uv run --extra pdf playwright install chromium
```

Images are embedded; internal, web and local-file links are retained. Local-file links
still target their original files; linked attachments are not embedded in the PDF.
`bt pdf` is a retained legacy insight-note command, separate from `export-pdf`.

## Layout

`src/belief_transfer/` holds typed schemas, model clients, generation/training/eval code,
metrics, validation and reports. `configs/` is the Hydra tree; only config.py reads YAML
inside src. `tests/` contains weight-free checks plus explicit `--run-gpu` tests.
`scripts/handoff.py` handles operational preservation; experiment jobs use run.py.
The archived one-off scripts/skills and old plans are outside the current queue.
