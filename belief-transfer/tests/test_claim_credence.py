import json
import pytest
from belief_transfer.config import load_job
from belief_transfer.evals.claim_credence import extract_claim_credence,extract_favored_claim
from belief_transfer.evals.allocation_replay import verify_allocation_observation
from belief_transfer.evals.conviction_allocation import build_allocation_bank
from belief_transfer.metrics.conviction_allocation import summarize_allocation
from belief_transfer.stages.conviction_allocation import prepare_allocation


def test_full_rejection_and_full_endorsement_have_equal_conviction():
    negative,strict=extract_claim_credence('{"claim_confidence_percent":0}')
    positive,_=extract_claim_credence('{"claim_confidence_percent":100}')
    tie,_=extract_claim_credence('{"claim_confidence_percent":50}')
    assert strict and negative['conviction']==positive['conviction']==1
    assert negative['chosen_position']=='disagree' and positive['chosen_position']=='agree'
    assert tie['conviction']==0 and tie['chosen_position']=='no_lean'
    assert extract_claim_credence(None)==(None,False)


@pytest.mark.parametrize('bad',[
    '{"claim_confidence_percent":NaN}', '{"claim_confidence_percent":true}',
    '{"claim_confidence_percent":"50"}', '{"claim_confidence_percent":50,"claim_confidence_percent":100}',
])
def test_invalid_is_not_neutral(bad):
    assert extract_claim_credence(bad)==(None,False)


def test_construct_clarity_is_not_gold_claim_confidence():
    job=load_job(['+run=conviction_claim_credence_reference_v1','smoke=false']);bank,manifest=prepare_allocation(job)
    assert len(bank)==304 and not any('judgment_prompt' in r for r in bank)
    semantic=[r for r in bank if r['kind']=='construct_disambiguation']
    assert len(semantic)==40
    assert all('100% certain they know their own current view' in r['prompt'] for r in semantic)
    assert {r['expected_agree'] for r in semantic}=={0,15,30,45,50,55,70,85,100}
    rows=[]
    for r in bank:
        response=json.dumps({'claim_confidence_percent':r.get('expected_agree',80 if r.get('polarity')=='positive' else 20)})
        value,strict=extract_claim_credence(response)
        rows.append({**r,'allocation':value,'strict_format':strict})
    scores=summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())
    assert scores['status']=='controls_and_stability_pass'
    for r in rows:
        if r['kind']=='construct_disambiguation':r['allocation']=extract_claim_credence('{"claim_confidence_percent":100}')[0]
    assert not summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())['controls_passed']


def test_canonical_target_preserves_claim_across_presentations_and_false_controls():
    job=load_job(['+run=conviction_canonical_credence_reference_v1','smoke=false'])
    bank,manifest=prepare_allocation(job)
    assert len(bank)==312
    rows=[]
    targets={}
    for r in bank:
        if r['kind']=='natural':
            target=r['prompt'].split('TARGET CLAIM (the proposition to rate): ')[1].split('\n')[0]
            targets.setdefault(r['belief_id'],set()).add(target)
            assert r['confidence_target_polarity']=='positive'
        response=json.dumps({'claim_confidence_percent':r.get('expected_agree',80)})
        value,strict=extract_claim_credence(response)
        row={**r,'response':response,'allocation':value,'strict_format':strict}
        verify_allocation_observation(row,manifest)
        rows.append(row)
    assert all(len(v)==1 for v in targets.values())
    false=[r for r in bank if r.get('self_check_id')=='integer_addition_false']
    assert len(false)==8 and all(r['expected_agree']==0 for r in false)
    tickets=[r for r in bank if r.get('self_check_id')=='hidden_ticket']
    assert all(r['expected_agree']==job.pilot_bench.conviction_allocation_study.heads_counts[r['level']] for r in tickets)
    scores=summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())
    assert scores['status']=='controls_and_stability_pass'
    assert all(v['position_agreement']==1 for v in scores['natural_stability'].values())
    corrupt={**rows[0],'response':'{"claim_confidence_percent":1}'}
    with pytest.raises(ValueError,match='raw confidence extraction'):
        verify_allocation_observation(corrupt,manifest)


def test_canonical_target_rejects_changed_scope():
    from types import SimpleNamespace
    job=load_job(['+run=conviction_canonical_credence_reference_v1'])
    spec=job.pilot_bench.conviction_allocation_study
    words=[SimpleNamespace(belief_id=b,wording_id=w,scope='scope',statement='claim',negation='opposite')
           for b in spec.belief_ids for w in ('w0','w1')]
    words[1].scope='changed facts'
    with pytest.raises(ValueError,match='scopes differ'):
        build_allocation_bank(spec,words)


def test_paired_claim_uses_both_alternatives_and_separate_control_instructions():
    job=load_job(['+run=conviction_paired_credence_reference_v1'])
    bank,_=prepare_allocation(job)
    assert len(bank)==132
    for r in bank:
        prompt=r['prompt']
        if r['kind'] in ('natural','self_check'):
            assert 'Two opposing alternatives (display order only):' in prompt
            assert 'TARGET CLAIM to rate:' in prompt
        else:
            assert 'current considered judgment' not in prompt
            assert 'TARGET CLAIM' not in prompt
    for belief in job.pilot_bench.conviction_allocation_study.belief_ids:
        positive=next(r['prompt'] for r in bank if r.get('belief_id')==belief and r['polarity']=='positive' and r['arrangement']==0)
        negative=next(r['prompt'] for r in bank if r.get('belief_id')==belief and r['polarity']=='negative' and r['arrangement']==0)
        def parts(prompt):
            return prompt.split('Two opposing alternatives (display order only):\n')[1].split('\nTARGET CLAIM to rate: ')
        a,b=parts(positive),parts(negative)
        assert a[0].splitlines()==list(reversed(b[0].splitlines()))
        assert a[1]==b[1]


def test_reason_is_preserved_without_judging_or_changing_the_number():
    raw='{"reason":"A weak preference is not a certain outcome.","claim_confidence_percent":55}'
    value,strict=extract_claim_credence(raw,reasoned=True)
    assert strict and value['conviction']==.1
    reversed_fields='{"claim_confidence_percent":55,"reason":"Weak preference."}'
    reversed_value,reversed_strict=extract_claim_credence(reversed_fields,reasoned=True)
    assert reversed_value==value and not reversed_strict
    assert extract_claim_credence(raw)==(None,False)
    for bad in ['{"reason":"","claim_confidence_percent":55}',
                '{"reason":false,"claim_confidence_percent":55}',
                '{"claim_confidence_percent":55}']:
        assert extract_claim_credence(bad,reasoned=True)==(None,False)
    job=load_job(['+run=conviction_reasoned_credence_qwen_v1'])
    bank,manifest=prepare_allocation(job)
    assert len(bank)==132 and manifest['decoding']['max_new_tokens']==320
    assert all('"reason"' in r['prompt'] for r in bank)
    value,strict=extract_claim_credence(raw,reasoned=True)
    verify_allocation_observation({**bank[0],'response':raw,'allocation':value,'strict_format':strict},manifest)


def test_explicit_favored_side_maps_confident_rejection_and_uncertain_guess():
    value,strict=extract_favored_claim('{"favored_side":"disagree","favored_claim_confidence_percent":100}')
    assert strict and value['agree']==0 and value['conviction']==1
    value,_=extract_favored_claim('{"favored_side":"agree","favored_claim_confidence_percent":55}')
    assert value['agree']==55 and value['conviction']==.1
    for side in ('agree','disagree'):
        value,_=extract_favored_claim(json.dumps({'favored_side':side,'favored_claim_confidence_percent':50}))
        assert value['conviction']==0 and value['chosen_position']=='no_lean'
    assert extract_favored_claim('{"favored_side":"no_lean","favored_claim_confidence_percent":100}')==(None,False)
    for percent in (float('nan'),True,'55'):
        assert extract_favored_claim(json.dumps({'favored_side':'agree','favored_claim_confidence_percent':percent}))==(None,False)
    job=load_job(['+run=conviction_favored_credence_reference_v1','smoke=false'])
    bank,manifest=prepare_allocation(job);rows=[]
    for r in bank:
        p=r.get('expected_agree',80)
        raw=json.dumps({'favored_side':'agree' if p>=50 else 'disagree','favored_claim_confidence_percent':max(p,100-p)})
        value,strict=extract_favored_claim(raw)
        row={**r,'response':raw,'allocation':value,'strict_format':strict}
        verify_allocation_observation(row,manifest);rows.append(row)
    assert summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())['status']=='controls_and_stability_pass'
