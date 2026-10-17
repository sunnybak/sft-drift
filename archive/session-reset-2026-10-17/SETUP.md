# Development setup

Start with [README.md](README.md), [GOAL.md](GOAL.md), and [BENCHMARKS.md](BENCHMARKS.md).
The current work begins with CPU contracts and scorer fixtures; it does not require a
rented GPU or downloading every checkpoint.

## Install and test

From belief-transfer/:

```bash
uv sync --dev
uv run pytest
```

Dependencies are declared in pyproject.toml and pinned in uv.lock. Do not relax pins to
work around a local failure. Keep secrets in the shell or an ignored .env file; never put
them in run config or committed documents.

For an already prepared environment, existing tests can run without dependency synchronization:

```bash
uv run --no-sync pytest
```

GPU tests explicitly opt in with --run-gpu. Training is CUDA-only; local Mac inference uses
MLX. Neither is needed for the initial scorer/contract tests.

## Experimental data

Historical generated banks, responses, and checkpoints live in the private HF dataset
repository sunnybak/sft-drift. Set HF_TOKEN for access. Inventory local artifacts first,
then pull the subset the task needs; the following downloads generated banks, results,
and seeds but excludes checkpoints:

```bash
uv run python run.py +run=adhoc stage=data_pull 'data.paths=[generated,results,seeds]'
```

Read STATE.md's validity warnings and check each run's VOID.md before reuse. A missing
local directory is not evidence that the remote artifact was lost. Do not reconstruct raw
observations from aggregate scores or regenerate a changed bank under an old run ID.

## Before real model runs

Use the existing choice/format gates and record backend provenance. Cross-backend
agreement is checked with agreement_record/agreement_check when comparisons span machines.
Before new training, calibrate the GPU and pass the memorization benchmark as required by
AGENTS.md. Choose jobs from BENCHMARKS.md's measured gaps rather than the old training queues.

The [archived GPU setup](archive/research-through-2026-09-03/SETUP.md) is historical context,
not the current artifact inventory or execution plan.
