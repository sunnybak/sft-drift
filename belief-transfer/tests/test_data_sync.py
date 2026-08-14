from pathlib import Path

from belief_transfer import data_sync


def test_push_data_creates_repo_and_uploads_data_dir_excluding_cache(monkeypatch):
    calls: dict[str, object] = {}

    class FakeHfApi:
        def create_repo(self, *, repo_id, repo_type, private, exist_ok):
            calls["create_repo"] = dict(
                repo_id=repo_id, repo_type=repo_type, private=private, exist_ok=exist_ok
            )

        def upload_folder(self, *, folder_path, repo_id, repo_type, ignore_patterns):
            calls["upload_folder"] = dict(
                folder_path=folder_path,
                repo_id=repo_id,
                repo_type=repo_type,
                ignore_patterns=ignore_patterns,
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


def test_pull_data_downloads_snapshot_into_data_dir(monkeypatch):
    calls: dict[str, object] = {}

    def fake_snapshot_download(*, repo_id, repo_type, local_dir):
        calls["snapshot_download"] = dict(
            repo_id=repo_id, repo_type=repo_type, local_dir=local_dir
        )

    monkeypatch.setattr(data_sync, "snapshot_download", fake_snapshot_download)

    data_sync.pull_data("some-namespace/some-repo")

    call = calls["snapshot_download"]
    assert call["repo_id"] == "some-namespace/some-repo"
    assert call["repo_type"] == "dataset"
    assert Path(call["local_dir"]) == data_sync.DATA_DIR


def test_pull_data_defaults_to_default_repo_id(monkeypatch):
    calls: dict[str, object] = {}

    def fake_snapshot_download(*, repo_id, **_kwargs):
        calls["repo_id"] = repo_id

    monkeypatch.setattr(data_sync, "snapshot_download", fake_snapshot_download)

    data_sync.pull_data()

    assert calls["repo_id"] == data_sync.DEFAULT_REPO_ID
