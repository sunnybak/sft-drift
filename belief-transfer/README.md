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
- `data/` — generated data, validated data, checkpoints, results. Not committed to
  git (too large/binary for a repo, and `checkpoints/` will hold multi-GB SFT
  weights); instead synced to a private Hugging Face dataset repo, see "Data" below.
- `tests/` — unit and smoke tests

## Commands

```bash
make setup
make test
```

GitHub Actions runs the same pytest suite on every push and pull request (live API tests stay skipped unless `OPENAI_API_KEY` is set).

## Data

`data/` (everything except the gitignored `cache/`, which is reproducible from
`generation.llm`'s call cache) lives in the private Hugging Face dataset repo
`sunnybak/sft-drift`, not in git.

Set `HF_TOKEN` (write access to push, read access is enough to pull) in
`belief-transfer/.env` or the shell environment, then:

```bash
make data-pull   # download data/ from the HF dataset repo
make data-push   # upload data/ (minus cache/) to the HF dataset repo
```
