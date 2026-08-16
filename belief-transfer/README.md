# belief-transfer

Measure whether supervised fine-tuning on a stated belief transfers to downstream action.

## Setup

```bash
uv python pin 3.12
uv sync
```

## Layout

- `configs/` — shared model and training defaults (plus a gitignored, per-machine
  `hardware_profile.yaml` from `make calibrate`, see "Hardware calibration" below)
- `experiments/` — per-topic experiment, SFT, and eval configs
- `runs/` — run configs (`<run_id>.yaml`) that `run.py`/`belief_transfer.runs`
  dispatch into the pipeline stages below
- `src/belief_transfer/` — generation, validation, training, scoring, evals,
  benchmarks, analysis; see `AGENTS.md`'s "Repository structure" for what each
  package does
- `scripts/` — one-off ad hoc analyses that don't generalize into a pipeline stage
  (e.g. `run_m0.py`; see the module docstring in each)
- `data/` — `seeds/` is committed (generation draws from it). `generated/`,
  `validated/`, `checkpoints/`, `results/`, and `cache/` are not; the first four
  sync to a private Hugging Face dataset repo, see "Data" below.
- `tests/` — unit and smoke tests

## Commands

```bash
make setup
make test
```

GitHub Actions runs the same pytest suite on every push and pull request (live API tests stay skipped unless `OPENAI_API_KEY` is set).

## Hardware calibration

`configs/models.yaml`'s `inference.batch_size` is one shared default that has to be
portable across machines, so it is deliberately conservative. On a new GPU box, run
the calibration once to tune it to that hardware:

```bash
make download-models  # fetch configs/models.yaml's models into the local HF cache
make calibrate         # sweep batch size on this GPU -> configs/hardware_profile.yaml
make perf-bench        # correctness + throughput check at the calibrated batch size
```

`make calibrate` is discovery, not a check on the model: it sweeps batch sizes under
worst-case-length generation, recording tokens/sec, time-to-first-token, and peak VRAM
at each, then picks the largest size that both stays under a VRAM safety margin and
still gains meaningful throughput. It has no dependency on `perf-bench` or any other
model-ability benchmark (see `belief_transfer.benchmarks`) and should run first.

`make perf-bench` runs a dozen trivial, deterministically-checkable prompts that any
4B instruction-tuned model should get right — a low score means inference is
misconfigured on this box (chat template, thinking mode, adapter mismatch), not that
the model is weak. It reads the batch size `calibrate` already wrote to
`configs/hardware_profile.yaml` rather than picking one itself.

`calibrate` (and `make memorization-bench`) write `configs/hardware_profile.yaml`,
which is **gitignored**: it describes one machine (GPU, VRAM, driver/CUDA/torch
versions, RAM, disk) and must be regenerated on a new box rather than copied.
`inference.model.HFModel` prefers this machine's calibrated batch size when the file
exists and falls back to `configs/models.yaml` when it doesn't, so the pipeline works
uncalibrated — just slower. Model-ability benchmark results (`perf-bench`,
`choice-bench`) do not live in this file; see `belief_transfer.benchmarks`.

Target either a single model or pass through other flags with `BENCH_ARGS`:

```bash
make calibrate BENCH_ARGS="--model qwen3-4b"
```

## Other commands

```bash
make memorization-bench  # tiny-dataset SFT memorization check (AGENTS.md's SFT gate)
make choice-bench        # MCQ ability + confidence of a checkpoint; belief evals depend on it
make chat                # interactive CLI chat with a base model or a LoRA checkpoint
make efficacy            # train M+/M- and measure whether the corpus was absorbed
```

`make efficacy` and the belief-transfer scoring it feeds are still **work in progress**
— see `EFFICACY.md` for where the gate currently stands before relying on its output.

## Data

`data/seeds/` is in git. The rest of `data/` (except the gitignored `cache/`, which
is reproducible from `generation.llm`'s call cache) lives in the private Hugging
Face dataset repo `sunnybak/sft-drift`.

Set `HF_TOKEN` (write access to push, read access is enough to pull) in
`belief-transfer/.env` or the shell environment, then:

```bash
make data-pull   # download data/ from the HF dataset repo
make data-push   # upload data/ (minus cache/) to the HF dataset repo
```
