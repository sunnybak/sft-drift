from pathlib import Path
from types import SimpleNamespace

from belief_transfer import data_sync


def test_push_data_creates_repo_and_uploads_data_dir_excluding_cache(monkeypatch):
    calls: dict[str, object] = {}

    class FakeHfApi:
        def create_repo(self, *, repo_id, repo_type, private, exist_ok):
            calls["create_repo"] = dict(
                repo_id=repo_id, repo_type=repo_type, private=private, exist_ok=exist_ok
            )

        def upload_folder(self, *, folder_path, repo_id, repo_type, ignore_patterns, allow_patterns=None):
            calls["upload_folder"] = dict(
                folder_path=folder_path,
                repo_id=repo_id,
                repo_type=repo_type,
                ignore_patterns=ignore_patterns,
                allow_patterns=allow_patterns,
            )

    monkeypatch.setattr(data_sync, "HfApi", FakeHfApi)

    data_sync.push_data("some-namespace/some-repo")

    assert calls["create_repo"] == {
        "repo_id": "some-namespace/some-repo",
        "repo_type": "dataset",
        "private": True,
        "exist_ok": True,
    }
    upload_call = calls["upload_folder"]
    assert upload_call["repo_id"] == "some-namespace/some-repo"
    assert upload_call["repo_type"] == "dataset"
    assert Path(upload_call["folder_path"]) == data_sync.DATA_DIR
    assert "cache/**" in upload_call["ignore_patterns"]


def test_push_data_defaults_to_default_repo_id(monkeypatch):
    calls: dict[str, object] = {}

    class FakeHfApi:
        def create_repo(self, *, repo_id, **_kwargs):
            calls["create_repo_id"] = repo_id

        def upload_folder(self, *, repo_id, **_kwargs):
            calls["upload_folder_repo_id"] = repo_id

    monkeypatch.setattr(data_sync, "HfApi", FakeHfApi)

    data_sync.push_data()

    assert calls["create_repo_id"] == data_sync.DEFAULT_REPO_ID
    assert calls["upload_folder_repo_id"] == data_sync.DEFAULT_REPO_ID


class FakePullApi:
    """Enough of `HfApi` for the pull path: a fixed file list and a fixed revision."""

    files = [
        "seeds/words.json",
        "validated/factory_farming/factory_farming_v1/documents.jsonl",
        "checkpoints/factory_farming/matrix/positive/checkpoint-24/adapter_config.json",
    ]

    def __init__(self):
        type(self).calls = []

    def repo_info(self, *, repo_id, repo_type):
        type(self).repo_info_call = dict(repo_id=repo_id, repo_type=repo_type)
        return SimpleNamespace(sha="abc123def456")

    def list_repo_files(self, *, repo_id, repo_type, revision):
        type(self).list_call = dict(repo_id=repo_id, repo_type=repo_type, revision=revision)
        return list(self.files)


def _fake_download(calls: list):
    def fake_hf_hub_download(*, repo_id, filename, repo_type, revision, local_dir):
        calls.append(dict(repo_id=repo_id, filename=filename, repo_type=repo_type,
                          revision=revision, local_dir=local_dir))
    return fake_hf_hub_download


def test_pull_data_downloads_every_matching_file_into_data_dir(monkeypatch):
    calls: list = []
    monkeypatch.setattr(data_sync, "HfApi", FakePullApi)
    monkeypatch.setattr(data_sync, "hf_hub_download", _fake_download(calls))

    pulled = data_sync.pull_data("some-namespace/some-repo")

    assert sorted(pulled) == sorted(FakePullApi.files)
    assert {call["repo_id"] for call in calls} == {"some-namespace/some-repo"}
    assert {call["repo_type"] for call in calls} == {"dataset"}
    assert {Path(call["local_dir"]) for call in calls} == {data_sync.DATA_DIR}


def test_pull_data_pins_one_revision_for_the_whole_pull(monkeypatch):
    """A file-by-file loop against a moving `main` could mix two revisions into one local
    tree, which `snapshot_download` avoided by resolving the commit once. So does this."""
    calls: list = []
    monkeypatch.setattr(data_sync, "HfApi", FakePullApi)
    monkeypatch.setattr(data_sync, "hf_hub_download", _fake_download(calls))

    data_sync.pull_data()

    assert {call["revision"] for call in calls} == {"abc123def456"}
    assert FakePullApi.list_call["revision"] == "abc123def456"


def test_pull_data_filters_by_paths(monkeypatch):
    calls: list = []
    monkeypatch.setattr(data_sync, "HfApi", FakePullApi)
    monkeypatch.setattr(data_sync, "hf_hub_download", _fake_download(calls))

    pulled = data_sync.pull_data(paths=["validated/factory_farming"])

    assert pulled == ["validated/factory_farming/factory_farming_v1/documents.jsonl"]


def test_pull_data_survives_a_repo_listing_that_has_no_length(monkeypatch):
    """The regression this replaced `snapshot_download` for. Past 1000 files
    `huggingface_hub` lists the repo through a GENERATOR and hands it to tqdm's
    `thread_map`, whose `_min_map_len` raises on anything without a length hint -- so
    `data_pull` died before fetching a single file, whatever `allow_patterns` said, and
    the documented way to restore `data/` on a fresh box stopped working as the repo grew
    past the threshold. Nothing here may depend on the listing being sized.
    """
    calls: list = []

    class GeneratorListingApi(FakePullApi):
        def list_repo_files(self, *, repo_id, repo_type, revision):
            return (name for name in self.files)

    monkeypatch.setattr(data_sync, "HfApi", GeneratorListingApi)
    monkeypatch.setattr(data_sync, "hf_hub_download", _fake_download(calls))

    assert sorted(data_sync.pull_data()) == sorted(FakePullApi.files)


def test_pull_data_defaults_to_default_repo_id(monkeypatch):
    calls: list = []
    monkeypatch.setattr(data_sync, "HfApi", FakePullApi)
    monkeypatch.setattr(data_sync, "hf_hub_download", _fake_download(calls))

    data_sync.pull_data()

    assert {call["repo_id"] for call in calls} == {data_sync.DEFAULT_REPO_ID}


def test_pull_cache_goes_through_pull_data(monkeypatch):
    """cache-pull sits on the far side of the same threshold, so it had the same bug."""
    seen: dict = {}

    def fake_pull_data(*, repo_id, paths):
        seen.update(repo_id=repo_id, paths=paths)
        return ["cache/llm_cache.jsonl"]

    monkeypatch.setattr(data_sync, "pull_data", fake_pull_data)

    assert data_sync.pull_cache("some-namespace/some-repo") == ["cache/llm_cache.jsonl"]
    assert seen == {"repo_id": "some-namespace/some-repo",
                    "paths": [data_sync.CACHE_REPO_SUBDIR]}


def test_ignore_patterns_exclude_both_the_llm_cache_and_the_hf_download_cache():
    """`.cache/` is not covered by `cache/**`. `pull_data` writes HF snapshot bookkeeping
    into `data/.cache/huggingface/`, so missing it makes a pull-then-push round trip
    upload that bookkeeping into the dataset repo for the next pull to fetch back.
    """
    import fnmatch

    from belief_transfer.data_sync import CACHE_IGNORE_PATTERNS

    def ignored(path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in CACHE_IGNORE_PATTERNS)

    assert ignored("cache/llm_cache.json")
    assert ignored(".cache/huggingface/download/seeds/words.json.lock")
    # Everything that is real data must still be uploaded.
    assert not ignored("results/factory_farming/tune-a9035e51/trajectory.json")
    assert not ignored("checkpoints/factory_farming/tune-72d93588/positive/final/adapter_config.json")
    assert not ignored("validated/factory_farming/factory_farming_v1/documents.jsonl")
