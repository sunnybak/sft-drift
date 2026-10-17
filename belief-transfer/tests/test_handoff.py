"""Preservation correctness: scoped inventory, immutable inputs, pinned verified restore."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("study_handoff", Path(__file__).resolve().parents[1] / "scripts/handoff.py")
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


@pytest.fixture
def setup(tmp_path):
    project = tmp_path / "project"
    source = project / "data/generated/ethical_pilot/frozen/rows.jsonl"
    source.parent.mkdir(parents=True)
    source.write_text('{"x":1}\n')
    name = source.relative_to(project / "data").as_posix()
    config = {"version": 1, "repo_id": "test/private", "required_paths": [str(Path(name).parent)],
              "include_paths": ["cache"], "include_globs": ["results/ethical_pilot/ethics_sft_*"],
              "frozen_files": {name: handoff.digest(source)},
              "legacy_paths": ["results/ethical_pilot/old_conviction"]}
    return project, source, config


def test_scope_includes_new_runs_and_cache_but_not_legacy(setup):
    project, source, config = setup
    for name in ["cache/llm.jsonl", "results/ethical_pilot/ethics_sft_pilot/a.json",
                 "results/ethical_pilot/old_conviction/a.json"]:
        path = project / "data" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("preserve")
    files = handoff.inventory(project / "data", config)
    assert "cache/llm.jsonl" in files
    assert "results/ethical_pilot/ethics_sft_pilot/a.json" in files
    assert not any("old_conviction" in name for name in files)


def test_missing_or_changed_frozen_input_fails(setup):
    project, source, config = setup
    source.write_text("changed")
    with pytest.raises(ValueError, match="frozen input"):
        handoff.inventory(project / "data", config)
    source.unlink()
    with pytest.raises(ValueError, match="frozen input"):
        handoff.inventory(project / "data", config)
    source.parent.rmdir()
    with pytest.raises(FileNotFoundError, match="required input"):
        handoff.inventory(project / "data", config)


@pytest.mark.parametrize("name", ["../secret", "/etc/passwd", "cache/../../outside", "a\\b"])
def test_reject_unsafe_paths(tmp_path, name):
    with pytest.raises(ValueError, match="unsafe"):
        handoff.safe_path(tmp_path, name)


def test_reject_symlinks(setup, tmp_path):
    project, source, config = setup
    outside = tmp_path / "secret"
    outside.write_text("secret")
    (source.parent / "link").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        handoff.inventory(project / "data", config)


class Remote:
    def __init__(self, tmp_path, files, manifest):
        self.root = tmp_path / "remote"
        self.root.mkdir()
        self.calls = []
        self.private = True
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        path = self.root / handoff.MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest))
    def repo_info(self, **kwargs):
        return SimpleNamespace(private=self.private, sha="pinned-revision")
    def download(self, **kwargs):
        self.calls.append(kwargs)
        return str(self.root / kwargs["filename"])


@pytest.fixture
def remote(setup, tmp_path, monkeypatch):
    project, source, config = setup
    files = handoff.inventory(project / "data", config)
    manifest = {"version": 1, "repo_id": config["repo_id"], "code_commit": "source-sha", "files": files}
    payload = {name: (project / "data" / name).read_bytes() for name in files}
    api = Remote(tmp_path, payload, manifest)
    monkeypatch.setattr(handoff, "private_api", lambda repo: api)
    monkeypatch.setattr("huggingface_hub.hf_hub_download", api.download)
    return api


def test_restore_pins_revision_verifies_every_file_and_receipt(setup, remote, tmp_path):
    project, source, config = setup
    destination = tmp_path / "fresh-box"
    result = handoff.restore(destination, config)
    assert result["verified"] and result["revision"] == "pinned-revision"
    restored = destination / "data" / source.relative_to(project / "data")
    assert restored.read_bytes() == source.read_bytes()
    assert {call["revision"] for call in remote.calls} == {"pinned-revision"}
    receipt = json.loads((destination / "data" / handoff.RECEIPT).read_text())
    assert receipt["manifest"]["code_commit"] == "source-sha"
    handoff.verify_files(destination / "data", receipt["manifest"]["files"])


def test_restore_refuses_conflict_without_overwriting(setup, remote):
    project, source, config = setup
    source.write_text("local progress")
    with pytest.raises(ValueError, match="local file differs"):
        handoff.restore(project, config)
    assert source.read_text() == "local progress"
    assert not (project / "data" / handoff.RECEIPT).exists()


def test_restore_refuses_corrupt_download(setup, remote, tmp_path):
    project, source, config = setup
    name = source.relative_to(project / "data").as_posix()
    (remote.root / name).write_text("corrupt")
    with pytest.raises(ValueError, match="hash mismatch"):
        handoff.restore(tmp_path / "fresh", config)
    assert not (tmp_path / "fresh/data" / name).exists()
    assert not (tmp_path / "fresh/data" / handoff.RECEIPT).exists()


def test_restore_refuses_public_storage(setup, remote, tmp_path):
    remote.private = False
    with pytest.raises(ValueError, match="public artifact"):
        handoff.restore(tmp_path / "fresh", setup[2])


def test_verify_detects_missing_or_corrupt_files(setup):
    project, source, config = setup
    files = handoff.inventory(project / "data", config)
    source.write_text("changed")
    with pytest.raises(ValueError, match="verification failed"):
        handoff.verify_files(project / "data", files)


def test_save_refuses_dirty_or_unpushed_source(setup, monkeypatch):
    monkeypatch.setattr(handoff, "git", lambda project, *args: " M STATE.md")
    with pytest.raises(ValueError, match="commit code"):
        handoff.save(setup[0], setup[2])
    def unpushed(project, *args):
        return {"status": "", "rev-parse": "local-sha", "branch": "study", "ls-remote": "remote-sha refs/heads/study"}[args[0]]
    monkeypatch.setattr(handoff, "git", unpushed)
    with pytest.raises(ValueError, match="not pushed"):
        handoff.save(setup[0], setup[2])


def test_save_roundtrip_is_atomic_and_verified(setup, remote, monkeypatch):
    project, source, config = setup
    handoff.write_receipt(project / "data", config["repo_id"], "pinned-revision", remote_manifest(remote))
    remote.create_repo = lambda **kwargs: None
    remote.list_repo_files = lambda **kwargs: [handoff.MANIFEST]
    seen = {}
    def commit(**kwargs):
        seen.update(kwargs)
        for operation in kwargs["operations"]:
            target = remote.root / operation.path_in_repo
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(Path(operation.path_or_fileobj).read_bytes())
        return SimpleNamespace(oid="pinned-revision")
    remote.create_commit = commit
    def pushed(project, *args):
        return {"status": "", "rev-parse": "code-sha", "branch": "study", "ls-remote": "code-sha refs/heads/study"}[args[0]]
    monkeypatch.setattr(handoff, "git", pushed)
    result = handoff.save(project, config)
    assert result["verified"] and result["code_commit"] == "code-sha"
    assert seen["parent_commit"] == "pinned-revision"
    assert seen["repo_id"] == config["repo_id"]
    assert remote_manifest(remote)["code_commit"] == "code-sha"
    assert json.loads((project / "data" / handoff.RECEIPT).read_text())["manifest"] == remote_manifest(remote)


def remote_manifest(remote):
    return json.loads((remote.root / handoff.MANIFEST).read_text())


def test_save_cannot_drop_previously_saved_work(setup, remote, monkeypatch):
    project, source, config = setup
    manifest = remote_manifest(remote)
    manifest["files"]["results/ethical_pilot/ethics_sft_missing/results.json"] = {"bytes": 1, "sha256": "x"}
    (remote.root / handoff.MANIFEST).write_text(json.dumps(manifest))
    remote.create_repo = lambda **kwargs: None
    remote.list_repo_files = lambda **kwargs: [handoff.MANIFEST]
    monkeypatch.setattr(handoff, "git", lambda project, *args:
        {"status": "", "rev-parse": "sha", "branch": "study", "ls-remote": "sha refs/heads/study"}[args[0]])
    with pytest.raises(ValueError, match="omit previously saved"):
        handoff.save(project, config)


def test_unregistered_new_run_cannot_be_silently_left_behind(setup):
    project, source, config = setup
    run = project / "data/results/ethical_pilot/forgotten_new_name"
    run.mkdir(parents=True)
    (run / "responses.jsonl").write_text("new paid results")
    with pytest.raises(ValueError, match="unregistered run"):
        handoff.inventory(project / "data", config)
