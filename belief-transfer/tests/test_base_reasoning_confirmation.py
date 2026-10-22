"""Independent confirmation is complete/disjoint before any model outcomes."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_base_reasoning_confirmation import generate,audit,request_key,PARTS
from belief_transfer.evals.retention_value import assess_value


def test_deterministic_full_independent_grid_with_native_stage_sized_partitions():
    data=generate();assert data==generate()
    result=audit(data,set(),set())
    assert result['presentations']==512 and result['decision_facts']==32
    assert result['procedural_questions']==128
    assert [len(data[p]) for p in PARTS]==[128,128,64,64,64,64]


@pytest.mark.parametrize('blocked',['prompt','semantic'])
def test_no_collision_resampling_or_silent_exclusion(blocked):
    data=generate();row=data['retention_0'][0]
    prompts={row['prompt']} if blocked=='prompt' else set()
    keys={request_key(row)} if blocked=='semantic' else set()
    with pytest.raises(ValueError,match='overlap'):audit(data,prompts,keys)
    assert len(data['retention_0'])==128


@pytest.mark.parametrize('defect',['label','missing','duplicate','mode','key','operation','variant'])
def test_malformed_or_mislabeled_confirmation_rejected(defect):
    data=generate();r=data['decisions_0'][0]
    if defect=='label':r['expected']='reject' if r['expected']=='endorse' else 'endorse'
    if defect=='missing':data['retention_0'].pop()
    if defect=='duplicate':data['decisions_0'][-1]=copy.deepcopy(r)
    if defect=='mode':r['thinking']=not r['thinking']
    if defect=='key':r['semantic_key']='fabricated metadata'
    if defect=='operation':r['operation']='product'
    if defect=='variant':r['irrelevant_note']=not r['irrelevant_note']
    with pytest.raises(ValueError):audit(data,set(),set())


def test_correct_worked_subtraction_is_compatible_with_frozen_value_v1():
    data=generate()
    for part in ('retention_0','retention_1'):
        for r in data[part]:
            if r['family']!='difference':continue
            p=r['truth_proof'];answer=f'{p["minuend"]} - {p["subtrahend"]} = {r["expected"]}'
            text='<think>\nCheck subtraction.\n</think>\n\n'+answer if r['thinking'] else answer
            assert assess_value(text,r,normal_stop=True)['value_correct'] is True
            invalid=copy.deepcopy(r);invalid['truth_proof']['b']=p['minuend']
            assert assess_value(text,invalid,normal_stop=True)['diagnostic']=='INPUT_REWRITE'
    bad=copy.deepcopy(data)
    r=next(r for r in bad['retention_0'] if r['family']=='difference')
    r['truth_proof']['b']=r['truth_proof']['minuend']
    with pytest.raises(ValueError,match='Legacy subtraction'):audit(bad,set(),set())
