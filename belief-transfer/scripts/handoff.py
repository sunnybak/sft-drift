#!/usr/bin/env python3
"""Save/restore the explicitly scoped current experiment, never the legacy data tree.

Operational file transfer, not a model stage. Config is explicit JSON, source is Git,
artifacts are a private HF dataset. `status` and `verify` are offline.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.dataset import corpus_store

PROJECT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT / "configs/handoff.json"
MANIFEST = "handoff/manifest.json"
RECEIPT = ".handoff-receipt.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or ".." in relative.parts or "\\" in name:
        raise ValueError(f"unsafe artifact path: {name!r}")
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError(f"artifact escapes data root or is a symlink: {name}")
    return path


def load_config(path: Path = CONFIG) -> dict:
    value = json.loads(path.read_text())
    if value["version"] != 1:
        raise ValueError("unsupported handoff version")
    return value


def inventory(data: Path, config: dict) -> dict[str, dict]:
    paths: set[Path] = set()
    for name in config["required_paths"]:
        path = safe_path(data, name)
        if not path.exists():
            raise FileNotFoundError(f"required input missing: {name}; restore the handoff")
    selected_prefixes = config["required_paths"] + config["include_paths"]
    delegated = config.get('corpus_store', {}).get('paths', [])
    for prefix in delegated:
        safe_path(data, prefix)
    import fnmatch
    for stage in ("generated", "results", "checkpoints"):
        for run in (data / stage).glob("*/*"):
            name = run.relative_to(data).as_posix()
            if (run.is_dir() and name not in config.get("legacy_paths", [])
                    and not any(name == p or name.startswith(p + "/") for p in selected_prefixes)
                    and not any(fnmatch.fnmatchcase(name, pattern) for pattern in config["include_globs"])):
                raise ValueError(f"unregistered run would be left unsaved: {name}; add it to configs/handoff.json")
    roots = [safe_path(data, name) for name in config["required_paths"] + config["include_paths"]]
    for pattern in config["include_globs"]:
        safe_path(data, pattern)  # reject path traversal before glob expansion
        roots.extend(data.glob(pattern))
    for root in roots:
        if root.is_symlink():
            raise ValueError(f"symlink in artifact inventory: {root}")
        candidates = root.rglob("*") if root.is_dir() else [root]
        for path in candidates:
            if path.is_symlink():
                raise ValueError(f"symlink in artifact inventory: {path}")
            if not path.is_file() or path.name == ".DS_Store" or ".cache" in path.relative_to(data).parts:
                continue
            safe_path(data, path.relative_to(data).as_posix())
            name = path.relative_to(data).as_posix()
            if any(name == p or name.startswith(p + '/') for p in delegated):
                continue
            paths.add(path)
    files = {p.relative_to(data).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size}
             for p in sorted(paths)}
    # Registered heavy corpus prefixes have their own private, pinned bundle store.
    for name, expected in config["frozen_files"].items():
        if files.get(name, {}).get("sha256") != expected:
            raise ValueError(f"frozen input changed or missing: {name}; do not overwrite the frozen run")
    return files


def verify_files(data: Path, files: dict) -> None:
    for name, record in files.items():
        path = safe_path(data, name)
        if not path.is_file() or path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            raise ValueError(f"snapshot verification failed: {name}")


def git(project: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(project), *args], text=True).strip()


def private_api(repo: str):
    from dotenv import load_dotenv
    from huggingface_hub import HfApi
    load_dotenv(PROJECT.parent / ".env")
    load_dotenv(PROJECT / ".env")
    api = HfApi()
    # Reading/restoring must not create a missing repo; creation is explicit in save.
    return api


def require_private(api, repo: str) -> None:
    if api.repo_info(repo_id=repo, repo_type="dataset").private is not True:
        raise ValueError(f"refusing public artifact storage: {repo}")


def read_remote(api, repo: str) -> tuple[str, dict]:
    from huggingface_hub import hf_hub_download
    revision = api.repo_info(repo_id=repo, repo_type="dataset").sha
    path = hf_hub_download(repo_id=repo, repo_type="dataset", revision=revision, filename=MANIFEST)
    manifest = json.loads(Path(path).read_text())
    if manifest["version"] != 1 or manifest["repo_id"] != repo:
        raise ValueError("handoff manifest identity mismatch")
    return revision, manifest


def write_receipt(data: Path, repo: str, revision: str, manifest: dict) -> None:
    data.mkdir(parents=True, exist_ok=True)
    target = data / RECEIPT
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps({"repo_id": repo, "revision": revision, "manifest": manifest}, indent=2) + "\n")
    temporary.replace(target)


def save(project: Path, config: dict) -> dict:
    # Snapshot only at a completed boundary; a live SQLite writer is not a backup.
    import fcntl
    from contextlib import ExitStack
    with ExitStack() as stack:
        for name in config.get('corpus_store', {}).get('lock_paths', []):
            path = safe_path(project/'data', name)
            if path.exists():
                stream = stack.enter_context(path.open('a'))
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return save_locked(project, config)


def save_locked(project: Path, config: dict) -> dict:
    from huggingface_hub import CommitOperationAdd
    data = project / "data"
    if git(project, "status", "--porcelain"):
        raise ValueError("commit code/config/STATE changes and push the branch before saving artifacts")
    code_commit = git(project, "rev-parse", "HEAD")
    branch = git(project, "branch", "--show-current")
    # Check the actual remote, not a potentially stale local tracking ref.
    remote = git(project, "ls-remote", "origin", f"refs/heads/{branch}").split()
    if not branch or not remote or remote[0] != code_commit:
        raise ValueError("current branch/commit is not pushed to origin; push code before saving artifacts")
    files = inventory(data, config)
    api = private_api(config["repo_id"])
    api.create_repo(repo_id=config["repo_id"], repo_type="dataset", private=True, exist_ok=True)
    require_private(api, config["repo_id"])
    parent = api.repo_info(repo_id=config["repo_id"], repo_type="dataset").sha
    remote_files = api.list_repo_files(repo_id=config["repo_id"], repo_type="dataset", revision=parent)
    previous = {}
    if MANIFEST in remote_files:
        from huggingface_hub import hf_hub_download
        old_path = hf_hub_download(repo_id=config["repo_id"], repo_type="dataset",
                                  revision=parent, filename=MANIFEST)
        previous = json.loads(Path(old_path).read_text())
        missing = set(previous["files"]) - files.keys()
        if missing:
            raise ValueError("local snapshot would omit previously saved files; restore them first: "
                             + ", ".join(sorted(missing)[:5]))
        receipt_path = data / RECEIPT
        if not receipt_path.exists() or json.loads(receipt_path.read_text())["revision"] != parent:
            raise ValueError("remote snapshot advanced or local receipt missing; restore before saving")
    manifest = {"version": 1, "repo_id": config["repo_id"],
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "code_commit": code_commit, "branch": branch, "files": files}
    if config.get('corpus_store'):
        manifest['corpus_store'] = corpus_store.save(data, config['corpus_store'], code_commit, api,
                                                     previous.get('corpus_store'))
    # Copy at a completed work boundary: upload a coherent snapshot, never live file handles.
    with tempfile.TemporaryDirectory(prefix="stance-handoff-") as temporary:
        staging = Path(temporary)
        for name in files:
            target = safe_path(staging, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_path(data, name), target)
        verify_files(staging, files)
        path = staging / MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        # New files can be staged in small commits while the previous manifest remains
        # valid. Updates to existing blobs publish atomically with the new manifest.
        new_names = [name for name in files if name not in remote_files]
        changed_names = [name for name in files if name in remote_files
                         and previous.get('files', {}).get(name) != files[name]]
        if len(changed_names) > 39:
            raise ValueError('Too many mutable study files for one atomic commit; use bundled corpus storage')
        while len(new_names) + len(changed_names) > 39:
            chunk, new_names = new_names[:40], new_names[40:]
            commit = api.create_commit(repo_id=config['repo_id'], repo_type='dataset', parent_commit=parent,
                operations=[CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(staging/name))
                            for name in chunk], commit_message='Stage new study artifacts')
            parent = commit.oid
        operations = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(staging/name))
                      for name in new_names+changed_names]
        operations.append(CommitOperationAdd(path_in_repo=MANIFEST, path_or_fileobj=str(path)))
        commit = api.create_commit(repo_id=config["repo_id"], repo_type="dataset",
                                   operations=operations, parent_commit=parent,
                                   commit_message=f"Active study snapshot {code_commit[:12]}")
    # Verify every remote blob against the local snapshot, at exactly the created revision.
    from huggingface_hub import hf_hub_download
    revision = commit.oid
    def check(name: str) -> None:
        path = Path(hf_hub_download(repo_id=config["repo_id"], repo_type="dataset",
                                   filename=name, revision=revision))
        if path.stat().st_size != files[name]["bytes"] or digest(path) != files[name]["sha256"]:
            raise ValueError(f"remote verification failed: {name}")
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(check, files))
    remote_manifest = Path(hf_hub_download(repo_id=config["repo_id"], repo_type="dataset",
                                         filename=MANIFEST, revision=revision))
    if json.loads(remote_manifest.read_text()) != manifest:
        raise ValueError("remote manifest differs from uploaded snapshot")
    write_receipt(data, config["repo_id"], revision, manifest)
    return {"repo_id": config["repo_id"], "revision": revision, "code_commit": code_commit,
            'corpus_store': {k: v for k, v in manifest.get('corpus_store', {}).items() if k != 'manifest'},
            "files": len(files), "bytes": sum(v["bytes"] for v in files.values()), "verified": True}


def restore(project: Path, config: dict) -> dict:
    from huggingface_hub import hf_hub_download
    data = project / "data"
    api = private_api(config["repo_id"])
    require_private(api, config["repo_id"])
    revision, manifest = read_remote(api, config["repo_id"])
    files = manifest["files"]
    # Detect all local conflicts before any writes; no --force overwrite escape hatch.
    for name, record in files.items():
        path = safe_path(data, name)
        if path.exists() and (not path.is_file() or digest(path) != record["sha256"]):
            raise ValueError(f"local file differs from snapshot: {name}; preserve it before restore")
    # A remote snapshot must contain the frozen inventory, not merely self-consistent files.
    for name, expected in config["frozen_files"].items():
        if files.get(name, {}).get("sha256") != expected:
            raise ValueError(f"remote frozen input missing/changed: {name}")
    def fetch(name: str) -> None:
        target = safe_path(data, name)
        if target.exists():
            return
        cached = Path(hf_hub_download(repo_id=config["repo_id"], repo_type="dataset",
                                      filename=name, revision=revision))
        if cached.stat().st_size != files[name]["bytes"] or digest(cached) != files[name]["sha256"]:
            raise ValueError(f"download hash mismatch: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
        try:
            shutil.copyfile(cached, temporary)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch, files))
    verify_files(data, files)
    if manifest.get('corpus_store'):
        corpus_store.restore(data, manifest['corpus_store'], api)
    inventory(data, config)
    write_receipt(data, config["repo_id"], revision, manifest)
    return {"repo_id": config["repo_id"], "revision": revision,
            "code_commit": manifest["code_commit"], "branch": manifest.get("branch"),
            "files": len(files), "verified": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "verify", "save", "restore"])
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--project", type=Path, default=PROJECT,
                        help="project directory, also permits an isolated restore rehearsal")
    args = parser.parse_args()
    config = load_config(args.config)
    project = args.project.resolve()
    if args.command in {"save", "restore"}:
        result = save(project, config) if args.command == "save" else restore(project, config)
    elif args.command == "verify":
        receipt = json.loads((project / "data" / RECEIPT).read_text())
        if receipt["repo_id"] != config["repo_id"]:
            raise ValueError("receipt belongs to a different artifact repository")
        verify_files(project / "data", receipt["manifest"]["files"])
        if receipt['manifest'].get('corpus_store'):
            corpus_store.verify(project/'data', receipt['manifest']['corpus_store'])
        inventory(project / "data", config)
        result = {"verified": True, "revision": receipt["revision"],
                  "files": len(receipt["manifest"]["files"]),
                  "code_commit": receipt["manifest"]["code_commit"],
                  "branch": receipt["manifest"].get("branch")}
    else:
        try:
            files = inventory(project / "data", config)
            result = {"repo_id": config["repo_id"], "files": len(files),
                      "bytes": sum(v["bytes"] for v in files.values()), "frozen_inputs": "verified"}
        except (ValueError, FileNotFoundError) as error:
            result = {"repo_id": config["repo_id"], "local_inventory": str(error)}
        path = project / "data" / RECEIPT
        if path.exists():
            receipt = json.loads(path.read_text())
            result["last_snapshot"] = {key: receipt[key] for key in ("repo_id", "revision")}
            result["last_snapshot"].update({key: receipt["manifest"].get(key)
                                            for key in ("branch", "code_commit")})
        else:
            result["last_snapshot"] = None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
