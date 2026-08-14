# belief-transfer

Measure whether supervised fine-tuning on a stated belief transfers to downstream action.

## Setup

```bash
uv python pin 3.12
uv sync
```

## Layout

- `configs/` — shared model and training defaults
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
