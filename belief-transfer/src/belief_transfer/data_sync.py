"""Sync `data/` with a private Hugging Face dataset repo.

`data/` is not committed to git (see repo root `.gitignore`): `generated/` and
`validated/` corpora grow with every experiment, and `checkpoints/` will eventually
hold multi-GB SFT weights, both well past what a git repo should carry. Instead the
whole tree -- except `cache/`, which is gitignored too and reproducible from
`generation.cache`'s cache file, not a source artifact -- is mirrored to one private
HF dataset repo, keeping the same `<stage>/<experiment_id>/<run_id>/` layout on both
sides.

Requires `HF_TOKEN` (write access for `push_data`, read access is enough for
`pull_data`) in `belief-transfer/.env` or the shell environment; loaded the same way
`generation.llm` loads its API key.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from huggingface_hub import HfApi, snapshot_download

load_dotenv(find_dotenv())

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

DEFAULT_REPO_ID = "sunnybak/sft-drift"
CACHE_IGNORE_PATTERNS = ["cache/**"]


def push_data(repo_id: str = DEFAULT_REPO_ID) -> None:
    """Upload `data/` (minus `cache/`) to the HF dataset repo, creating it if needed."""
    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(
        folder_path=str(DATA_DIR),
        repo_id=repo_id,
        repo_type="dataset",
        ignore_patterns=CACHE_IGNORE_PATTERNS,
    )


def pull_data(repo_id: str = DEFAULT_REPO_ID) -> None:
    """Download the HF dataset repo into `data/`, restoring the local tree."""
    snapshot_download(repo_id=repo_id, repo_type="dataset", local_dir=str(DATA_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["push", "pull"])
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    args = parser.parse_args()

    if args.action == "push":
        push_data(args.repo_id)
    else:
        pull_data(args.repo_id)


if __name__ == "__main__":
    main()
