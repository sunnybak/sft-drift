"""Paired missing-value accounting and raw measurement reconstruction, no weights."""
import copy
import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_replay_value_probe import paired_values, audit_surface
from prepare_replay_weight_ablation import write_rows
from belief_transfer.metrics.measurements import request_sampling_seed
from belief_transfer.stages.measurements import observed_backend_reply


def values(kind):
    field, family, n = ('value', 'family', 64) if kind == 'retention' else ('assessment', 'operation', 32)
    return [{'example_id': f'{mode}/{i}', 'thinking': mode, family: 'sum',
        field: {'value_correct': True}, 'response_sha256': 'a'*64}
        for mode in (True, False) for i in range(n)]


@pytest.mark.parametrize('kind', ['retention', 'decisions'])
def test_known_missing_reply_remains_unknown_and_bounds_are_explicit(kind):
    control = values(kind); candidate = copy.deepcopy(control)
    field = 'value' if kind == 'retention' else 'assessment'
    candidate[0][field]['value_correct'] = None
    candidate[1][field]['value_correct'] = False
    summary, pairs = paired_values(control, candidate, control, kind=kind)
    group = summary['True/base_known']
    assert group['candidate_unscorable'] == 1
    assert group['accuracy_difference_pp'] is None
    assert group['difference_missing_bounds_pp'] == [-200/group['n'], -100/group['n']]
    assert len(group['losses']) == 1 and len(group['unscorable_transitions']) == 1
    assert pairs[0]['candidate_correct'] is None


@pytest.mark.parametrize('defect', ['duplicate', 'missing', 'mode', 'foreign_known'])
def test_invalid_pairing_rejected(defect):
    control = values('decisions'); candidate = copy.deepcopy(control); known = copy.deepcopy(control)
    if defect == 'duplicate':candidate[-1] = candidate[0]
    if defect == 'missing':candidate.pop()
    if defect == 'mode':candidate[0]['thinking'] = not candidate[0]['thinking']
    if defect == 'foreign_known':known[0]['example_id'] = 'foreign'
    with pytest.raises(ValueError):
        paired_values(control, candidate, known, kind='decisions')


class Tokenizer:
    def apply_chat_template(self, messages, **kwargs):return messages[0]['content']
    def encode(self, text, **kwargs):return list(text.encode())
    def decode(self, tokens, **kwargs):return 'endorse'


@pytest.mark.parametrize('defect', [None, 'input', 'seed', 'adapter', 'saved_reply'])
def test_surface_token_audit_reconstructs_frozen_replies_and_detects_identity_errors(tmp_path, defect):
    tokenizer = Tokenizer()
    generation = SimpleNamespace(revision='revision', model_dump=lambda: {'engine': 'vllm'})
    spec = SimpleNamespace(seed=42, measurement_decoding=SimpleNamespace(thinking=False), cuda_generation=generation)
    for bank_name, reply_name in [('stance_bank','stance_observations'), ('stance_control_bank','stance_controls')]:
        row = {'presentation_id': bank_name, 'prompt': bank_name, 'prompt_sha': hashlib.sha256(bank_name.encode()).hexdigest(),
            'options': ['agree','disagree'], 'response_format': 'stance_word', 'display_options': ['endorse','reject']}
        seed = request_sampling_seed(row, 42)
        metadata = {'input_token_ids': tokenizer.encode(row['prompt']), 'sampling_seed': seed,
            'model_revision': 'revision', 'adapter_lora_id': 1, 'execution': {'engine':'vllm'},
            'execution_versions': {'vllm':'version'}, 'output_token_ids': [3,9],
            'generation_tokens': 2, 'prompt_tokens': len(row['prompt']), 'finish_reason': 'stop'}
        observed = observed_backend_reply(row, 'endorse', metadata, thinking=False, seed=seed)
        if bank_name == 'stance_bank':
            if defect == 'input':metadata['input_token_ids'] = [1]
            if defect == 'seed':metadata['sampling_seed'] += 1
            if defect == 'adapter':metadata['adapter_lora_id'] = None
            if defect == 'saved_reply':observed['response'] = 'reject'
        write_rows(tmp_path/(bank_name+'.jsonl'),[row])
        write_rows(tmp_path/(reply_name+'.jsonl'),[observed])
    audit = audit_surface(tmp_path, spec, tokenizer, {'versions': {'vllm':'version'}})
    assert audit['records'] == 2
    assert audit['passed'] is (defect is None)
    assert len(audit['mismatches']) == (0 if defect is None else 1)
