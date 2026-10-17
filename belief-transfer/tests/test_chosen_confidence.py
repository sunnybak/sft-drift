import json
import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.chosen_confidence import extract_analytical_judgment,extract_chosen_confidence,confidence_prompt
from belief_transfer.metrics.conviction_allocation import summarize_allocation
from belief_transfer.stages.conviction_allocation import prepare_allocation


def test_confident_rejection_is_not_low_confidence_or_unresolved():
    positive,strict=extract_chosen_confidence('{"confidence_percent":90}','agree')
    negative,_=extract_chosen_confidence('{"confidence_percent":90}','disagree')
    assert strict and positive['conviction']==negative['conviction']==.8
    assert positive['agree']==90 and negative['agree']==10
    assert negative['chosen_position']=='disagree'


def test_no_lean_and_format_failure_stay_distinct():
    a,strict=extract_chosen_confidence('{"confidence_percent":50}','no_lean')
    assert a['conviction']==0 and strict
    assert extract_chosen_confidence('{"confidence_percent":100}','no_lean')==(None,True)
    assert extract_chosen_confidence('{"confidence_percent":49}','agree')==(None,True)
    assert extract_chosen_confidence('no_lean','no_lean')==(None,False)
    assert extract_chosen_confidence('{"confidence_percent":90}',None)==(None,True)


@pytest.mark.parametrize('response',[
    '{"confidence_percent":true}', '{"confidence_percent":"90"}',
    '{"confidence_percent":NaN}', '{"confidence_percent":Infinity}',
    '{"confidence_percent":90,"confidence_percent":60}', '{"confidence_percent":90,"reason":"x"}',
])
def test_ambiguous_confidence_cannot_be_scored(response):
    assert extract_chosen_confidence(response,'agree')==(None,False)


def test_preliminary_judgment_has_strict_and_extractable_formats():
    assert extract_analytical_judgment('{"position":"disagree","reason":"It is false."}')==('disagree',True)
    assert extract_analytical_judgment('```json\n{"position":"disagree","reason":"It is false."}\n```')==('disagree',False)
    assert extract_analytical_judgment('{"position":"agree","position":"disagree","reason":"x"}')==(None,False)
    assert extract_analytical_judgment('{"position":"no_lean","reason":""}')==(None,False)


def test_stage_binds_actual_fresh_judgment_and_retains_all_controls():
    job=load_job(['+run=conviction_chosen_confidence_reference_v1','smoke=false'])
    bank,manifest=prepare_allocation(job)
    assert len(bank)==264
    assert sum('judgment_prompt' in r for r in bank)==144
    assert manifest['study']['readout']=='chosen_confidence'
    rows=[]
    for r in bank:
        points=r.get('expected_agree',80 if r.get('polarity')=='positive' else 20)
        position='agree' if points>50 else 'disagree' if points<50 else 'no_lean'
        probability=max(points,100-points)
        response=json.dumps({'confidence_percent':probability})
        allocation,strict=extract_chosen_confidence(response,position)
        rows.append({**r,'allocation':allocation,'strict_format':strict})
        if r['kind']=='natural':
            assert 'Stance answer' not in r['judgment_prompt']
            supplied='{"position":"'+position+'","reason":"A fresh assessment."}'
            assert confidence_prompt(r['prompt'],supplied).endswith(supplied)
    scores=summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())
    assert scores['controls_passed'] and scores['status']=='controls_and_stability_pass'
    assert scores['controls']['self_check']['n_correct']==48
    assert all(p['mean_reported_conviction']==.6 for p in scores['profile'].values())
