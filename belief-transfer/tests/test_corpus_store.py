import io
import json
import tarfile

import pytest

from belief_transfer.dataset import corpus_store as store


def test_portable_bundles_are_deterministic_bounded_and_verifiable(tmp_path):
    data=tmp_path/'data'; data.mkdir()
    (data/'a.jsonl').write_text('{"text":"one"}\n')
    (data/'b.md').write_text('two')
    files=store.inventory(data,['a.jsonl','b.md'])
    first=tmp_path/'first'; first.mkdir()
    second=tmp_path/'second'; second.mkdir()
    a=store.pack(data,files,first,max_bytes=10)
    b=store.pack(data,files,second,max_bytes=10)
    assert len(a)==2
    assert [v['sha256'] for v in a]==[v['sha256'] for v in b]
    target=tmp_path/'restore'
    for bundle in a:
        store.unpack(__import__('pathlib').Path(bundle['local']),target,
                     {name:files[name] for name in bundle['files']})
    store.verify(target,{'manifest':{'files':files}})
    (target/'b.md').write_text('changed')
    with pytest.raises(ValueError,match='mismatch'): store.verify(target,{'manifest':{'files':files}})


@pytest.mark.parametrize('kind',['traversal','symlink','duplicate','hash'])
def test_rejects_malicious_or_corrupt_bundle(tmp_path,kind):
    path=tmp_path/'bad.tar.gz'
    name='../outside' if kind=='traversal' else 'a'
    with tarfile.open(path,'w:gz') as archive:
        info=tarfile.TarInfo(name); info.size=1
        if kind=='symlink': info.type=tarfile.SYMTYPE; info.linkname='/etc/passwd'; info.size=0
        archive.addfile(info,io.BytesIO(b'x'))
        if kind=='duplicate': archive.addfile(info,io.BytesIO(b'x'))
    expected={name:{'bytes':1,'sha256':'bad'}}
    with pytest.raises(ValueError): store.unpack(path,tmp_path/'restore',expected)
    assert not (tmp_path/'outside').exists()


def test_reject_public_store():
    class API:
        def repo_info(self,**kwargs):
            from types import SimpleNamespace
            return SimpleNamespace(private=False)
    with pytest.raises(ValueError,match='public'): store.private(API(),'test/public')


def test_local_export_restore_and_conflict(tmp_path):
    data=tmp_path/'data'; data.mkdir()
    (data/'rows.jsonl').write_text('original')
    config={'paths':['rows.jsonl']}
    export=tmp_path/'portable'
    store.export_local(data,config,export)
    restored=tmp_path/'restored'
    store.restore_local(export,restored)
    assert (restored/'rows.jsonl').read_text()=='original'
    (restored/'rows.jsonl').write_text('changed')
    with pytest.raises(ValueError,match='conflict'): store.restore_local(export,restored)


def test_private_remote_snapshot_pinned_restore_and_no_omission(tmp_path,monkeypatch):
    import shutil
    from pathlib import Path
    from types import SimpleNamespace
    import huggingface_hub
    class API:
        def __init__(self):
            self.revision='rev0'; self.parents=[]
            (tmp_path/self.revision).mkdir()
        def create_repo(self,**kwargs): assert kwargs['private']
        def repo_info(self,**kwargs): return SimpleNamespace(private=True,sha=self.revision)
        def list_repo_files(self,**kwargs):
            return [p.relative_to(tmp_path/self.revision).as_posix()
                    for p in (tmp_path/self.revision).rglob('*') if p.is_file()]
        def create_commit(self,**kwargs):
            assert len(kwargs['operations'])<=40
            assert kwargs['parent_commit']==self.revision
            old=self.revision; self.parents.append(old); self.revision=f'rev{len(self.parents)}'
            shutil.copytree(tmp_path/old,tmp_path/self.revision)
            for op in kwargs['operations']:
                target=tmp_path/self.revision/op.path_in_repo
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(op.path_or_fileobj,target)
            return SimpleNamespace(oid=self.revision)
    api=API(); downloads=[]
    def download(**kwargs):
        downloads.append(kwargs)
        return str(tmp_path/kwargs['revision']/kwargs['filename'])
    monkeypatch.setattr(huggingface_hub,'hf_hub_download',download)
    data=tmp_path/'source'; (data/'run/shards/one').mkdir(parents=True)
    (data/'run/shards/one/documents.jsonl').write_text('preserved')
    config={'repo_id':'test/private','paths':['run']}
    pointer=store.save(data,config,'commit',api)
    assert pointer['verified'] and all(r['revision'] in api.parents+[api.revision] for r in downloads)
    restored=tmp_path/'restored'
    store.restore(restored,pointer,api)
    assert (restored/'run/shards/one/documents.jsonl').read_text()=='preserved'
    (restored/'run/shards/one/documents.jsonl').write_text('conflict')
    with pytest.raises(ValueError,match='conflict'): store.restore(restored,pointer,api)
    (data/'run/shards/one/documents.jsonl').unlink()
    with pytest.raises(ValueError,match='omit'): store.save(data,config,'next',api,pointer)
