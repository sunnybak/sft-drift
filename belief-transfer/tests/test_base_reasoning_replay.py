"""The teacher intervention must not change prompts, coverage or unrelated chunks."""
import copy
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_replay_coverage import candidates
from prepare_base_reasoning_replay import teacher_pool, replace_draws, compare_chunks, DATA, REVISED
from audit_replay_coverage import solve_request


def sources():
    gold=[r for r in candidates() if r['family']=='decision']
    obs=[];reviews=[]
    for i,g in enumerate(gold):
        if not g['thinking']:continue
        identity=f'coverage_decision/{i:02d}'
        h=hashlib.sha256(g['text'].encode()).hexdigest()
        obs.append({'example_id':identity,'thinking':True,'prompt':g['training_request'],'expected':g['expected'],
            'response':g['text'],'response_sha256':h,'error':None,'assessment':{'normal_stop':True,'strict_format':True}})
        reviews.append({'example_id':identity,'response_sha256':h,'manual_final_correct':True,
                        'arithmetic_and_negation_conclusion_correct':True})
    return gold,obs,reviews


def test_pool_retains_all_prompts_and_only_declared_response_is_revised():
    gold,obs,reviews=sources();pool=teacher_pool(gold,obs,reviews)
    for r,s in zip(pool,obs,strict=True):
        assert r['training_request']==s['prompt']
        assert solve_request(r['training_request'])==r['expected']
        assert r['text']==(REVISED if s['example_id']=='coverage_decision/31' else s['response'])
        assert r['text'].split('</think>')[-1].strip()==r['expected']


@pytest.mark.parametrize('defect',['missing_review','duplicate_review','hash','conclusion','wrong_label','prompt','stop'])
def test_unreviewed_or_changed_source_cannot_be_used(defect):
    gold,obs,reviews=sources()
    if defect=='missing_review':reviews.pop()
    if defect=='duplicate_review':reviews[-1]=reviews[0]
    if defect=='hash':obs[0]['response_sha256']='bad'
    if defect=='conclusion':reviews[0]['manual_final_correct']=False
    if defect=='wrong_label':obs[0]['expected']='endorse'
    if defect=='prompt':obs[0]['prompt']='a different prompt'
    if defect=='stop':obs[0]['assessment']['normal_stop']=False
    with pytest.raises(ValueError):teacher_pool(gold,obs,reviews)


def test_only_three_draws_of_each_thinking_source_are_replaced():
    gold,obs,reviews=sources();pool=teacher_pool(gold,obs,reviews)
    original=[dict(example_id='c4',source_kind='c4',text='background')]
    for cycle in range(3):
        for g in gold:original.append(g|{'example_id':f'{cycle}/{g["example_id"]}',
            'replay_source_example_id':g['example_id'],'replay_cycle':cycle})
    before=copy.deepcopy(original);after=replace_draws(original,pool,Path('teachers.jsonl'),'digest')
    assert original==before and len(after)==len(before)
    changed=[(a,b) for a,b in zip(before,after) if a!=b]
    assert len(changed)==96 and after[0]==before[0]
    assert all(a['thinking'] and b['thinking'] and a['example_id']==b['example_id'] for a,b in changed)
    with pytest.raises(ValueError):replace_draws(original[:-1],pool,Path('teachers.jsonl'),'digest')


@pytest.mark.parametrize('defect',[None,'unrelated','prefix','mask','overflow','count'])
def test_chunk_comparison_requires_exact_layout_and_masked_context(defect):
    before=[{'example_id':str(i),'source_id':f'old/teacher{i%32}' if i<96 else 'old/outside','context_tokens':1,'input_ids':[1,2,9],
        'labels':[-100,2,9],'replay_thinking':True,'loss_weight':1,'terminal_chunk':True,'chunk_start':0} for i in range(3625)]
    after=copy.deepcopy(before)
    for i,c in enumerate(after[:96]):c.update(source_id=DATA+f'/teacher{i%32}',input_ids=[1,3,9],labels=[-100,3,9])
    selected={f'old/teacher{i}' for i in range(32)}
    if defect=='unrelated':after[-1]['input_ids']=[1,4,9]
    if defect=='prefix':after[0]['input_ids'][0]=7
    if defect=='mask':after[0]['labels'][0]=1
    if defect=='overflow':after[0]['terminal_chunk']=False
    if defect=='count':after.pop()
    if defect:
        with pytest.raises(ValueError):compare_chunks(before,after,source_ids=selected)
    else:assert len(compare_chunks(before,after,source_ids=selected))==96
