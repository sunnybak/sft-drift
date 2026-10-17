"""Controls for measurement failure modes; no model weights."""
import asyncio
import json
from typing import get_args
import pytest
from pydantic import ValidationError
from belief_transfer.metrics.instrument import summarize_instrument
from belief_transfer.schemas import BeliefDefinition, InstrumentValidationSpec, StanceClaim, InstrumentCheck
from belief_transfer.validation.instrument import build_observations, parse_answer, scorer_controls


def spec(checks):
    return InstrumentValidationSpec(checks=checks, belief=BeliefDefinition(
        id='test', version='1', domain='test', scope='A hypothetical case.',
        stance=StanceClaim(id='core', statement='X is acceptable.',
            negation='It is not the case that X is acceptable.', paraphrases=['X is permissible.']),
        semantic_review='test fixture'))


def answered(bank,positive='agree',negative='disagree'):
    return [r.model_dump() | {'answer':positive if r.polarity=='positive' else negative} for r in bank]


@pytest.mark.parametrize('p,n,signed,absolute',[
    ('agree','disagree',0,0),('disagree','agree',0,0),('agree','agree',1,1),
    ('disagree','disagree',-1,1),('unresolved','unresolved',None,None)])
def test_negation_does_not_mistake_unknown_or_no_sayer_for_belief(p,n,signed,absolute):
    bank=build_observations(spec(['negation']))
    cell=summarize_instrument([r.model_dump() for r in bank],answered(bank,p,n))['negation']['claims']['core']
    assert cell['signed_acquiescence']==signed
    assert cell['absolute_acquiescence']==absolute
    assert cell['n_determinate_pairs']==(0 if p=='unresolved' else 6)


def test_opposing_acquiescence_cannot_cancel():
    bank=build_observations(spec(['negation'])); responses=answered(bank)
    for r in responses: r['answer']='agree' if r['arrangement']<3 else 'disagree'
    cell=summarize_instrument([r.model_dump() for r in bank],responses)['negation']['claims']['core']
    assert cell['signed_acquiescence']==0 and cell['absolute_acquiescence']==1


def test_missing_order_is_a_failure_not_stability():
    bank=build_observations(spec(['option_order']))
    report=summarize_instrument([r.model_dump() for r in bank],answered(bank)[:-1])['option_order']
    assert report['n_expected']==6 and report['n_valid']==5
    assert report['coverage_status']=='incomplete'
    assert report['claims']['core']['stable'] is None


def test_slot_bias_and_strict_format():
    bank=build_observations(spec(['option_order']))
    responses=[r.model_dump() | {'answer':parse_answer('A',r.options)} for r in bank]
    assert summarize_instrument([r.model_dump() for r in bank],responses)['option_order']['claims']['core']['stable'] is False
    assert parse_answer('A because it is right',bank[0].options) is None
    assert scorer_controls()['status']=='passed'


def test_duplicate_or_mismatched_prompts_rejected():
    bank=build_observations(spec(['negation'])); expected=[r.model_dump() for r in bank]; responses=answered(bank)
    with pytest.raises(ValueError,match='duplicate'): summarize_instrument(expected,responses+[responses[0]])
    responses[0]['prompt_sha']='changed'
    with pytest.raises(ValueError,match='frozen prompt'): summarize_instrument(expected,responses)


def test_each_check_runs_independently():
    for check in get_args(InstrumentCheck):
        assert all(r.benchmark==check for r in build_observations(spec([check])))
    assert len(build_observations(spec(['responsiveness'])))==36
    assert len(build_observations(spec(['comprehension'])))==18


def test_nonmoral_controls_use_supplied_property():
    cfg=spec(['responsiveness']); cfg.belief.domain='software'
    cfg.belief.stance.statement='X has lower latency.'
    cfg.belief.stance.negation='It is not true that X has lower latency.'
    bank=build_observations(cfg)
    assert all('ethically acceptable' not in r.prompt for r in bank)
    assert any('take as true: X has lower latency.' in r.prompt for r in bank)


def test_invalid_definitions_and_providers():
    cfg=spec(['negation']).belief.model_dump(); cfg['facets']=[cfg['stance']]
    with pytest.raises(ValidationError,match='unique'): BeliefDefinition(**cfg)
    with pytest.raises(ValidationError,match='adapter'): InstrumentValidationSpec(provider='openai',adapter='/fake')
    with pytest.raises(ValueError,match='requires'): build_observations(InstrumentValidationSpec(checks=['negation']))


@pytest.mark.parametrize('provider',['local','openai','anthropic'])
@pytest.mark.parametrize('check',get_args(InstrumentCheck))
def test_stage_uses_shared_interface_and_preserves_artifacts(make_job,tmp_path,monkeypatch,provider,check):
    from belief_transfer.stages import instrument_validation as stage
    captured=[]
    class FakeModel:
        def __init__(self):
            from types import SimpleNamespace
            self.client=SimpleNamespace(records=[])
            self.batch_responses=[]
        def generate(self,prompts,temperature=0):
            self.batch_responses=[{'stop_reason':'end_turn'} for _ in prompts]
            captured.extend(prompts); return ['A']*len(prompts)
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'local_model',lambda *a,**k:FakeModel())
    monkeypatch.setattr(stage,'ApiModel',lambda *a,**k:FakeModel())
    monkeypatch.setattr(stage,'AnthropicModel',lambda *a,**k:FakeModel())
    monkeypatch.setattr(stage,'write_result',lambda result:tmp_path/'result.yaml')
    j=make_job(['+run=instrument_ethics_v1',f'instrument_validation.provider={provider}',
                f'instrument_validation.checks=[{check}]'])
    result=asyncio.run(stage.run(j)); d=tmp_path/'data/results/factory_farming/instrument_ethics_v1'
    assert len(captured)=={'scorer_controls':0,'format':18,'comprehension':18,'option_order':6,'negation':12,'paraphrase':12,'responsiveness':36}[check]
    assert (d/'instrument_bank.jsonl').exists()
    rows=[json.loads(line) for line in (d/'instrument_observations.jsonl').read_text().splitlines()]
    assert all(r['response']=='A' and r['prompt'] for r in rows)
    if check=='scorer_controls':
        assert result.metrics['checks'][check]['status']=='passed'
    else:
        assert result.metrics['checks'][check]['n_valid']==len(captured)
        assert result.metrics['model']['provider']==provider
    with pytest.raises(FileExistsError): asyncio.run(stage.run(j))


def test_api_wrapper_orders_replies_and_disables_cache(monkeypatch):
    from belief_transfer.inference import model as module
    from types import SimpleNamespace
    calls={}
    class Client:
        def __init__(self,**kwargs): calls.update(kwargs)
        async def __aenter__(self): return self
        async def __aexit__(self,*a): pass
        async def batch(self,prompts,**kwargs):
            calls.update(kwargs)
            for i in reversed(range(len(prompts))): yield SimpleNamespace(index=i,text=str(i))
    monkeypatch.setattr(module.llm,'Client',Client)
    assert module.ApiModel('test',throughput=2,use_cache=False).generate(['x','y'])==['0','1']
    assert calls['use_cache'] is False and calls['throughput']==2


def test_paraphrase_change_and_missingness_are_not_hidden():
    bank=build_observations(spec(['paraphrase'])); expected=[r.model_dump() for r in bank]
    responses=answered(bank)
    for r in responses:
        if r['wording']=='1': r['answer']='disagree'
    cell=summarize_instrument(expected,responses)['paraphrase']['claims']['core']
    assert cell['stable_rate']==0
    assert summarize_instrument(expected,responses[:-1])['paraphrase']['claims']['core']['stable_rate'] is None


def test_responsiveness_separates_content_and_null_controls():
    bank=build_observations(spec(['responsiveness'])); responses=answered(bank)
    for r in responses: r['answer']='disagree' if r['condition']=='negative' else 'agree'
    cell=summarize_instrument([r.model_dump() for r in bank],responses)['responsiveness']['claims']['core']
    assert cell['prompted_contrast']==1
    assert cell['neutral_shift']==0 and cell['offtopic_contrast']==0
    assert cell['conditions']['negative']['expected_answer_rate']==1


def test_stage_records_execution_failure_without_fabricated_scores(make_job,tmp_path,monkeypatch):
    from belief_transfer.stages import instrument_validation as stage
    class Broken:
        def generate(self,*args,**kwargs): raise RuntimeError('unavailable')
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'ApiModel',lambda *a,**k:Broken())
    monkeypatch.setattr(stage,'write_result',lambda r:tmp_path/'result.yaml')
    j=make_job(['+run=instrument_ethics_v1','instrument_validation.provider=openai',
                'instrument_validation.checks=[negation]'])
    r=asyncio.run(stage.run(j))
    assert r.metrics['execution_status']=='failed'
    cell=r.metrics['checks']['negation']['claims']['acceptability']
    assert cell['n_incomplete_pairs']==6 and cell['signed_acquiescence'] is None


def test_scorer_only_never_constructs_a_model(make_job,tmp_path,monkeypatch):
    from belief_transfer.stages import instrument_validation as stage
    def forbidden(*args,**kwargs): raise AssertionError('model loaded for CPU scorer controls')
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'local_model',forbidden)
    monkeypatch.setattr(stage,'write_result',lambda r:tmp_path/'result.yaml')
    j=make_job(['+run=adhoc','stage=instrument_validation','instrument_validation.checks=[scorer_controls]'])
    r=asyncio.run(stage.run(j))
    assert r.metrics['checks']['scorer_controls']['status']=='passed'
    assert r.metrics['model'] is None


def test_definition_typos_fail_instead_of_dropping_semantics():
    claim=spec(['negation']).belief.stance.model_dump()
    claim['parapharses']=['Another wording']
    with pytest.raises(ValidationError,match='Extra inputs'): StanceClaim(**claim)


def test_response_cannot_rewrite_ground_truth():
    bank=build_observations(spec(['comprehension'])); responses=answered(bank)
    for r in responses: r['expected']='agree'
    report=summarize_instrument([r.model_dump() for r in bank],responses)['comprehension']['claims']
    assert report['arithmetic_false']['accuracy']==0


def test_unpriced_api_model_is_rejected_before_call(make_job,tmp_path,monkeypatch):
    from belief_transfer.stages import instrument_validation as stage
    def forbidden(*args,**kwargs): raise AssertionError('API constructed before preflight')
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'ApiModel',forbidden)
    j=make_job(['+run=instrument_ethics_v1','instrument_validation.provider=openai',
                'instrument_validation.model=unpriced','instrument_validation.checks=[format]'])
    with pytest.raises(ValueError,match='cost accounting'): asyncio.run(stage.run(j))
    assert not (tmp_path/'data').exists()


def test_null_can_change_rejection_to_unknown_without_agreement_change():
    bank=build_observations(spec(['responsiveness'])); responses=answered(bank)
    for r in responses: r['answer']='unresolved' if r['condition']=='offtopic_positive' else 'disagree'
    c=summarize_instrument([r.model_dump() for r in bank],responses)['responsiveness']['claims']['core']
    assert c['offtopic_contrast']==0
    assert c['offtopic_answer_change_rate']==1
