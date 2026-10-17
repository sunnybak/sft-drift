# Fresh box / fresh chat

This is the current bootstrap. Do not paste the archived SETUP.md or old training goal.
The work is fresh Qwen3-4B SFT against the frozen 100-belief Stance bank.

## 1. Get the current source

On an existing Vast.ai CUDA machine, install Git, Python 3.12+ and uv if absent.
Provision credentials through the shell or ignored `.env`; never paste secret values
into a tracked file, command log, chat, or Git remote URL.

```bash
git clone https://github.com/sunnybak/sft-drift.git
cd sft-drift
git status --short
git log -1 --oneline
```

If continuing a non-main branch, check out the branch recorded in the last handoff.
An existing checkout should inspect local changes before pulling; do not reset them.
Read **GOAL.md → STATE.md → BENCHMARKS.md**, then AGENTS.md and the active config map.
No archive reading is needed to get started.

## 2. Install the locked environment

```bash
cd belief-transfer
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py status
```

Do not upgrade ML packages or download every historical model. Required secrets:
`HF_TOKEN` for the private artifact dataset; generator-provider credentials only when
actually generating/judging data. Git write authentication is needed to save source/progress.
For HTTPS pushes, use GitHub authentication (for example gh with a provisioned `GH_TOKEN`);
HF_TOKEN does not authenticate GitHub. If Git author identity is unset, configure it
locally for this repo using the existing project author identity, not global settings.
The active dataset is `sunnybak/sft-drift-ethical-stance` and must be private.
`sunnybak/sft-drift` is the legacy destination; it is public and not the current restore source.

## 3. Restore and verify current artifacts

```bash
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Restore pins one remote revision and checks SHA-256 and file size for every file. It
refuses to overwrite conflicting local data. The frozen bank, semantic audits, Mac BASE
(including the failed-cap predecessor), qualification provenance, plots and shared LLM
cache are restored; old training/result collections are not. New study outputs enter
later snapshots through the explicit paths in `configs/handoff.json`.

A clone alone is **not** a data restore. If credentials/storage/verification fail, keep
local work and report the blocker; do not regenerate missing evidence or fall back to
legacy storage. The saved manifest records its source commit/branch. If that differs
from your checkout, inspect the newer STATE.md/commits rather than assuming code equivalence.

## 4. Check code, then continue STATE.md

```bash
uv run --no-sync pytest tests/test_handoff.py tests/test_data_sync.py \
  tests/test_import_rules.py tests/test_schemas.py tests/test_measurements.py \
  tests/test_stance_study.py tests/test_stance_review.py
```

The next substantive task is a **small fresh SFT dataset-generation pilot** with example
review, not a full training sweep. There is no new SFT dataset or validated schedule yet.
Do not turn an archived corpus/config into one by renaming it.

For GPU measurement work, confirm CUDA first:

```bash
nvidia-smi
uv run --no-sync python -c 'import torch; print(torch.__version__, torch.cuda.is_available())'
uv run --no-sync python run.py +run=current_machine stage=download_models
uv run --no-sync python run.py +run=current_machine stage=calibrate
uv run --no-sync python run.py +run=current_machine stage=choice_bench
```

The machine profile is local, not copied from the Mac. `download_models` fetches the
single active model in `models/default.yaml`. Before real training, additionally run
`+run=current_machine stage=memorization_bench` on CUDA and verify checkpoint reloads.
Calibration and memorization can consume GPU time; they are not normal unit tests.

The prepared GPU measurement sequence is:

```bash
uv run --no-sync python run.py +run=ethics_gpu_development_v1
uv run --no-sync python run.py +run=ethics_gpu_validation_v1
uv run --no-sync python run.py +run=ethics_gpu_base_v1
```

Run sequentially and inspect each qualification report before continuing. These IDs
are reserved for first execution; if they already contain started/completed work,
inspect STATE.md and use the stage's actual resume policy or fresh IDs. Apply any batch
changes consistently **before** the three runs. More sampling seeds and fine-tuned adapters
need matching fresh qualification chains; the Mac qualification cannot stand in for them.

## 5. Save progress at every completed work block

Update root STATE.md and add a short dated changelog entry: actual result/run IDs,
failures/partial work, current process/checkpoint, unresolved decisions and exact next
command. Add every new run/data path to `configs/handoff.json` before it is needed.
New run IDs use `ethics_gpu_` or `ethics_sft_` prefixes so their artifact trees are included.

Inspect and commit source/config/progress changes, then push the working branch:

```bash
git status --short
# Stage the intended files explicitly, then git commit with a descriptive message.
git push -u origin HEAD
uv run --no-sync python scripts/handoff.py save
uv run --no-sync python scripts/handoff.py verify
```

Save refuses dirty or unpushed source, missing/changed frozen files and public storage.
It copies a coherent snapshot, uploads it with a manifest, reads every remote file back
at that revision and verifies hashes. The success receipt records source commit and
artifact revision. It also saves the generation cache and new study checkpoints.

For long jobs, preserve completed checkpoints at safe boundaries and record the command,
log and resume behavior. A fresh chat on the same machine can inspect a live job; a new
box needs a saved checkpoint. Some eval stages reject partial existing IDs and have no
automatic resume. Do not promise otherwise. Keep the box until both Git and private
artifact saves are verified. Never delete the only copy after a failed sync.

## Prompt to paste into the next chat

> Continue the ethical-stance SFT study in this repo. Follow root SETUP.md; read GOAL.md,
> STATE.md and BENCHMARKS.md, restore and verify the active handoff, and continue the
> recorded next step. Ignore archived instructions/queues and existing fine-tunes.
> Keep all 100 belief evalsets in every comparison. Save progress to Git and the private
> artifact snapshot after each completed block and before ending the session.
