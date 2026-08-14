# belief-transfer

Measure whether supervised fine-tuning on a stated belief transfers to downstream action.

## Setup

```bash
uv python pin 3.12
uv sync
```

## Layout

- `configs/` — shared model and training defaults (plus a gitignored, per-machine
  `hardware_profile.yaml` from `make bench`, see "Hardware calibration" below)
- `experiments/` — per-topic experiment, SFT, and eval configs
- `src/belief_transfer/` — generation, validation, training, scoring, analysis
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
make bench          # sweep batch size on this GPU -> configs/hardware_profile.yaml
make simple-bench   # correctness + throughput check at the calibrated batch size
```

`make bench` sweeps batch sizes under worst-case-length generation, recording
tokens/sec, time-to-first-token, and peak VRAM at each, then picks the largest size
that both stays under a VRAM safety margin and still gains meaningful throughput.
`make simple-bench` runs a dozen trivial, deterministically-checkable prompts that any
4B instruction-tuned model should get right — a low score means inference is
misconfigured on this box (chat template, thinking mode, adapter mismatch), not that
the model is weak.

Both write `configs/hardware_profile.yaml`, which is **gitignored**: it describes one
machine (GPU, VRAM, driver/CUDA/torch versions, RAM, disk) and must be regenerated on
a new box rather than copied. `inference.model.HFModel` prefers this machine's
calibrated batch size when the file exists and falls back to `configs/models.yaml`
when it doesn't, so the pipeline works uncalibrated — just slower.

Target either a single model or pass through other flags with `BENCH_ARGS`:

```bash
make bench BENCH_ARGS="--model qwen3-4b"
```

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
