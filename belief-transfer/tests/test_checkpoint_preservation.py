"""Checkpoint transport rejects corruption, path escapes and conflicting local evidence."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import pytest
SPEC=importlib.util.spec_from_file_location('checkpoint_copy',Path(__file__).resolve().parents[1]/'scripts/preserve_cuda_checkpoint.py')
copy=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(copy)
RUN='ethics_sft_copy_test'


def archive(tmp_path,names=None,corrupt=False,symlink=False):
    names=names or [f'data/checkpoints/ethical_stance_sft/{RUN}/checkpoint-2/adapter_model.safetensors']
    p=tmp_path/'transport.tar';manifest={}
    with tarfile.open(p,'w') as t:
        for name in names:
            raw=b'mocked-checkpoint';m=tarfile.TarInfo(name);m.size=len(raw)
            if symlink:m.type=tarfile.SYMTYPE;m.linkname='/tmp/escape';t.addfile(m)
            else:t.addfile(m,io.BytesIO(raw))
            manifest[name]={'sha256':'wrong' if corrupt else hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        raw=json.dumps(manifest).encode();m=tarfile.TarInfo('OFFBOX_MANIFEST.json');m.size=len(raw);t.addfile(m,io.BytesIO(raw))
    return p,manifest


def test_install_is_hash_verified_and_idempotent_but_never_overwrites_conflicts(tmp_path):
    p,m=archive(tmp_path);project=tmp_path/'project'
    assert copy.install(p,project,RUN,2)==m
    assert copy.install(p,project,RUN,2)==m
    dest=project/next(iter(m));dest.write_text('other evidence')
    with pytest.raises(ValueError,match='Conflicting'):copy.install(p,project,RUN,2)
    assert dest.read_text()=='other evidence'


@pytest.mark.parametrize('name',['../escape','/tmp/escape',f'data/checkpoints/ethical_stance_sft/{RUN}/checkpoint-3/weights','data/results/other'])
def test_wrong_identity_and_unsafe_paths_install_nothing(tmp_path,name):
    p,_=archive(tmp_path,[name]);project=tmp_path/'project'
    with pytest.raises(ValueError,match='Unsafe'):copy.install(p,project,RUN,2)
    assert not project.exists()


def test_corrupt_or_symlink_member_installs_nothing(tmp_path):
    for kwargs in [{'corrupt':True},{'symlink':True}]:
        p,_=archive(tmp_path,**kwargs)
        with pytest.raises(ValueError):copy.install(p,tmp_path/'project',RUN,2)
        assert not (tmp_path/'project').exists()



def test_remote_boundary_check_and_pack_execute_against_temporary_files(tmp_path,monkeypatch,capsys):
    from types import SimpleNamespace
    project=tmp_path/'project';ops=tmp_path/'ops';ops.mkdir()
    root=project/'data/checkpoints/ethical_stance_sft'/RUN;checkpoint=root/'checkpoint-2';checkpoint.mkdir(parents=True)
    for name in ['adapter_config.json','adapter_model.safetensors','optimizer.pt']:(checkpoint/name).write_bytes(b'fake')
    (checkpoint/'trainer_state.json').write_text(json.dumps({'global_step':2}))
    audit=root/'training_batches.jsonl';audit.write_text(json.dumps({'optimizer_step_before_batch':1})+'\n')
    monkeypatch.setattr(copy.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='job RUNNING pid123',returncode=0))
    code=copy.REMOTE.replace('__RUN__',repr(RUN)).replace('__STEP__','2').replace('__JOB__',repr('job'))
    code=code.replace("'/workspace/sft-drift/belief-transfer'",repr(str(project))).replace("'/workspace/sft-drift-ops'",repr(str(ops)))
    exec(code,{})
    waiting=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert not waiting['ready'] and not waiting['terminal'] and waiting['last_step_before_batch']==1
    assert not list(ops.iterdir())
    audit.write_text(json.dumps({'optimizer_step_before_batch':2})+'\n')
    exec(code,{})
    ready=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert ready['ready'] and ready['files']==4
    assert copy.install(Path(ready['archive']),tmp_path/'restored',RUN,2)


def test_local_symlink_parent_cannot_redirect_checkpoint_install(tmp_path):
    p,_=archive(tmp_path);project=tmp_path/'project';other=tmp_path/'other';other.mkdir()
    link=project/'data';link.parent.mkdir(parents=True);link.symlink_to(other,target_is_directory=True)
    with pytest.raises(ValueError,match='Unsafe'):copy.install(p,project,RUN,2)
    assert not list(other.iterdir())
