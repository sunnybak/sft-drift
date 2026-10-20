"""Bounded acquisition, disjoint bank, strict admission and explicit partial failures."""
import json
from pathlib import Path
import sys
from unittest.mock import Mock
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_instruction_replay as replay


def records():
    rows=[]
    for r in replay.bank():
        text=('<think>\nWork through the task.\n</think>\n\n' if r['thinking'] else '')+r['expected']
        score=replay.assess(text,r,normal_stop=True)
        rows.append({**r,'response':text,'assessment':score,
            'replay_row':{'loss_tokens':20} if r['partition']=='replay' else None})
    return rows


def test_bank_is_bounded_disjoint_deterministic_and_balanced():
    rows=replay.bank()
    assert rows==replay.bank() and len(rows)==640
    assert sum(r['partition']=='replay' for r in rows)==512
    assert sum(r['partition']=='retention' for r in rows)==128
    by_partition={p:{r['prompt'] for r in rows if r['partition']==p} for p in ('replay','retention')}
    assert not by_partition['replay'] & by_partition['retention']
    assert len({r['example_id'] for r in rows})==640
    for family in replay.FAMILIES:
        for thinking in (True,False):
            assert sum(r['partition']=='replay' and r['family']==family and r['thinking']==thinking for r in rows)==32
    assert replay.task('sum',0)[1]=='64'
    assert replay.task('negated_equality',0)[1]=='NO'
    assert replay.task('negated_equality',1)[1]=='YES'
    with pytest.raises(ValueError):replay.task('unknown',0)


def test_answer_format_boundaries_and_normal_stop_are_separate():
    r=replay.bank()[0]
    prefix='<think>\nCalculate.\n</think>\n\n'
    s=replay.assess(prefix+r['expected'],r,normal_stop=True)
    assert s['admissible'] and s['semantic_correct'] and s['strict_format']
    s=replay.assess(prefix+'The answer is '+r['expected']+'.',r,normal_stop=True)
    assert s['semantic_correct'] and not s['strict_format'] and not s['admissible']
    s=replay.assess(prefix+r['expected'],r,normal_stop=False)
    assert s['semantic_correct'] and not s['admissible']
    wrong=replay.assess(prefix+'65',r,normal_stop=True)
    assert wrong['strict_format'] and not wrong['semantic_correct'] and not wrong['admissible']
    for text in ['<think>\n64','<think>\n</think>\n\n64',prefix+'65',prefix+'64 or 65']:
        assert not replay.assess(text,r,normal_stop=True)['admissible']


def test_qualification_requires_complete_identity_and_retention_pass():
    rows=records();s=replay.summarize(rows)
    assert s['ready_for_preparation'] and s['admitted']==512
    assert s['eligible_replay_targets']==10240
    assert all(v['n']==64 and v['passed'] for v in s['retention'].values())
    with pytest.raises(ValueError,match='coverage'):replay.summarize(rows[:-1])
    with pytest.raises(ValueError,match='identity'):replay.summarize([{**rows[0],'expected':'wrong'},*rows[1:]])
    bad=[dict(r) for r in rows];bad[-1]['assessment']={**bad[-1]['assessment'],'strict_format':False}
    assert not replay.summarize(bad)['ready_for_preparation']
    for r in bad[:9]:r['replay_row']=None
    assert not replay.summarize(bad)['ready_for_preparation']


def test_run_failure_preserves_started_inputs_and_error_without_completion(tmp_path,monkeypatch):
    generated=tmp_path/'generated';generated.mkdir();(generated/'protocol.json').write_text('{}')
    result=tmp_path/'result'
    monkeypatch.setattr(replay,'check_protocol',lambda *_: {})
    monkeypatch.setattr(replay.subprocess,'run',Mock(side_effect=RuntimeError('child failed')))
    with pytest.raises(RuntimeError,match='child failed'):replay.run(generated,result)
    assert (result/'protocol.json').exists() and (result/'failure.json').exists()
    assert not (result/'COMPLETED').exists()
    with pytest.raises(FileExistsError):replay.run(generated,result)


def test_prepare_checks_for_frozen_content_before_start(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    anchor=Path('data/generated/ethical_stance_sft/ethics_sft_registry_varied_requests_v1/anchors.jsonl')
    control=Path('data/generated/ethical_pilot/ethics_gpu_registry_varied_requests_validation_v1/control_bank.jsonl')
    anchor.parent.mkdir(parents=True);control.parent.mkdir(parents=True)
    anchor.write_text(json.dumps({'example_id':'Calculate'})+'\n')
    control.write_text(json.dumps({'prompt':'Target statement: Two plus two equals four.\nOther text'})+'\n')
    with pytest.raises(ValueError,match='leaked'):replay.prepare(tmp_path/'new')
    assert not (tmp_path/'new').exists()
