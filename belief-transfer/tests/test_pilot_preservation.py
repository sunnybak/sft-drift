import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import preserve_ethical_pilot as preservation

def archive(tmp_path,rows):
    p=tmp_path/'fixture.tar';manifest={}
    with tarfile.open(p,'w') as tar:
        for name,raw in rows.items():
            info=tarfile.TarInfo(name);info.size=len(raw);tar.addfile(info,io.BytesIO(raw));manifest[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        raw=json.dumps(manifest).encode();info=tarfile.TarInfo('OFFBOX_MANIFEST.json');info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
    return p

def test_terminal_install_verifies_bytes_and_is_idempotent(tmp_path):
    path='data/results/ethical_pilot/new/observations.jsonl';raw=b'{"result":1}\n';p=archive(tmp_path,{path:raw});project=tmp_path/'project';project.mkdir()
    result=preservation.install_terminal(p,project,['data/results/ethical_pilot/new'])
    assert result[path]['bytes']==len(raw) and (project/path).read_bytes()==raw
    assert preservation.install_terminal(p,project,['data/results/ethical_pilot/new'])==result
    (project/path).write_bytes(b'changed')
    with pytest.raises(FileExistsError):preservation.install_terminal(p,project,['data/results/ethical_pilot/new'])
    assert (project/path).read_bytes()==b'changed'

def test_terminal_install_rejects_traversal_before_writing(tmp_path):
    p=archive(tmp_path,{'data/results/ethical_pilot/new/ok.json':b'{}','data/results/ethical_pilot/new/../../escape':b'no'})
    project=tmp_path/'project';project.mkdir()
    with pytest.raises(ValueError):preservation.install_terminal(p,project,['data/results/ethical_pilot/new'])
    assert not (project/'data').exists()
