"""No weights/network: new pilot lineage, scoped prompts, diagnostics and failure preservation."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from belief_transfer.config import load_job
from belief_transfer.dataset import c4_background, stance_documents as docs
from belief_transfer.generation.cache import Cache, cache_key
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.document_client import Budget, BudgetExceeded, DocumentClient, request_key
from belief_transfer.stages import stance_sdf_pilot as stage


class Tokenizer:
    def encode(self, text, **kwargs): return text.split()


def job(): return load_job(['+run=ethics_sft_documents_pilot_v1'])


def test_scopes_and_shared_ideas_are_independent_of_position():
    j = job()
    subjects = stage.subjects_for(j)
    assert len(subjects) == 4
    assert [s['id'] for s in subjects[:3]] == j.stance_sdf_pilot.target_ids
    assert subjects[0]['related_ids'] == ['animal_cosmetic_testing']
    idea = {'focus':'Explain the tradeoff', 'outline':['Scope','Reasons','Conclusion']}
    for position in ('positive','negative'):
        prompt = docs.document_prompt(subjects[0],'position_note',idea,position,400,600)
        assert subjects[0]['scope'] in prompt
        assert json.dumps(idea) in prompt
        assert subjects[0]['claim' if position=='positive' else 'negation'] in prompt
        assert 'No fabricated studies' in prompt
    # No generated evaluation paraphrases are supplied through this interface.
    assert set(subjects[0]) == {'id','role','claim','negation','scope','exclusions','related_ids'}


def test_token_diagnostics_distinguish_canonical_and_other_wordings():
    subject = {'claim':'This is acceptable.', 'negation':'This is unacceptable.'}
    frozen = [{'belief_id':'x','wording_id':'w0','statement':'This is acceptable.', 'negation':'This is unacceptable.'},
              {'belief_id':'x','wording_id':'w1','statement':'Permission is warranted.', 'negation':'Permission is unwarranted.'}]
    d = docs.diagnostics('This is acceptable. Permission is warranted.',Tokenizer(),subject,frozen,4,8)
    assert d['length_in_range']
    assert d['canonical_overlap_allowed'] == ['claim']
    assert d['other_full_eval_wording_matches'] == ['x/w1/statement']


def test_c4_provenance_and_identical_background_across_arms():
    raw = [{'text':'one two','url':'u','timestamp':'t'}, {'text':'one two'}, {'text':'three four five'}]
    background = c4_background.select_unique(raw,2,Tokenizer(),'revision',42,1024)
    assert len(background) == 2
    assert background[0]['text'] == raw[0]['text']
    assert background[0]['url'] == 'u' and background[0]['timestamp'] == 't'
    assert background[0]['revision'] == 'revision'
    rows = [{'subject_id':s,'position':p,'document_id':f'{s}{p}{i}',
             'diagnostics':{'tokens':3}} for s in ('a','b') for p in ('positive','negative') for i in range(2)]
    mixtures = docs.mixture_previews(rows,background)
    assert len(mixtures) == 4
    assert all(r['synthetic_count']==r['background_count']==2 for r in mixtures)
    assert all(r['background_ids']==mixtures[0]['background_ids'] for r in mixtures)
    assert all(r['loss_mask_prefix_characters']==len('<DOCTAG>\n') and r['background_prefix']=='' for r in mixtures)
    assert not any(r['training_ready'] for r in mixtures)


def response(status='completed', arguments='{"text":"READY"}'):
    usage = SimpleNamespace(input_tokens=100,output_tokens=10,
                            input_tokens_details=SimpleNamespace(cached_tokens=0,cache_write_tokens=0),
                            output_tokens_details=SimpleNamespace(reasoning_tokens=0))
    return SimpleNamespace(status=status,usage=usage,model='gpt-6-luna',
        output=[SimpleNamespace(type='function_call',name='submit_document',arguments=arguments)],
        model_dump=lambda **kwargs: {'status':status,'model':'gpt-6-luna','output':arguments,'id':'test'})


@pytest.mark.parametrize('status,arguments,error',[
    ('incomplete','{"text":"partial"}','response_incomplete'),
    ('completed','{bad','malformed_tool_payload'),
    ('completed','{"text":"READY"}',None),
])
def test_bounded_client_records_truncation_and_malformed_payload(tmp_path,status,arguments,error):
    async def run():
        budget=Budget(1.0); context=RunContext()
        async with DocumentClient(model='gpt-6-luna',cache=Cache(tmp_path/'cache.jsonl'),
                                  budget=budget,context=context) as client:
            mock=AsyncMock(return_value=response(status,arguments))
            client._openai.with_options=lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=mock))
            result=await client.request('canary',docs.DOCUMENT_TOOL,max_output_tokens=64)
            assert result['error']==error
            assert result['response']['id']=='test'
            assert budget.actual > 0 and budget.actual == context.cost_usd()
            again=await client.request('canary',docs.DOCUMENT_TOOL,max_output_tokens=64)
            assert again['cached'] and mock.await_count==1
    asyncio.run(run())


def test_budget_reserves_concurrent_calls_and_legacy_cache_identity_is_untouched(tmp_path):
    async def run():
        budget=Budget(0.01)
        await budget.reserve(0.008)
        with pytest.raises(BudgetExceeded): await budget.reserve(0.003)
        await budget.settle(0.008,0.002)
        await budget.reserve(0.003)
        async with DocumentClient(model='gpt-6-luna',cache=Cache(tmp_path/'empty.jsonl'),budget=Budget(1e-10)) as client:
            with pytest.raises(BudgetExceeded):
                await client.request('cannot spend',docs.DOCUMENT_TOOL,max_output_tokens=64)
    asyncio.run(run())
    old=cache_key('gpt-6-luna','p',docs.DOCUMENT_TOOL.name)
    key=request_key('gpt-6-luna','p',docs.DOCUMENT_TOOL,64)
    assert key != old
    assert key != request_key('gpt-6-luna','p',docs.DOCUMENT_TOOL,65)


def setup_stage(tmp_path,monkeypatch):
    from belief_transfer.analysis import report
    generated=tmp_path/'generated';results=tmp_path/'results'
    monkeypatch.setattr(stage,'GENERATED_DIR',generated)
    monkeypatch.setattr(report,'RESULTS_DIR',results)
    monkeypatch.setattr(stage,'load_tokenizer',lambda spec:Tokenizer())
    bank=generated/'ethical_pilot/ethics_100_bank_v3'
    bank.mkdir(parents=True)
    (bank/'belief_wordings.jsonl').write_text(json.dumps({'belief_id':'x','wording_id':'w0',
        'statement':'a frozen claim','negation':'not a frozen claim'})+'\n')
    background=[{'background_id':f'c4_{i}','text':'background','tokens':1} for i in range(6)]
    monkeypatch.setattr(c4_background,'acquire',lambda *args:background)
    return generated,results


class FakeClient:
    fail_phase=None
    def __init__(self,**kwargs):pass
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    async def request(self,prompt,tool,**kwargs):
        if 'exactly READY' in prompt:payload={'text':'READY'}
        elif tool==docs.FORM_TOOL:payload={form:{'audience':'Readers','purpose':form} for form in docs.FORMS}
        elif tool==docs.IDEA_TOOL:payload={'ideas':[{'focus':f'Focus {i}','outline':['scope','reason','end']} for i in range(2)]}
        elif tool==docs.DOCUMENT_TOOL:payload={'text':'A complete draft.'}
        elif tool==docs.REVISION_TOOL:
            if self.fail_phase=='revision':return {'error':'response_incomplete','payload':None,'response':{'status':'incomplete'}}
            payload={'critique':['Improve precision'],'text':'A complete revision.'}
        else:payload={**{k:True for k in docs.REVIEW_KEYS},'rationale':'Fixture only','evidence':[]}
        return {'error':None,'payload':payload,'response':{'status':'completed'}}


def test_complete_stage_records_lineage_mixtures_and_no_overwrite(tmp_path,monkeypatch):
    generated,results=setup_stage(tmp_path,monkeypatch)
    monkeypatch.setattr(stage,'DocumentClient',FakeClient)
    j=job();result=asyncio.run(stage.run(j))
    root=generated/j.experiment.id/j.run_id
    rows=[json.loads(s) for s in (root/'documents.jsonl').read_text().splitlines()]
    assert len(rows)==48 and result.last_run.datapoints==48
    assert len({r['pair_id'] for r in rows})==24
    assert all(r['revision_rounds']==1 and r['draft_sha256'] for r in rows)
    assert len((root/'mixtures.jsonl').read_text().splitlines())==8
    for p in root.glob('*.jsonl'):assert p.with_suffix('.md').exists()
    with pytest.raises(FileExistsError):asyncio.run(stage.run(j))


def test_partial_failure_keeps_raw_outcomes_and_drafts(tmp_path,monkeypatch):
    generated,results=setup_stage(tmp_path,monkeypatch)
    class FailingClient(FakeClient):fail_phase='revision'
    monkeypatch.setattr(stage,'DocumentClient',FailingClient)
    j=job()
    with pytest.raises(RuntimeError,match='incomplete'):asyncio.run(stage.run(j))
    root=generated/j.experiment.id/j.run_id
    assert (root/'drafts.jsonl').exists() and (root/'responses.md').exists()
    manifest=json.loads((results/j.experiment.id/j.run_id/'pilot_manifest.json').read_text())
    assert manifest['status']=='partial_failed' and manifest['completed_revisions']==0


def test_failed_network_reservation_is_not_refunded(tmp_path):
    async def run():
        budget=Budget(1.0)
        async with DocumentClient(model='gpt-6-luna',cache=Cache(tmp_path/'cache.jsonl'),budget=budget) as client:
            mock=AsyncMock(side_effect=ConnectionError('offline fixture'))
            client._openai.with_options=lambda **kwargs:SimpleNamespace(responses=SimpleNamespace(create=mock))
            outcome=await client.request('request',docs.DOCUMENT_TOOL,max_output_tokens=64)
            assert outcome['error']=='ConnectionError'
            assert budget.actual==0 and budget.uncertain==budget.committed>0
            assert not (tmp_path/'cache.jsonl').exists()
    asyncio.run(run())


def test_gpt6_pricing_leaves_historical_default_unchanged():
    from belief_transfer.generation import llm
    usage=response().usage
    assert llm.MODEL=='gpt-5.6-luna'
    assert llm.estimate_cost_usd('gpt-6-luna',usage)==pytest.approx((100*.1+10*.5)/1_000_000)
    assert llm.estimate_cost_usd(llm.MODEL,usage)==pytest.approx((100*.2+10*1.2)/1_000_000)


def test_versioned_composition_and_expanded_scope():
    from belief_transfer.dataset import stance_document_prompts_v2 as v2
    original = job()
    matched = load_job(['+run=ethics_sft_documents_pilot_v2'])
    expanded = load_job(['+run=ethics_sft_documents_expanded_v1'])
    assert original.stance_sdf_pilot.prompt_version == 'v1'
    assert matched.stance_sdf_pilot.prompt_version == expanded.stance_sdf_pilot.prompt_version == 'v2'
    assert stage.subjects_for(original) == stage.subjects_for(matched)
    assert len(stage.subjects_for(expanded)) == 7
    subject = stage.subjects_for(matched)[0]
    idea = {'focus': 'Weighing reasons', 'outline': ['scope', 'principle', 'objection', 'conclusion']}
    prompt = v2.document_prompt(subject, 'position_note', idea, 'negative', 400, 600)
    assert 'protected_conditions' in prompt and subject['negation'] in prompt
    assert 'English words' not in prompt
    assert 'final\ndocument WILL explain and defend' in v2.forms_prompt(subject)
    assert 'If already in range' in v2.revision_prompt(subject, 'position_note', idea,
        'negative', 'draft', 500, 400, 600)
    assert len(v2.calibration_cases(stage.subjects_for(matched))) == 4


def test_v2_stage_records_calibration_and_prompt_version(tmp_path, monkeypatch):
    generated, results = setup_stage(tmp_path, monkeypatch)
    monkeypatch.setattr(stage, 'DocumentClient', FakeClient)
    j = load_job(['+run=ethics_sft_documents_pilot_v2'])
    asyncio.run(stage.run(j))
    root = generated / j.experiment.id / j.run_id
    assert len((root/'reviewer_calibration.jsonl').read_text().splitlines()) == 4
    assert (root/'reviewer_calibration.md').exists()
    manifest = json.loads((results/j.experiment.id/j.run_id/'pilot_manifest.json').read_text())
    assert manifest['prompt_version'] == 'v2' and manifest['completed_revisions'] == 48
    requests = [json.loads(s) for s in (root/'requests.jsonl').read_text().splitlines()]
    assert all('protected_conditions' in r['prompt'] for r in requests if r['phase'] == 'draft')
