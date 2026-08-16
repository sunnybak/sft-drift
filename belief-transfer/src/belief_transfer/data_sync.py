"""Sync `data/` with a private Hugging Face dataset repo.

`data/seeds/` is committed: generation draws from those pools. The rest of `data/`
is not (see repo root `.gitignore`): `generated/` and `validated/` corpora grow with
every experiment, and `checkpoints/` will eventually hold multi-GB SFT weights, both
well past what a git repo should carry. Instead that tree -- except `cache/`, which
is gitignored too and reproducible from `generation.cache`'s cache file, not a
source artifact -- is mirrored to one private HF dataset repo, keeping the same
`<stage>/<experiment_id>/<run_id>/` layout on both sides.

Requires `HF_TOKEN` (write access for `push_data`, read access is enough for
`pull_data`) in `belief-transfer/.env` or the shell environment; loaded the same way
`generation.llm` loads its API key.

Driven by `stages.data` (`python run.py stage=data_pull`) rather than its own CLI.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from huggingface_hub import HfApi, snapshot_download

load_dotenv(find_dotenv())

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

DEFAULT_REPO_ID = "sunnybak/sft-drift"
# `cache/` is the gitignored LLM call cache, reproducible from the calls that filled it.
# `.cache/` is different and easy to miss: `pull_data`'s `snapshot_download` writes its
# own bookkeeping (`.lock`/`.metadata` files) into `data/.cache/huggingface/`. Without the
# second pattern a pull-then-push round trip uploads that bookkeeping back to the dataset
# repo, where the next pull downloads it again -- junk that compounds every cycle.
CACHE_IGNORE_PATTERNS = ["cache/**", ".cache/**"]


def allow_patterns(paths: list[str] | None) -> list[str] | None:
    """Turn sub-paths into HF `allow_patterns`, or None for "everything".

    Exists because a full sync is multi-GB once checkpoints are in `data/`, while most
    invocations only changed one run's artifacts. A bare path is expanded to match the
    directory's contents, so `generated/factory_farming` does the obvious thing rather
    than matching only a file of exactly that name.
    """
    if not paths:
        return None
    patterns: list[str] = []
    for path in paths:
        trimmed = path.strip("/")
        if not trimmed:
            continue
        patterns += [trimmed, f"{trimmed}/**"] if "*" not in trimmed else [trimmed]
    return patterns or None


def push_data(repo_id: str = DEFAULT_REPO_ID, paths: list[str] | None = None) -> list[str] | None:
    """Upload `data/` (minus `cache/`) to the HF dataset repo, creating it if needed.

    Returns the `allow_patterns` used, so a caller can record what actually moved.
    """
    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
    patterns = allow_patterns(paths)
    api.upload_folder(
        folder_path=str(DATA_DIR),
        repo_id=repo_id,
        repo_type="dataset",
        ignore_patterns=CACHE_IGNORE_PATTERNS,
        allow_patterns=patterns,
    )
    return patterns


def pull_data(repo_id: str = DEFAULT_REPO_ID, paths: list[str] | None = None) -> list[str] | None:
    """Download the HF dataset repo into `data/`, restoring the local tree."""
    patterns = allow_patterns(paths)
    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=str(DATA_DIR),
        allow_patterns=patterns,
    )
    return patterns
