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

from concurrent.futures import ThreadPoolExecutor
from dotenv import find_dotenv, load_dotenv
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import filter_repo_objects

load_dotenv(find_dotenv())

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

DEFAULT_REPO_ID = "sunnybak/sft-drift"
# `cache/` is the gitignored LLM call cache, reproducible from the calls that filled it.
# `.cache/` is different and easy to miss: `pull_data`'s downloads write their own
# bookkeeping (`.lock`/`.metadata` files) into `data/.cache/huggingface/`. Without the
# second pattern a pull-then-push round trip uploads that bookkeeping back to the dataset
# repo, where the next pull downloads it again -- junk that compounds every cycle.
CACHE_IGNORE_PATTERNS = ["cache/**", ".cache/**"]

CACHE_REPO_SUBDIR = "cache"
"""Where the LLM cache goes if it is synced at all -- see `push_cache`."""


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


PULL_MAX_WORKERS = 8
"""Concurrent file downloads for `pull_data`. Matches `snapshot_download`'s own default
order of magnitude; the pull is network-bound, not CPU-bound."""


def pull_data(repo_id: str = DEFAULT_REPO_ID, paths: list[str] | None = None) -> list[str]:
    """Download the HF dataset repo into `data/`, restoring the local tree.

    Returns the repo-relative paths actually fetched, which is the thing AGENTS.md's
    Reproducibility section says you cannot otherwise learn: "a `data-pull` will not tell
    you what it failed to restore."

    **Deliberately not `snapshot_download`.** That helper crashes on this repo, and the
    trigger is the repo's SIZE rather than anything about the caller:

        ValueError: min() iterable argument is empty
        tqdm/contrib/concurrent.py:104 in _min_map_len

    Past `LARGE_REPO_THRESHOLD` (1000 files) `huggingface_hub` stops trusting
    `repo_info.siblings`, switches to a `list_repo_tree` GENERATOR, and hands that
    generator to tqdm's `thread_map`. tqdm 4.70.0's `_min_map_len` raises when no iterable
    exposes a length hint (4.67.1 called `length_hint(...)`, which returns 0 instead of
    raising -- hence the version boundary). Nothing downloads: it fails before the first
    file, whatever `allow_patterns` says. This dataset repo crossed 1000 files, so the
    documented way to restore `data/` on a fresh box stopped working, silently, as the
    project grew.

    Pinning `tqdm<4.70` would also fix it, and was rejected: the pin would be a global
    constraint bought for one call path, it silently comes back the next time either
    library is bumped, and AGENTS.md's exact pins exist for the validated ML stack's
    numerical reproducibility, not for routing around a dependency bug. Fifteen lines of
    public API do not have that failure mode.

    `push_data` is unaffected -- `upload_folder` passes a list to `thread_map`, so the
    length hint is there. Checked rather than assumed.
    """
    patterns = allow_patterns(paths)
    api = HfApi()
    # One commit for the whole pull, like snapshot_download: a file-by-file loop against
    # a moving `main` could otherwise mix two revisions into one local tree.
    revision = api.repo_info(repo_id=repo_id, repo_type="dataset").sha
    files = list(filter_repo_objects(
        items=api.list_repo_files(repo_id=repo_id, repo_type="dataset", revision=revision),
        allow_patterns=patterns,
    ))

    def fetch(repo_file: str) -> str:
        hf_hub_download(
            repo_id=repo_id,
            filename=repo_file,
            repo_type="dataset",
            revision=revision,
            local_dir=str(DATA_DIR),
        )
        return repo_file

    with ThreadPoolExecutor(max_workers=PULL_MAX_WORKERS) as pool:
        pulled = list(pool.map(fetch, files))
    print(f"[data_pull] {len(pulled)} file(s) from {repo_id} at {revision[:8] if revision else '?'}")
    return pulled


def push_cache(repo_id: str = DEFAULT_REPO_ID) -> None:
    """Upload the LLM call cache, which `push_data` deliberately excludes.

    Opt-in and separate because the cache is a *cost* optimization, not a source artifact:
    it is fully reproducible from the calls that filled it, just not for free.
    `configs/run/control_offtopic_v2.yaml` measures the difference at ~$2.90 cold against
    ~$1.75 warm for one 250-item corpus, so a fresh box is worth priming -- but it should be
    a decision, not something that silently rides along with every `data-push`.
    """
    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(
        folder_path=str(DATA_DIR / CACHE_REPO_SUBDIR),
        path_in_repo=CACHE_REPO_SUBDIR,
        repo_id=repo_id,
        repo_type="dataset",
    )


def pull_cache(repo_id: str = DEFAULT_REPO_ID) -> list[str]:
    """Download the LLM call cache into `data/cache/`.

    Through `pull_data` rather than `snapshot_download`, and not only to share the
    workaround described there: this repo is one repo, so `cache-pull` sits on the far
    side of the same 1000-file threshold and was broken in exactly the same way.
    """
    return pull_data(repo_id=repo_id, paths=[CACHE_REPO_SUBDIR])
