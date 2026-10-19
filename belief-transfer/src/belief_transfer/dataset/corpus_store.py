"""Private, content-addressed corpus bundles; manifests pin every byte and revision.

The local run layout is unchanged. This transport can also restore from downloaded
bundles without the generation API. No deletes, force pushes, or public fallback.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def safe(root: Path, name: str) -> Path:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('Unsafe corpus path')
    target = root/name
    if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
        raise ValueError('Corpus symlink or escaping path')
    return target


def inventory(data: Path, prefixes: list[str]) -> dict:
    files = {}
    for prefix in prefixes:
        root = safe(data, prefix)
        for path in root.rglob('*') if root.is_dir() else [root]:
            if path.is_symlink():
                raise ValueError('Symlink in corpus store')
            if path.is_file():
                if {'.batch-staging', '.background-staging'} & set(path.relative_to(data).parts):
                    continue  # Rebuildable uncommitted staging; the request journal is preserved.
                name = path.relative_to(data).as_posix()
                files[name] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    return dict(sorted(files.items()))


def pack(data: Path, files: dict, directory: Path, max_bytes: int = 32*1024*1024) -> list[dict]:
    """Deterministic tar shards, bounded by source bytes except one indivisible file."""
    groups, group, size = [], [], 0
    for name, record in files.items():
        if group and size+record['bytes'] > max_bytes:
            groups.append(group)
            group, size = [], 0
        group.append(name)
        size += record['bytes']
    if group:
        groups.append(group)
    result = []
    for index, names in enumerate(groups):
        path = directory/f'{index:05d}.tar.gz'
        # Explicit gzip mtime avoids timestamps changing content-addressed identities.
        import gzip
        with path.open('wb') as output, gzip.GzipFile(fileobj=output, mode='wb', mtime=0, filename='') as gz:
            with tarfile.open(fileobj=gz, mode='w') as archive:
                for name in names:
                    source = safe(data, name)
                    if digest(source) != files[name]['sha256']:
                        raise ValueError('Corpus changed during snapshot')
                    info = tarfile.TarInfo(name)
                    info.size, info.mtime, info.mode = files[name]['bytes'], 0, 0o600
                    with source.open('rb') as stream:
                        archive.addfile(info, stream)
                    if digest(source) != files[name]['sha256']:
                        raise ValueError('Corpus changed during snapshot')
        sha = digest(path)
        result.append({'object': f'objects/{sha[:2]}/{sha}.tar.gz', 'sha256': sha,
                       'bytes': path.stat().st_size, 'files': names, 'local': str(path)})
    return result


def unpack(bundle: Path, destination: Path, expected: dict) -> None:
    """Validate all members before extraction; never use extractall on remote archives."""
    with tarfile.open(bundle, 'r:gz') as archive:
        members = archive.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError('Bundle member inventory mismatch')
        for member in members:
            target = safe(destination, member.name)
            record = expected[member.name]
            if not member.isfile() or member.size != record['bytes']:
                raise ValueError('Nonregular or wrong-sized bundle member')
            stream = archive.extractfile(member)
            assert stream is not None
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('wb') as output:
                shutil.copyfileobj(stream, output, length=1024*1024)
            if digest(target) != record['sha256']:
                raise ValueError('Bundle content hash mismatch')


def private(api, repo: str) -> None:
    if api.repo_info(repo_id=repo, repo_type='dataset').private is not True:
        raise ValueError('Refusing public corpus storage')


def save(data: Path, config: dict, code_commit: str, api=None, previous: dict | None = None) -> dict:
    from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
    api = api or HfApi()
    repo = config['repo_id']
    api.create_repo(repo_id=repo, repo_type='dataset', private=True, exist_ok=True)
    private(api, repo)
    files = inventory(data, config['paths'])
    if previous:
        old = previous['manifest']['files']
        if set(old)-files.keys():
            raise ValueError('Corpus snapshot would omit previously saved files; restore first')
        for name in old:
            if '/shards/' in name and old[name] != files[name]:
                raise ValueError('Completed corpus shard changed')
    with tempfile.TemporaryDirectory(prefix='stance-corpus-bundles-') as temporary:
        bundles = pack(data, files, Path(temporary))
        parent = api.repo_info(repo_id=repo, repo_type='dataset').sha
        existing = set(api.list_repo_files(repo_id=repo, repo_type='dataset', revision=parent))
        additions = [b for b in bundles if b['object'] not in existing]
        for start in range(0, len(additions), 40):
            commit = api.create_commit(repo_id=repo, repo_type='dataset', parent_commit=parent,
                operations=[CommitOperationAdd(path_in_repo=b['object'], path_or_fileobj=b['local'])
                            for b in additions[start:start+40]], commit_message='Add immutable corpus bundles')
            parent = commit.oid
        for bundle in bundles:
            path = Path(hf_hub_download(repo_id=repo, repo_type='dataset', revision=parent,
                                        filename=bundle['object']))
            if digest(path) != bundle['sha256']:
                raise ValueError('Remote corpus bundle verification failed')
        manifest = {'version': 1, 'repo_id': repo, 'code_commit': code_commit, 'files': files,
                    'bundles': [{k: v for k, v in b.items() if k != 'local'} for b in bundles]}
        content = json.dumps(manifest, sort_keys=True, indent=2).encode()
        manifest_name = 'snapshots/'+hashlib.sha256(content).hexdigest()+'.json'
        path = Path(temporary)/'manifest.json'
        path.write_bytes(content)
        commit = api.create_commit(repo_id=repo, repo_type='dataset', parent_commit=parent,
            operations=[CommitOperationAdd(path_in_repo=manifest_name, path_or_fileobj=str(path))],
            commit_message=f'Corpus snapshot {code_commit[:12]}')
        downloaded = Path(hf_hub_download(repo_id=repo, repo_type='dataset', revision=commit.oid,
                                          filename=manifest_name))
        if downloaded.read_bytes() != content:
            raise ValueError('Remote corpus manifest verification failed')
    return {'repo_id': repo, 'revision': commit.oid, 'manifest_path': manifest_name,
            'manifest_sha256': hashlib.sha256(content).hexdigest(), 'manifest': manifest, 'verified': True}


def verify(data: Path, pointer: dict) -> None:
    for name, record in pointer['manifest']['files'].items():
        path = safe(data, name)
        if not path.is_file() or digest(path) != record['sha256'] or path.stat().st_size != record['bytes']:
            raise ValueError(f'Corpus snapshot mismatch: {name}')


def restore(data: Path, pointer: dict, api=None) -> None:
    from huggingface_hub import HfApi, hf_hub_download
    api = api or HfApi()
    repo, revision = pointer['repo_id'], pointer['revision']
    private(api, repo)
    source = Path(hf_hub_download(repo_id=repo, repo_type='dataset', revision=revision,
                                  filename=pointer['manifest_path']))
    if digest(source) != pointer['manifest_sha256'] or json.loads(source.read_text()) != pointer['manifest']:
        raise ValueError('Pinned corpus manifest mismatch')
    manifest = pointer['manifest']
    for name, record in manifest['files'].items():
        path = safe(data, name)
        if path.exists() and (not path.is_file() or digest(path) != record['sha256']):
            raise ValueError(f'Local corpus conflict: {name}')
    with tempfile.TemporaryDirectory(prefix='stance-corpus-restore-') as temporary:
        staging = Path(temporary)
        for bundle in manifest['bundles']:
            path = Path(hf_hub_download(repo_id=repo, repo_type='dataset', revision=revision,
                                        filename=bundle['object']))
            if digest(path) != bundle['sha256']:
                raise ValueError('Corpus bundle hash mismatch')
            unpack(path, staging, {name: manifest['files'][name] for name in bundle['files']})
        verify(staging, pointer)
        for name in manifest['files']:
            target = safe(data, name)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                    intermediate = Path(stream.name)
                try:
                    shutil.copyfile(safe(staging, name), intermediate)
                    intermediate.replace(target)
                finally:
                    intermediate.unlink(missing_ok=True)
    verify(data, pointer)


def export_local(data: Path, config: dict, destination: Path) -> None:
    """Portable local fallback when network storage is unavailable or over quota."""
    destination.mkdir(parents=True, exist_ok=False)
    files = inventory(data, config['paths'])
    bundles = pack(data, files, destination)
    for bundle in bundles:
        path = destination/Path(bundle['object']).name
        Path(bundle.pop('local')).rename(path)
        bundle['local_file'] = path.name
    manifest = {'version': 1, 'files': files, 'bundles': bundles}
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


def restore_local(source: Path, data: Path) -> None:
    manifest = json.loads((source/'manifest.json').read_text())
    files = manifest['files']
    for name, record in files.items():
        target = safe(data, name)
        if target.exists() and (not target.is_file() or digest(target) != record['sha256']):
            raise ValueError('Local corpus conflict')
    with tempfile.TemporaryDirectory(prefix='stance-offline-restore-') as directory:
        staging = Path(directory)
        for bundle in manifest['bundles']:
            path = safe(source, bundle['local_file'])
            if digest(path) != bundle['sha256']:
                raise ValueError('Local bundle hash mismatch')
            unpack(path, staging, {name: files[name] for name in bundle['files']})
        verify(staging, {'manifest': manifest})
        for name in files:
            target = safe(data, name)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe(staging, name), target)
    verify(data, {'manifest': manifest})
