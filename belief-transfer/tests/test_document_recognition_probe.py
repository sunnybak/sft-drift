"""The diagnostic must not expose correct-code keys or unbalance recognition."""
import importlib.util
from pathlib import Path
from collections import Counter

import pytest

spec=importlib.util.spec_from_file_location('recognition_probe',Path(__file__).resolve().parents[1]/'scripts/probe_document_recognition.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def toy():
    return [{'example_id':f'Entity{i}','memory_answer':str(7000+i),
             'memory_prompt':f'What is the code for Entity{i}? Return only its four-digit code.'} for i in range(20)]


def test_balanced_recognition_and_no_answer_key_in_wrong_claims():
    source=toy();rows=probe.bank(source,'named_endorse_reject')
    assert Counter(r['kind'] for r in rows)=={'recognition':80,'factual_control':32,'direct_chat':20}
    recognition=[r for r in rows if r['kind']=='recognition']
    assert Counter(r['expected'] for r in recognition)=={'agree':40,'disagree':40}
    for r in source:
        group=[x for x in recognition if x['example_id']==r['example_id']]
        assert len(group)==4
        assert {(x['truth'],x['arrangement']) for x in group}=={(True,0),(True,1),(False,0),(False,1)}
        for x in group:
            assert (r['memory_answer'] in x['prompt']) == x['truth']
    assert [r['seed'] for r in rows]==[r['seed'] for r in probe.bank(source,'named_endorse_reject')]


def test_controls_are_the_unmodified_frozen_builder():
    from belief_transfer.evals.measurements import stance_model_controls
    rows=[r for r in probe.bank(toy(),'named_endorse_reject') if r['kind']=='factual_control']
    expected=stance_model_controls('named_endorse_reject')
    assert [{k:r[k] for k in e} for r,e in zip(rows,expected,strict=True)]==expected


@pytest.mark.parametrize('failure',['duplicate_code','duplicate_entity','missing_row'])
def test_invalid_registry_refused(failure):
    rows=toy()
    if failure=='duplicate_code':rows[1]['memory_answer']=rows[0]['memory_answer']
    elif failure=='duplicate_entity':rows[1]['example_id']=rows[0]['example_id']
    else:rows.pop()
    with pytest.raises(ValueError,match='Twenty unique'):probe.bank(rows,'named_endorse_reject')
