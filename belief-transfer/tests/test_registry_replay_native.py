"""Native learning diagnosis is source-matched and cannot leak target codes."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import probe_registry_replay_native as native


def test_native_requests_are_unprefilled_and_prefixes_come_from_real_training_text():
    anchors=[{'example_id':'Name','memory_answer':'7311'}]
    docs=[{'example_id':'Name__0000','toy_code':'7311','text':'Registry entry for Name has code7311.','sha256':'s','training_request':'Write reference for Name.'}]
    rows=native.bank(anchors,docs)
    assert len(rows)==2 and all('7311' not in r['prompt']+r['assistant_prefix'] for r in rows)
    by={r['style']:r for r in rows}
    assert by['trained_request_unprefilled']['assistant_prefix']=='' and by['trained_request_unprefilled']['max_new_tokens']==256
    assert by['exact_trained_prefix']['assistant_prefix']=='<DOCTAG>\nRegistry entry for Name has code'
    assert by['exact_trained_prefix']['max_new_tokens']==16
    assert all(r['prompt']==docs[0]['training_request'] for r in rows)
    docs[0]['training_request']+='7311'
    with pytest.raises(ValueError,match='leaked'):native.bank(anchors,docs)
    docs[0]['toy_code']='1111'
    with pytest.raises(ValueError,match='mapping'):native.bank(anchors,docs)
