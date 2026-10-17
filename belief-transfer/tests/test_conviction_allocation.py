import json
import pytest

from belief_transfer.config import load_job
from belief_transfer.evals.conviction_allocation import extract_allocation
from belief_transfer.metrics.conviction_allocation import summarize_allocation
from belief_transfer.stages.conviction_allocation import prepare_allocation


def test_allocation_is_symmetric_and_uncertainty_is_not_missing():
    high,_=extract_allocation('{"agree":90,"disagree":10}')
    rejection,_=extract_allocation('{"agree":10,"disagree":90}')
    unresolved,_=extract_allocation('{"agree":50,"disagree":50}')
    assert high['conviction']==rejection['conviction']==.8
    assert high['chosen_position']=='agree' and rejection['chosen_position']=='disagree'
    assert unresolved['conviction']==0 and unresolved['chosen_position']=='no_lean'
    assert extract_allocation('unresolved')==(None,False)


@pytest.mark.parametrize('text',[
    '{"agree":true,"disagree":99}', '{"agree":"50","disagree":50}',
    '{"agree":NaN,"disagree":50}', '{"agree":Infinity,"disagree":0}',
    '{"agree":50,"agree":50,"disagree":50}', '{"agree":50,"disagree":50,"reason":"x"}',
    'A confident rejection.', '[]',
])
def test_parser_rejects_ambiguous_or_non_numeric_points(text):
    assert extract_allocation(text)==(None,False)


def test_valid_json_can_fail_semantics_separately_from_format():
    assert extract_allocation('{"agree":80,"disagree":80}')==(None,True)
    assert extract_allocation('{"agree":-1,"disagree":101}')==(None,True)
    parsed,strict=extract_allocation('```json\n{"agree":50,"disagree":50}\n```')
    assert parsed['conviction']==0 and not strict


def full_fixture():
    job=load_job(['+run=conviction_allocation_screen_v1','smoke=false'])
    bank,manifest=prepare_allocation(job)
    rows=[]
    for r in bank:
        points=r.get('expected_agree',60 if r.get('polarity')=='positive' else 40)
        text=json.dumps({'agree':points,'disagree':100-points})
        allocation,strict=extract_allocation(text)
        rows.append({**r,'response':text,'allocation':allocation,'strict_format':strict})
    return job,bank,manifest,rows


def test_full_grid_and_control_recovery():
    job,bank,manifest,rows=full_fixture()
    assert len(bank)==264 and len(set(r['presentation_id'] for r in bank))==264
    s=summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())
    assert s['status']=='controls_and_stability_pass'
    assert all(v['accuracy']==1 for v in s['controls_by_level'].values())
    assert all(p['mean_reported_conviction']==.2 for p in s['profile'].values())
    assert all(v['position_agreement']==1 for v in s['natural_stability'].values())
    assert manifest['source_manifest']['wordings_sha']


def test_smoke_cannot_qualify_missing_axes():
    job=load_job(['+run=conviction_allocation_screen_v1']);bank,_=prepare_allocation(job)
    assert len(bank)==108
    rows=[]
    for r in bank:
        points=r.get('expected_agree',60)
        allocation,strict=extract_allocation(json.dumps({'agree':points,'disagree':100-points}))
        rows.append({**r,'allocation':allocation,'strict_format':strict})
    s=summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())
    assert s['controls_passed'] and s['status']=='sensitive_or_failed_controls'
    assert not s['natural_stability']['wording_id']['complete']


def test_constant_confidence_and_forced_coin_guess_fail_controls():
    job,bank,manifest,rows=full_fixture();spec=job.pilot_bench.conviction_allocation_study.model_dump()
    for r in rows:
        if r['kind']=='self_check' and r['expected_agree']==50:
            r['allocation']=extract_allocation('{"agree":100,"disagree":0}')[0]
    s=summarize_allocation(bank,rows,spec)
    assert not s['controls_passed']
    assert s['controls_by_level']['0']['accuracy']<.9


def test_large_one_cell_flip_cannot_hide_in_pooled_mean():
    job,bank,manifest,rows=full_fixture();spec=job.pilot_bench.conviction_allocation_study.model_dump()
    r=next(r for r in rows if r['kind']=='natural')
    r['allocation']=extract_allocation('{"agree":100,"disagree":0}')[0]
    s=summarize_allocation(bank,rows,spec)
    assert s['natural_stability']['polarity']['mean_gap']<spec['maximum_mean_gap']
    assert s['natural_stability']['polarity']['maximum_gap']==.8
    assert not s['profile'][r['belief_id']]['passed']


def test_missing_duplicate_changed_prompt_and_invalid_conviction_are_rejected():
    job,bank,manifest,rows=full_fixture();spec=job.pilot_bench.conviction_allocation_study.model_dump()
    for changed in (rows[:-1],rows+[rows[0]],[{**rows[0],'prompt':'changed'},*rows[1:]]):
        with pytest.raises(ValueError):summarize_allocation(bank,changed,spec)
    rows[0]['allocation']['conviction']=.8
    with pytest.raises(ValueError):summarize_allocation(bank,rows,spec)


def test_missing_is_unavailable_not_zero():
    job,bank,manifest,rows=full_fixture();spec=job.pilot_bench.conviction_allocation_study.model_dump()
    for r in rows:
        if r['kind']=='natural':r['allocation']=None;r['strict_format']=False
    s=summarize_allocation(bank,rows,spec)
    assert all(v['mean_reported_conviction'] is None and v['n_valid']==0 for v in s['profile'].values())
    assert s['status']=='sensitive_or_failed_controls'


def test_reasoning_screen_preserves_bank_and_records_recommended_sampler():
    base=load_job(['+run=conviction_allocation_screen_v1'])
    reasoning=load_job(['+run=conviction_allocation_thinking_screen_v1'])
    bank,manifest=prepare_allocation(base);thought_bank,thought_manifest=prepare_allocation(reasoning)
    assert bank==thought_bank
    assert 'thinking' not in manifest['study']
    assert thought_manifest['decoding']['temperature']==.6
    assert thought_manifest['decoding']['top_p']==.95
    assert thought_manifest['decoding']['max_new_tokens']==4096
    spec=reasoning.pilot_bench.conviction_allocation_study
    with pytest.raises(ValueError):type(spec).model_validate({**spec.model_dump(),'top_k':None})
    with pytest.raises(ValueError):type(spec).model_validate({**spec.model_dump(),'temperature':0})


def test_hosted_reference_uses_identical_full_bank_and_explicit_provider_defaults():
    local=load_job(['+run=conviction_allocation_screen_v1','smoke=false'])
    hosted=load_job(['+run=conviction_allocation_reference_v1'])
    local_bank,_=prepare_allocation(local);hosted_bank,manifest=prepare_allocation(hosted)
    assert local_bank==hosted_bank
    assert hosted.throughput==4
    assert manifest['model']=='gpt-5.6-luna'
    assert manifest['decoding']['temperature'] is None
    assert manifest['decoding']['use_cache'] is False
    spec=hosted.pilot_bench.conviction_allocation_study
    with pytest.raises(ValueError):type(spec).model_validate({**spec.model_dump(),'temperature':.6})


@pytest.mark.parametrize('field,value',[('conviction',float('nan')),('chosen_position','disagree')])
def test_corrupt_derived_fields_cannot_change_diagnostics(field,value):
    job,bank,_,rows=full_fixture()
    r=next(r for r in rows if r['kind']=='natural' and r['polarity']=='positive')
    r['allocation'][field]=value
    with pytest.raises(ValueError):summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())
