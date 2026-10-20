"""Engine identity, generation metadata and failures with no model weights."""
import sys
from types import SimpleNamespace

import pytest

from belief_transfer.inference.local import local_model
from belief_transfer.inference.vllm_model import VLLMModel
from belief_transfer.schemas import CUDAGenerationSpec, ModelSpec, ModelsConfig, PilotBenchSpec
from belief_transfer.stages.measurements import decoding_record
from test_cuda_measurement_batch import fake_hf

REVISION = '1' * 40


def spec(engine):
    return CUDAGenerationSpec(engine=engine, revision=REVISION)


def test_optional_engine_leaves_historical_identity_unchanged():
    normal = PilotBenchSpec(measurement_batch_size=8)
    assert 'cuda_generation' not in normal.model_dump()
    old = decoding_record(normal)
    compiled = PilotBenchSpec(measurement_batch_size=8, cuda_generation=spec('hf_compiled'))
    record = decoding_record(compiled)
    assert record['execution']['revision'] == REVISION
    assert record['sampling_seed_strategy'] == 'per-token-v1'
    assert 'execution' not in old
    assert record != old


def test_explicit_engines_cannot_silently_fall_back_to_cpu():
    models = ModelsConfig(models={'qwen': ModelSpec(pretrained='fake')})
    with pytest.raises(ValueError, match='require CUDA'):
        local_model('qwen', models, backend='cpu', generation=spec('hf_compiled'))


def test_compiled_request_requires_real_activation_and_keeps_metadata():
    m = fake_hf()
    m.generation = spec('hf_compiled')
    original = m._hf_model.generate
    seen = []

    def generate(**kwargs):
        seen.append(kwargs)
        m._hf_model._compiled_call = object()
        return original(**kwargs)

    m._hf_model.generate = generate
    _, meta = m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)[0]
    assert seen[0]['cache_implementation'] == 'static'
    assert seen[0]['compile_config'].mode == 'reduce-overhead'
    assert meta['execution']['engine'] == 'hf_compiled'
    assert meta['compiled_call_present'] is True
    del m._hf_model._compiled_call
    m._hf_model.generate = original
    with pytest.raises(RuntimeError, match='did not activate'):
        m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)
    m.generation.max_model_len = 1
    with pytest.raises(ValueError, match='context capacity'):
        m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)


def fake_vllm(monkeypatch):
    monkeypatch.setitem(sys.modules, 'vllm', SimpleNamespace(SamplingParams=lambda **kw: SimpleNamespace(**kw)))
    monkeypatch.setattr('belief_transfer.inference.execution.version', lambda package: 'test-version')
    models = ModelsConfig(models={'qwen': ModelSpec(pretrained='fake')})
    m = VLLMModel('qwen', models, generation=spec('vllm'), max_new_tokens=8,
                  enable_thinking=True, top_p=.95, top_k=20, min_p=0)
    m._tokenizer = SimpleNamespace(apply_chat_template=lambda messages, **kw: messages[0]['content'],
        encode=lambda text, **kw: [ord(c) for c in text], decode=lambda ids, **kw: 'reply')
    m.calls = []

    def generate(inputs, params, **kwargs):
        m.calls.append((inputs, params, kwargs))
        return [SimpleNamespace(prompt_token_ids=x['prompt_token_ids'], outputs=[SimpleNamespace(
            token_ids=[4, 5, 0], finish_reason='stop', stop_reason=None)]) for x in inputs]

    m._engine = SimpleNamespace(generate=generate)
    return m


def test_vllm_has_explicit_distinct_rng_identity_and_no_retokenized_inputs(monkeypatch):
    m = fake_vllm(monkeypatch)
    outputs = m.generate_batch_with_metadata(['abc', 'q'], seeds=[7, 91], temperature=.6, batch_size=2)
    for i, (_, meta) in enumerate(outputs):
        assert meta['input_token_ids'] == list(map(ord, ['abc', 'q'][i]))
        assert meta['output_token_ids'] == [4, 5, 0]
        assert meta['sampling_seed'] == [7, 91][i]
        assert meta['sampling_seed_strategy'] == 'vllm-per-request-v1'
        assert meta['model_revision'] == REVISION
        assert meta['max_num_seqs'] == 64
        assert meta['execution_versions']['vllm'] == 'test-version'
    assert [p.seed for p in m.calls[0][1]] == [7, 91]
    assert all(p.top_k == 20 and p.top_p == .95 for p in m.calls[0][1])
    record = decoding_record(PilotBenchSpec(cuda_generation=spec('vllm'), measurement_batch_size=256))
    assert record['sampling_seed_strategy'] == 'vllm-per-request-v1'
    assert record['batch_size'] == 256


def test_vllm_rejects_incomplete_reordered_and_oversized_requests(monkeypatch):
    m = fake_vllm(monkeypatch)
    with pytest.raises(ValueError, match='Aligned'):
        m.generate_batch_with_metadata(['abc'], seeds=[], temperature=.6, batch_size=1)
    m._engine.generate = lambda *a, **kw: []
    with pytest.raises(ValueError, match='request count'):
        m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)
    m._engine.generate = lambda *a, **kw: [SimpleNamespace(prompt_token_ids=[999], outputs=[])]
    with pytest.raises(ValueError, match='input identity'):
        m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)
    m.generation.max_model_len = 1
    with pytest.raises(ValueError, match='context capacity'):
        m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)


def test_vllm_must_confirm_the_requested_adapter(monkeypatch):
    m = fake_vllm(monkeypatch)
    m._lora = SimpleNamespace(lora_int_id=1)
    with pytest.raises(ValueError, match='confirm the requested adapter'):
        m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)
    generate = m._engine.generate

    def confirmed(*a, **kw):
        rows = generate(*a, **kw)
        assert kw['lora_request'] is m._lora
        for r in rows:
            r.lora_request = m._lora
        return rows

    m._engine.generate = confirmed
    _, metadata = m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)[0]
    assert metadata['adapter_lora_id'] == 1
