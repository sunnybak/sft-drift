"""Corpus preparation, bounded generation and interruption safety without API/weights."""
import asyncio
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from belief_transfer.config import load_job
from belief_transfer.dataset import stance_corpus as corpus
from belief_transfer.dataset import stance_corpus_prompts as prompts
from belief_transfer.dataset import stance_documents as docs
from belief_transfer.generation.corpus_journal import CorpusJournal
from belief_transfer.generation.document_client import BudgetExceeded
from belief_transfer.stages import stance_corpus as stage


def job():
    return load_job(['+run=ethics_sft_pooled_corpus_v2'])


def test_full_plan_shared_slots_and_complementary_category_balance():
    j = job()
    subjects = stage.subjects_for(j)
    assert Counter(s['role'] for s in subjects) == {'ethical': 90, 'offtopic_training_control': 9}
    plan = corpus.schedule(subjects, 100, 500, 5, 42)
    counts = Counter()
    forms = {}
    for batch in plan:
        counts[batch['subject_id']] += len(batch['slots'])*2
        forms.setdefault(batch['subject_id'], Counter())[batch['form']] += len(batch['slots'])
        assert 1 <= len(batch['slots']) <= 5
    assert sum(counts.values()) == 27000
    assert all(counts[s['id']] == (200 if s['role'] == 'ethical' else 1000) for s in subjects)
    assert all(max(c.values())-min(c.values()) <= 1 for c in forms.values())
    arms = corpus.assignments(subjects, 42)
    assert Counter(arms['mixed_a'].values()) == {'positive': 45, 'negative': 45}
    assert all(arms['mixed_a'][k] != arms['mixed_b'][k] for k in arms['mixed_a'])
    assert corpus.schedule(subjects,100,500,5,42) == plan
    assert len({s['category'] for s in subjects if s['role']=='ethical'}) == 9
    hashes = stage.contract_for(j, subjects)['source_hashes']
    assert len(hashes) == 7
    assert 'stages/stance_corpus.py' in hashes and 'dataset/stance_corpus.py' in hashes
    for category in {s['category'] for s in subjects if s['role']=='ethical'}:
        assert Counter(arms['mixed_a'][s['id']] for s in subjects
                       if s['role']=='ethical' and s['category']==category) == {'positive':5,'negative':5}


def test_prompts_explicitly_route_opponent_and_keep_fixed_premises():
    subject = stage.subjects_for(job())[0]
    idea = dict(focus='Relative weights', positive_reason='PRO REASON',
                negative_reason='CON REASON', development='Develop the tension')
    for position, own, other in [('positive','PRO REASON','CON REASON'), ('negative','CON REASON','PRO REASON')]:
        prompt = prompts.document_prompt(subject,'editorial',idea,position,400,600)
        assert f'Develop this supporting reason: {own}' in prompt
        assert f'Address this opposing reason as an objection: {other}' in prompt
        assert subject['scope'] in prompt
    schema = prompts.review_tool(subject).parameters
    assert len(schema['properties']['condition_checks']['properties']) == len(subject['conditions'])
    assert 'the brief' in prompts.RULES
    assert 'No material risk' in prompts.RULES


def test_journal_durability_recovery_and_unknown_charge_block(tmp_path):
    path=tmp_path/'journal.sqlite'
    journal=CorpusJournal(path)
    assert journal.begin('a','key',{'prompt':'exact'}) is None
    journal.close()
    journal=CorpusJournal(path)
    with pytest.raises(RuntimeError,match='may have been billed'):
        journal.reconcile()
    record={'cost_usd':0.05, 'error':None, 'payload':{'text':'saved'}}
    journal.set('key',{'record':record})
    journal.reconcile()
    assert journal.begin('a','key',{}) == record
    assert journal.spend() == (0.05,0)
    journal.begin('cached-copy','key',{})
    journal.reconcile()
    assert journal.spend() == (0.05,0)
    assert journal.duplicates('doc-a','hash') == []
    assert journal.duplicates('doc-b','hash') == ['doc-a']
    assert journal.duplicates('doc-a','hash') == ['doc-b']
    with pytest.raises(ValueError,match='identity changed'):
        journal.begin('a','newkey',{})
    journal.close()


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    j=job()
    j.stance_corpus.documents_per_position=3
    j.stance_corpus.control_documents_per_position=3
    monkeypatch.setattr(stage,'GENERATED_DIR',tmp_path/'generated')
    monkeypatch.setattr(stage.report,'RESULTS_DIR',tmp_path/'results')
    # One ethical subject suffices for fault/lineage tests; no real frozen result reads.
    subjects=stage.subjects_for(j)[:1]
    monkeypatch.setattr(stage,'subjects_for',lambda _:subjects)
    monkeypatch.setattr(stage,'load_tokenizer',lambda _:SimpleNamespace(encode=lambda text,**_:text.split()))
    frozen=tmp_path/'generated/ethical_pilot/ethics_100_bank_v3/belief_wordings.jsonl'
    frozen.parent.mkdir(parents=True)
    frozen.write_text('')
    asyncio.run(stage.run(j))
    return j,tmp_path/'generated'/j.experiment.id/j.run_id


class FakeClient:
    failure = None
    calls = []
    def __init__(self,**kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self,*args): pass
    async def request(self,prompt,tool,**kwargs):
        self.calls.append((prompt,tool.name))
        if self.failure == 'budget': raise BudgetExceeded('ceiling')
        if self.failure == 'truncated':
            return {'error':'response_incomplete','payload':None,'cost_usd':.01,'response':{'status':'incomplete'}}
        if tool.name=='plan_forms':
            payload={f:{'audience':'General audience','purpose':'Defend the assigned position'} for f in corpus.FORMS}
        elif tool.name=='plan_ideas':
            n=tool.parameters['properties']['ideas']['minItems']
            payload={'ideas':[{'focus':f'Focus {i}','positive_reason':'Pro','negative_reason':'Con','development':'Weigh reasons'} for i in range(n)]}
        elif tool.name=='submit_document': payload={'text':'READY' if 'text READY.' in prompt else 'This is a scoped statement.'}
        elif tool.name=='revise_document': payload={'critique':[],'text':'This is a revised scoped statement.'}
        else:
            checks=tool.parameters['properties']['condition_checks']['properties']
            payload={**{k:True for k in docs.REVIEW_KEYS}, 'condition_checks':{k:{'preserved':True,'evidence':'Scope'} for k in checks},
                     'unsupported_premises':[],'rationale':'Provisional','evidence':['Statement']}
        if self.failure=='malformed': payload={'unexpected':'field'}
        return {'payload':payload,'error':None,'cost_usd':.001,'response':{'id':'mock'}}


def test_prepare_no_api_overwrite_and_contract_guards(prepared):
    j,root=prepared
    assert len((root/'schedule.jsonl').read_text().splitlines())==3
    assert not (root/'requests.sqlite').exists()
    with pytest.raises(FileExistsError): asyncio.run(stage.run(j))
    j.stance_corpus.resume=True
    j.stance_corpus.min_tokens=300
    with pytest.raises(ValueError,match='contract changed'): asyncio.run(stage.run(j))


def test_bounded_generation_lineage_resume_and_markdown(prepared,monkeypatch):
    j,root=prepared
    monkeypatch.setattr(stage.document_client,'DocumentClient',FakeClient)
    FakeClient.failure=None; FakeClient.calls=[]
    j.stance_corpus.operation='generate'; j.stance_corpus.resume=True
    asyncio.run(stage.run(j))
    shard=next((root/'shards').iterdir())
    rows=[json.loads(s) for s in (shard/'documents.jsonl').read_text().splitlines()]
    assert len(rows)==2 and rows[0]['idea']==rows[1]['idea']
    assert rows[0]['draft_sha256']==docs.text_hash(rows[0]['draft'])
    assert rows[0]['sha256']==docs.text_hash(rows[0]['text'])
    assert all(r['tokens']==6 and 'token_length' in r['mechanical_flags'] for r in rows)
    assert rows[0]['intended_prefix']=='<DOCTAG>\n'
    assert all(not r['training_ready'] for r in rows)
    forms_before=sum(n=='plan_forms' for _,n in FakeClient.calls)
    asyncio.run(stage.run(j))
    assert len(list((root/'shards').iterdir()))==2
    assert sum(n=='plan_forms' for _,n in FakeClient.calls)==forms_before
    for path in root.rglob('*.jsonl'): assert path.with_suffix('.md').exists()
    journal=CorpusJournal(root/'requests.sqlite')
    assert journal.spend()[0]>0
    journal.close()


@pytest.mark.parametrize('failure,exception',[('truncated',RuntimeError),('malformed',ValueError),('budget',BudgetExceeded)])
def test_failures_preserved_and_budget_refusal_safe_to_resume(prepared,monkeypatch,failure,exception):
    j,root=prepared
    monkeypatch.setattr(stage.document_client,'DocumentClient',FakeClient)
    FakeClient.failure=failure
    j.stance_corpus.operation='generate'; j.stance_corpus.resume=True
    with pytest.raises(exception): asyncio.run(stage.run(j))
    journal=CorpusJournal(root/'requests.sqlite')
    journal.reconcile()  # All dispatched failures preserved, refused calls never pending.
    assert journal.spend()[0] == (0 if failure=='budget' else (.01 if failure=='truncated' else .001))
    journal.close()
    assert not list((root/'shards').glob('*'))
    FakeClient.failure=None


def test_payload_validation_and_mechanical_flags():
    with pytest.raises(ValueError): corpus.validate_payload({'text':''},docs.DOCUMENT_TOOL.parameters)
    with pytest.raises(ValueError): corpus.validate_payload({'text':'good','extra':'bad'},docs.DOCUMENT_TOOL.parameters)
    assert corpus.flags('According to the brief.',450,400,600)==['visible_task_metadata']


def test_historical_config_fingerprint_excludes_new_unset_stage():
    import hashlib
    from belief_transfer.config import config_sha
    old=load_job(['+run=ethics_sft_documents_expanded_v1'])
    previous=old.model_dump(mode='json',exclude={'run_id','smoke','force','stance_corpus'})
    expected=hashlib.sha256(json.dumps(previous,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12]
    assert config_sha(old)==expected


def test_c4_bounded_shards_resume_provenance_and_no_prefix(prepared,monkeypatch):
    import datasets
    j,root=prepared
    # Fresh contract for the changed background count/shard setting.
    j.run_id='ethics_sft_test_c4'
    j.stance_corpus.c4_documents=3
    j.stance_corpus.background_shard_size=2
    j.stance_corpus.resume=False
    j.stance_corpus.operation='prepare'
    asyncio.run(stage.run(j))
    root=root.parent/j.run_id
    class Stream:
        def shuffle(self,**kwargs):
            assert kwargs=={'seed':42,'buffer_size':1024}
            return iter([{'text':'one two','url':'u','timestamp':'t'}, {'text':'one two'},
                         {'text':'three four'}, {'text':'five six'}])
    def load(*args,**kwargs):
        assert kwargs['revision']==j.stance_corpus.c4_revision and kwargs['streaming']
        return Stream()
    monkeypatch.setattr(datasets,'load_dataset',load)
    j.stance_corpus.operation='background'; j.stance_corpus.resume=True
    asyncio.run(stage.run(j))
    assert len(list((root/'background').glob('*/documents.jsonl')))==1
    asyncio.run(stage.run(j))
    rows=[json.loads(line) for p in (root/'background').glob('*/documents.jsonl') for line in p.read_text().splitlines()]
    assert len(rows)==3 and len({r['sha256'] for r in rows})==3
    assert all(r['tokens']==2 and r['intended_prefix']=='' and not r['prefix_loss_masked'] for r in rows)
    assert next(r for r in rows if r['url']=='u')['timestamp']=='t'
