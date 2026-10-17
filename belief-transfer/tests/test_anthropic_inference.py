"""Anthropic transport/usage tests without network calls or real credentials."""
import json
from urllib.error import HTTPError

import pytest

from belief_transfer.generation import anthropic
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.model import AnthropicModel


def envelope(text='A',stop='end_turn'):
    return {'id':'msg_test','model':anthropic.MODEL,'content':[{'type':'text','text':text}],
            'stop_reason':stop,'usage':{'input_tokens':100,'output_tokens':2,'cache_read_input_tokens':10}}


def test_payload_credentials_and_cost_accounting(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY','secret-for-test')
    captured=[]
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return json.dumps(envelope()).encode()
    def open_(request,timeout):
        captured.append(request)
        return Response()
    monkeypatch.setattr(anthropic,'urlopen',open_)
    context=RunContext(); client=anthropic.Client(context=context)
    assert client.complete('unchanged prompt')['stop_reason']=='end_turn'
    body=json.loads(captured[0].data)
    assert body['messages']==[{'role':'user','content':'unchanged prompt'}]
    assert body['thinking']=={'type':'between_tools'}
    assert 'temperature' not in body and 'system' not in body
    assert 'secret-for-test' not in json.dumps(client.records)
    assert context.calls[0].input_tokens==110
    assert context.calls[0].cost_usd==pytest.approx((100*2+10*.2+2*10)/1_000_000)


def test_configuration_fails_before_calls(monkeypatch):
    with pytest.raises(ValueError,match='frozen'): anthropic.Client('unknown')
    monkeypatch.delenv('ANTHROPIC_API_KEY',raising=False)
    with pytest.raises(ValueError,match='ANTHROPIC_API_KEY'): anthropic.Client()


def test_rate_limit_retry_and_authentication_failure(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY','test')
    monkeypatch.setattr(anthropic.time,'sleep',lambda seconds:None)
    calls=[]
    def fail(request,timeout):
        calls.append(1)
        raise HTTPError(request.full_url,429,'rate limited',None,None)
    monkeypatch.setattr(anthropic,'urlopen',fail)
    with pytest.raises(RuntimeError,match='HTTP 429'): anthropic.Client().complete('prompt')
    assert len(calls)==4
    calls.clear()
    def unauthorized(request,timeout):
        calls.append(1)
        raise HTTPError(request.full_url,401,'unauthorized',None,None)
    monkeypatch.setattr(anthropic,'urlopen',unauthorized)
    with pytest.raises(RuntimeError,match='HTTP 401'): anthropic.Client().complete('prompt')
    assert len(calls)==1


def test_wrapper_preserves_order_and_envelopes(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY','test')
    model=AnthropicModel(throughput=2)
    monkeypatch.setattr(model.client,'complete',lambda prompt:envelope(prompt))
    assert model.generate(['A','B','C'])==['A','B','C']
    assert len(model.batch_responses)==3


def test_non_end_turn_answer_is_not_a_valid_measurement(make_job,tmp_path,monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from belief_transfer.stages import instrument_validation as stage
    class Truncated:
        client=SimpleNamespace(records=[])
        batch_responses=[]
        def generate(self,prompts,temperature=0):
            self.batch_responses=[envelope(stop='max_tokens') for _ in prompts]
            return ['A']*len(prompts)
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'AnthropicModel',lambda *a,**k:Truncated())
    monkeypatch.setattr(stage,'write_result',lambda r:tmp_path/'result.yaml')
    job=make_job(['+run=instrument_anthropic_ethics_v1','instrument_validation.checks=[negation]'])
    result=asyncio.run(stage.run(job))
    assert result.metrics['checks']['negation']['n_valid']==0
    assert result.metrics['checks']['negation']['claims']['acceptability']['n_determinate_pairs']==0
