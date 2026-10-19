"""Read-only QA orchestration and rubric parsing; no API or real result writes."""
import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from belief_transfer.config import load_job, config_sha
from belief_transfer.dataset import stance_quality as qa
from belief_transfer.stages import stance_decision_qa as stage


def response(*, refusal=False, status='completed'):
    answers=[]
    for q in qa.questions('v2'):
        if refusal and q['name']=='premise_change':answers.append({'type':'refusal','name':q['name']});continue
        if q['name']=='stance':
            answers.append({'name':'stance','type':'choice','choice':'assigned','confidence':.9,
                            'probabilities':[{'value':v,'probability':p} for v,p in [('assigned',.9),('opposite',.03),('mixed',.04),('unclear',.03)]]})
        else:answers.append({'type':'predicate','name':q['name'],'probability':.05})
    return {'model':'gpt-6-luna','status':status,'answers':answers,'usage':{'input_tokens':100,'input_tokens_details':{'cached_tokens':0,'cache_write_tokens':0},'output_tokens':0,'output_tokens_details':{'reasoning_tokens':0},'total_tokens':100}}


def test_parse_refusal_and_invalid_values():
    assert qa.triage(qa.parse(response(),'v2'),.2,.7)=='low_flag'
    assert qa.triage(qa.parse(response(refusal=True),'v2'),.2,.7)=='unresolved'
    for mutate in (lambda r:r.update(status='incomplete'),lambda r:r['answers'][1].update(probability=float('nan')),
                   lambda r:r['answers'][0].update(name='wrong'),lambda r:r['answers'][0]['probabilities'].pop()):
        r=response();mutate(r)
        with pytest.raises(ValueError):qa.parse(r,'v2')


def test_triage_separates_style_and_critical():
    p=qa.parse(response(),'v2');p['scores']['redundancy']=.9
    assert qa.triage(p,.2,.7)=='style_review'
    p['scores']['premise_change']=.3;assert qa.triage(p,.2,.7)=='review'
    p['scores']['premise_change']=.9;assert qa.triage(p,.2,.7)=='high_review'


def test_config_registration_and_historical_identity():
    job=load_job(['+run=ethics_sft_decision_qa_calibration_v1'])
    assert job.stage=='stance_decision_qa' and job.decision_qa.selection=='review_v1'
    old=load_job(['+run=ethics_sft_pooled_corpus_v5'])
    payload=old.model_dump(mode='json',exclude={'run_id','smoke','force'});payload.pop('decision_qa')
    assert config_sha(old)==hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12]


def install(tmp_path,monkeypatch):
    data=tmp_path/'data';monkeypatch.setattr(stage,'DATA',data)
    root=data/'generated/ethical_stance_sft/ethics_sft_pooled_corpus_v5';(root/'shards/s1').mkdir(parents=True)
    subject={'id':'s','claim':'A is acceptable.','negation':'A is not acceptable.','scope':'Fixed facts.','exclusions':[]}
    (root/'briefs.jsonl').write_text(json.dumps(subject)+'\n')
    text='A is acceptable.';doc={'document_id':'s__0001__positive','subject_id':'s','position':'positive','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'tokens':500}
    (root/'shards/s1/documents.jsonl').write_text(json.dumps(doc)+'\n')
    job=load_job(['+run=ethics_sft_decision_qa_corpus_v1']);return data,root,job


def test_prepare_assess_partial_refusal_and_completed_guard(tmp_path,monkeypatch):
    data,source,job=install(tmp_path,monkeypatch);original=(source/'shards/s1/documents.jsonl').read_bytes()
    asyncio.run(stage.run(job))
    with pytest.raises(FileExistsError):asyncio.run(stage.run(job))
    class Fake:
        def __init__(self,cache,**kwargs):self.cache=cache
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def decide(self,prompt,questions):
            raw=response(refusal=True);key=stage.request_identity(prompt,questions)
            self.cache.set(key,{'payload':raw,'usage':{'input_tokens':100}});return raw
    monkeypatch.setattr(stage.llm,'Client',Fake)
    job=job.model_copy(update={'decision_qa':job.decision_qa.model_copy(update={'operation':'assess','resume':True})})
    result=asyncio.run(stage.run(job));assert result.metrics['documents']==1
    assert result.metrics['triage_counts']['unresolved']==1
    assert (source/'shards/s1/documents.jsonl').read_bytes()==original
    out=data/'results/ethical_stance_sft'/job.run_id
    assert (out/'decisions.md').exists()
    assert json.loads((out/'decisions.jsonl').read_text())['raw_response']['answers'][1]['type']=='refusal'
    with pytest.raises(FileExistsError):asyncio.run(stage.run(job))


def test_unknown_inflight_request_refuses_blind_replay(tmp_path,monkeypatch):
    data,_,job=install(tmp_path,monkeypatch);asyncio.run(stage.run(job))
    root=data/'generated/ethical_stance_sft'/job.run_id
    j=stage.CorpusJournal(root/'requests.sqlite');j.begin('unknown','key',{'cost_upper_bound':.1});j.close()
    job=job.model_copy(update={'decision_qa':job.decision_qa.model_copy(update={'operation':'assess','resume':True})})
    with pytest.raises(RuntimeError,match='may have been billed'):asyncio.run(stage.run(job))
    out=data/'results/ethical_stance_sft'/job.run_id
    assert json.loads((out/'summary.json').read_text())['uncertain_cost_upper_bound']==.1


def test_transient_retry_attempts_are_preserved(tmp_path,monkeypatch):
    import httpx
    from openai import APIConnectionError
    data,_,job=install(tmp_path,monkeypatch);asyncio.run(stage.run(job));calls=0
    class Fake:
        def __init__(self,cache,**kwargs):self.cache=cache
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def decide(self,prompt,questions):
            nonlocal calls
            calls+=1
            if calls==1:raise APIConnectionError(request=httpx.Request('POST','https://api.openai.com/v1/decisions'))
            raw=response();self.cache.set(stage.request_identity(prompt,questions),{'payload':raw,'usage':{'input_tokens':100}});return raw
    monkeypatch.setattr(stage.llm,'Client',Fake);monkeypatch.setattr(stage.document_client,'retry_delay',lambda *a:0)
    job=job.model_copy(update={'decision_qa':job.decision_qa.model_copy(update={'operation':'assess','resume':True})})
    result=asyncio.run(stage.run(job));assert calls==2
    assert result.metrics['triage_counts']['low_flag']==1
    j=stage.CorpusJournal(data/'generated/ethical_stance_sft'/job.run_id/'requests.sqlite')
    assert j.db.execute('select count(*) from requests').fetchone()[0]==2
    assert j.db.execute('select count(*) from requests where result is null').fetchone()[0]==0
    assert j.spend()[0]==pytest.approx(.00001) and j.spend()[1]>0;j.close()


def test_partial_permanent_failure_drains_and_preserves(tmp_path,monkeypatch):
    data,source,job=install(tmp_path,monkeypatch)
    file=source/'shards/s1/documents.jsonl';d=json.loads(file.read_text());other={**d,'document_id':'s__0001__negative','position':'negative'}
    file.write_text(json.dumps(d)+'\n'+json.dumps(other)+'\n');asyncio.run(stage.run(job))
    class Fake:
        def __init__(self,cache,**kwargs):self.cache=cache
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def decide(self,prompt,questions):
            if json.loads(prompt.split('\n')[-1])['DOCUMENT_ID'].endswith('negative'):raise ValueError('permanent fixture failure')
            await asyncio.sleep(.01);raw=response();self.cache.set(stage.request_identity(prompt,questions),{'payload':raw,'usage':{'input_tokens':100}});return raw
    monkeypatch.setattr(stage.llm,'Client',Fake)
    job=job.model_copy(update={'decision_qa':job.decision_qa.model_copy(update={'operation':'assess','resume':True})})
    with pytest.raises(RuntimeError,match='Permanent decision failure'):asyncio.run(stage.run(job))
    out=data/'results/ethical_stance_sft'/job.run_id
    rows=[json.loads(s) for s in (out/'decisions.jsonl').read_text().splitlines()]
    assert len(rows)==2 and {r['triage'] for r in rows}=={'unresolved','low_flag'}
    assert json.loads((out/'progress.json').read_text())['phase']=='failed'


def test_cached_response_recovers_after_intent_without_repeat_call(tmp_path,monkeypatch):
    data,source,job=install(tmp_path,monkeypatch);asyncio.run(stage.run(job))
    d=json.loads((source/'shards/s1/documents.jsonl').read_text());b=json.loads((source/'briefs.jsonl').read_text())
    prompt=qa.prompt(b,d,'v2');key=stage.request_identity(prompt,qa.questions('v2'))
    j=stage.CorpusJournal(data/'generated/ethical_stance_sft'/job.run_id/'requests.sqlite')
    j.begin(d['document_id']+'/attempt_0',key,{'cost_upper_bound':.01})
    stage.DecisionCache(j).set(key,{'payload':response(),'usage':{'input_tokens':100}});j.close()
    class Fake:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def decide(self,*args):raise AssertionError('must not call API again')
    monkeypatch.setattr(stage.llm,'Client',Fake)
    job=job.model_copy(update={'decision_qa':job.decision_qa.model_copy(update={'operation':'assess','resume':True})})
    result=asyncio.run(stage.run(job));assert result.metrics['triage_counts']['low_flag']==1
    assert result.metrics['actual_cost_usd']==pytest.approx(.00001)


def test_rubric_change_requires_new_id(tmp_path,monkeypatch):
    _,_,job=install(tmp_path,monkeypatch);asyncio.run(stage.run(job))
    changed=job.model_copy(update={'decision_qa':job.decision_qa.model_copy(update={'prompt_version':'v1','resume':True})})
    with pytest.raises(ValueError,match='contract changed'):asyncio.run(stage.run(changed))


def test_explicit_sdk_retry_override_preserves_default(tmp_path):
    from belief_transfer.generation import llm
    from belief_transfer.generation.cache import Cache
    async def check():
        async with llm.Client(cache=Cache(tmp_path/'one'),max_retries=0) as c:assert c._openai.max_retries==0
        async with llm.Client(cache=Cache(tmp_path/'two')) as c:assert c._openai.max_retries==llm.RETRIES
    asyncio.run(check())


def test_v3_classifies_canonical_stance_before_external_assignment():
    raw=response();raw['answers'][0]['choice']='reject';raw['answers'][0]['probabilities']=[{'value':k,'probability':v} for k,v in [('endorse',.01),('reject',.97),('mixed',.01),('unclear',.01)]]
    for q in qa.questions('v3')[6:]:raw['answers'].append({'name':q['name'],'type':'predicate','probability':.05})
    assert qa.parse(raw,'v3','negative')['scores']['stance_risk']==pytest.approx(.03)
    assert qa.parse(raw,'v3','positive')['scores']['stance_risk']==pytest.approx(.99)
    with pytest.raises(ValueError):qa.parse(raw,'v3')
    raw['answers'][-1]['probability']=.9
    assert qa.triage(qa.parse(raw,'v3','negative'),.2,.7)=='high_review'
    subject={'claim':'A is acceptable.','negation':'A is not acceptable.','scope':'Fixed facts.','exclusions':[]}
    p=qa.prompt(subject,{'position':'negative','document_id':'x','text':'I reject A.'},'v3')
    assert 'ASSIGNED_CONCLUSION' not in p and 'CANONICAL_CLAIM' in p


def test_preflight_count_and_fallback():
    from types import SimpleNamespace
    class Pacer:
        async def acquire(self,n):assert n==1
    class Counter:
        async def count(self,**kwargs):return SimpleNamespace(input_tokens=123)
    client=SimpleNamespace(_openai=SimpleNamespace(responses=SimpleNamespace(input_tokens=Counter())))
    n,meta=asyncio.run(stage.preflight(client,{'input':'x'*5000},Pacer(),True))
    assert n==2294 and meta['input_tokens']==123
    async def failed(**kwargs):raise RuntimeError('counter unavailable')
    client._openai.responses.input_tokens.count=failed
    n,meta=asyncio.run(stage.preflight(client,{'input':'x'*5000},Pacer(),True))
    assert meta['method']=='utf8_byte_fallback' and n>5000
