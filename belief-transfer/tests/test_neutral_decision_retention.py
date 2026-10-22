"""Supplemental decision assessment and stage tests; no real weights or results."""
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_replay_coverage_probe import decision_bank
from build_replay_coverage import candidates
from belief_transfer.config import load_job
from belief_transfer.schemas import NeutralDecisionRetentionSpec
from belief_transfer.evals.neutral_decision_retention import assess, summarize
from belief_transfer.stages import neutral_decision_retention as stage


def item(thinking=False, expected='endorse'):
    return {'prompt': 'An independent factual request.', 'thinking': thinking, 'expected': expected}


@pytest.mark.parametrize('text,mode,expected,value,strict,diagnostic', [
    ('endorse', False, 'endorse', True, True, None),
    ('reject', False, 'endorse', False, True, 'WRONG_DECISION_VALUE'),
    ('ENDORSE', False, 'endorse', True, False, None),
    ('endorse.', False, 'endorse', None, False, 'UNSUPPORTED_OR_AMBIGUOUS_FINAL'),
    ('endorse reject', False, 'endorse', None, False, 'UNSUPPORTED_OR_AMBIGUOUS_FINAL'),
    ('<think>\nThe fact is true.\n</think>\n\nreject', True, 'endorse', False, True, 'WRONG_DECISION_VALUE'),
    ('<think>\nStill thinking', True, 'endorse', None, False, 'INCOMPLETE_OR_INVALID_BOUNDARIES'),
    (None, False, 'endorse', None, False, 'MISSING_RESPONSE'),
])
def test_value_format_boundaries_and_missing_stay_separate(text, mode, expected, value, strict, diagnostic):
    result = assess(text, item(mode, expected), normal_stop=True)
    assert result['value_correct'] is value
    assert result['strict_format'] is strict
    assert result['diagnostic'] == diagnostic


def test_cap_does_not_receive_value_even_if_word_looks_correct():
    result = assess('endorse', item(), normal_stop=False)
    assert result['value_correct'] is None and result['parsed_word'] is None


def bank():
    rows = decision_bank(candidates())
    for r in rows:
        r['expected_input_token_ids'] = list(map(ord, r['prompt']))
    return rows


def test_pair_denominators_and_unscorable_pairs_explicit():
    data = bank()
    observations = [{**r, 'assessment': assess(
        '<think>\nProof.\n</think>\n\n' + r['expected'] if r['thinking'] else r['expected'],
        r, normal_stop=True)} for r in data]
    result = summarize(observations)
    assert result['pairs']['note']['eligible_pairs'] == 32
    assert result['pairs']['note']['agreement'] == 1
    assert result['pairs']['polarity']['agreement'] == 1
    observations[0]['assessment'] = assess(None, observations[0], normal_stop=False)
    result = summarize(observations)
    assert result['pairs']['note']['eligible_pairs'] == 31
    assert result['pairs']['note']['unscorable_pairs'] == 1
    with pytest.raises(ValueError, match='all64'):
        summarize(observations[:-1])


class Tokenizer:
    eos_token_id = 1000000

    def decode(self, tokens, **kwargs):
        return ''.join(map(chr, tokens))


def reply(row, *, wrong_seed=False, cap=False):
    text = '<think>\nProof.\n</think>\n\n' + row['expected'] if row['thinking'] else row['expected']
    tokens = list(map(ord, text)) + ([] if cap else [Tokenizer.eos_token_id])
    return text, {'output_token_ids': tokens, 'input_token_ids': row['expected_input_token_ids'],
                  'model_revision': 'a' * 40, 'adapter_lora_id': None,
                  'sampling_seed': row['seed'] + int(wrong_seed),
                  'generation_tokens': len(tokens), 'finish_reason': 'length' if cap else 'stop'}


def test_request_identity_mismatch_does_not_count_correct():
    row = bank()[0]
    result = stage.observation(row, reply(row, wrong_seed=True), Tokenizer(), revision='a'*40, adapter=False)
    assert result['error'] == 'DECISION_REQUEST_IDENTITY_MISMATCH'
    assert result['assessment']['value_correct'] is None


@pytest.mark.parametrize('failed_batch', [False, True])
def test_stage_preserves_all_records_and_refuses_overwrite(tmp_path, monkeypatch, failed_batch):
    data = bank()
    source = tmp_path / 'bank.jsonl'
    source.write_text(''.join(json.dumps(r) + '\n' for r in data))
    job = load_job(['+run=ethics_gpu_retention_rca_base_v2'])
    spec = NeutralDecisionRetentionSpec(model_label='base', bank_path='bank.jsonl',
        bank_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    job = job.model_copy(update={'stage': 'neutral_decision_retention', 'run_id': 'ethics_gpu_mock_decision',
        'neutral_decision_retention': spec, 'instruction_retention': None})
    bench = job.pilot_bench.model_copy(update={'cuda_generation':
        job.pilot_bench.cuda_generation.model_copy(update={'revision': 'a'*40})})
    job = job.model_copy(update={'pilot_bench': bench})
    calls = []
    lookup = {(r['prompt'], r['thinking']): r for r in data}
    class Model:
        _tokenizer = Tokenizer()
        enable_thinking = True
        def generate_batch_with_metadata(self, prompts, **kwargs):
            calls.append((self.enable_thinking, kwargs['temperature'], kwargs['seeds']))
            if failed_batch and not self.enable_thinking:
                raise RuntimeError('mock backend failure')
            return [reply(lookup[p, self.enable_thinking]) for p in prompts]
    monkeypatch.setattr(stage, 'ROOT', tmp_path)
    monkeypatch.setattr(stage, 'require_training_backend', lambda: None)
    monkeypatch.setattr(stage, 'backend_info', lambda **kwargs: SimpleNamespace(model_dump=lambda: {}))
    monkeypatch.setattr(stage, 'local_model', lambda *args, **kwargs: Model())
    monkeypatch.setattr(stage, 'version', lambda name: 'mock')
    monkeypatch.setattr(stage, 'write_resolved_config', lambda *args: None)
    monkeypatch.setattr(stage, 'code_revision', lambda: 'mock')
    monkeypatch.setattr(stage, 'build_result', lambda *args, **kwargs: kwargs)
    monkeypatch.setattr(stage, 'write_result', lambda result: None)
    asyncio.run(stage.run(job))
    parent = tmp_path / 'data/results' / job.experiment.id / job.run_id
    records = list(map(json.loads, (parent / 'responses.jsonl').read_text().splitlines()))
    assert len(records) == 64 and (parent / 'responses.md').is_file()
    assert [(mode, temp) for mode, temp, _ in calls] == [(True, .6), (False, 0)]
    assert sum(r['response'] is None for r in records) == (32 if failed_batch else 0)
    with pytest.raises(FileExistsError):
        asyncio.run(stage.run(job))


def test_opt_in_does_not_appear_in_historical_config_serialization():
    job = load_job(['+run=ethics_gpu_retention_rca_base_v2'])
    assert 'neutral_decision_retention' not in job.model_dump()
