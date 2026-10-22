"""Finite worker, raw-token verification and review guards; mocks/tempdirs only."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_lower_lr_probe as worker
from belief_transfer.evals.fresh_retention import bank
from belief_transfer.evals.instruction_retention import assess
from belief_transfer.metrics.instruction_retention import report


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))


def grid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, parent = worker.roots()
    folder = Path('data/results/ethical_pilot') / worker.retention_id('base')
    bank_path = Path('data/generated/ethical_pilot') / worker.BANK / 'bank.jsonl'
    frozen = bank(set())
    for i, row in enumerate(frozen):
        row['expected_input_token_ids'] = [i + 1]
    jsonl(bank_path, frozen); jsonl(folder / 'bank.jsonl', frozen)
    runtime = {'model': {'pretrained': 'fixture'}, 'backend': {'backend': 'cuda'},
        'generation': {'revision': 'revision'}, 'decoding': {'temperature': .6},
        'max_new_tokens': 4096, 'batch_size': 32, 'versions': {'torch': 'fixture'}}
    meta_eval = {'model_label': 'base'}
    dump(folder / 'manifest.json', runtime | {'code_revision': 'abc', 'evaluation': meta_eval, 'adapter_sha256': None})
    dump(parent / 'base_retention_dispatch.json', {'source_commit': 'abcdef', 'config_sha': 'fixed', 'adapter_sha256': None})
    lookup = {}; observed = []
    for seed in (42, 7, 1729):
        for i, row in enumerate(frozen):
            response = '<think>\nCheck.\n</think>\n\n' + row['expected'] if row['thinking'] else row['expected']
            token = len(lookup) + 1; lookup[token] = response
            observed.append(row | {'eval_seed': seed, 'response': response, 'response_sha256': hashlib.sha256(response.encode()).hexdigest(),
                'assessment': assess(response, row, normal_stop=True), 'error': None,
                'generation_metadata': {'output_token_ids': [token, 999], 'input_token_ids': row['expected_input_token_ids'],
                    'finish_reason': 'stop', 'model_revision': 'revision', 'adapter_lora_id': None,
                    'sampling_seed': (row['seed'] ^ 42 ^ seed) & 0xffffffff,
                    'generation_tokens': 2, 'execution': runtime['generation'], 'execution_versions': runtime['versions']}})
    jsonl(folder / 'responses.jsonl', observed)
    known = report(observed[:128], frozen)[1]; jsonl(folder / 'known_items.jsonl', known)
    dump(folder / 'summary.json', {'by_seed': {str(seed): report([r for r in observed if r['eval_seed'] == seed], frozen, known)[0] for seed in (42, 7, 1729)}})
    (folder / 'COMPLETED').write_text('complete')
    monkeypatch.setattr(worker, 'load_job', lambda *a: SimpleNamespace(instruction_retention=SimpleNamespace(model_dump=lambda **kw: meta_eval)))
    monkeypatch.setattr(worker, 'config_sha', lambda j: 'fixed')
    tokenizer = SimpleNamespace(decode=lambda tokens, **kw: lookup[tokens[0]])
    return folder, {'bank_path': str(bank_path), 'bank_sha256': worker.sha(bank_path), 'runtime_reference': runtime, 'eos_token_id': 999}, tokenizer, observed


def test_full_raw_retention_grid_rebuilds_values_and_original_grade(tmp_path, monkeypatch):
    _, protocol, tokenizer, _ = grid(tmp_path, monkeypatch)
    values, _ = worker.inspect_retention('base', protocol, tokenizer)
    assert len(values) == 384 and all(r['value']['value_correct'] is True for r in values)


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'wrong_input', 'wrong_hash', 'wrong_value_grade'])
def test_grid_rejects_missing_identity_and_changed_original_grade(tmp_path, monkeypatch, fault):
    folder, protocol, tokenizer, observed = grid(tmp_path, monkeypatch)
    if fault == 'missing': observed.pop()
    elif fault == 'duplicate': observed.append(observed[0])
    elif fault == 'wrong_input': observed[0]['generation_metadata']['input_token_ids'] = [0]
    elif fault == 'wrong_hash': observed[0]['response_sha256'] = 'wrong'
    else: observed[0]['assessment']['semantic_correct'] = False
    jsonl(folder / 'responses.jsonl', observed)
    with pytest.raises(ValueError):
        worker.inspect_retention('base', protocol, tokenizer)


def full_surface_fixture(tmp_path, monkeypatch, dev_pass, val_pass, valid=2400):
    monkeypatch.chdir(tmp_path)
    _, parent = worker.roots(); parent.mkdir(parents=True)
    root = Path('data/results/ethical_pilot')
    dump(root / worker.eval_id('development') / 'stance_study_summary.json', {'selected': 'named_endorse_reject' if dev_pass else None})
    dump(root / worker.eval_id('validation') / 'stance_study_summary.json', {'validation_passed': val_pass})
    dump(parent / 'candidate_assessment.json', {'passed': True})
    monkeypatch.setattr(worker, 'check_bindings', lambda b: None)
    monkeypatch.setattr(worker, 'verify_binding', lambda b: None)
    monkeypatch.setattr(worker, 'load_job', lambda *a: None)
    monkeypatch.setattr(worker, 'config_sha', lambda j: 'fixed')
    monkeypatch.setattr(worker, 'original_surface_status', lambda f: {'recorded': 2400, 'valid': valid})
    protocol = {'source_bindings': {}, 'jobs': {worker.eval_id(p): 'fixed' for p in ('development', 'validation', 'reading', 'unqualified')}}
    return parent, protocol


@pytest.mark.parametrize('dev,val,phases', [(False,False,['development','unqualified']), (True,False,['development','validation','unqualified']), (True,True,['development','validation','reading'])])
def test_control_failures_still_collect_all_and_keep_actual_qualification(tmp_path, monkeypatch, dev, val, phases):
    parent, protocol = full_surface_fixture(tmp_path, monkeypatch, dev, val, valid=2399)
    calls = []
    monkeypatch.setattr(worker, 'execute', lambda cmd, p, phase: calls.append(phase) is None)
    worker.full_surface(protocol, {}, parent)
    assert calls == phases
    result = worker.read(parent / 'candidate_measurement_status.json')
    assert result['development_passed'] == dev and result['validation_passed'] == val
    assert result['actual_coverage']['valid'] == 2399  # No retry or score-gate filtering.


def test_technical_phase_failure_stops_instead_of_masking_as_unqualified(tmp_path, monkeypatch):
    parent, protocol = full_surface_fixture(tmp_path, monkeypatch, False, False)
    calls = []
    def fail(cmd, p, phase):
        calls.append(phase); return False
    monkeypatch.setattr(worker, 'execute', fail)
    with pytest.raises(RuntimeError, match='technical failure'):
        worker.full_surface(protocol, {}, parent)
    assert calls == ['development']


def test_reference_review_requires_every_queue_response_hash_and_private_receipt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, parent = worker.roots(); parent.mkdir(parents=True)
    observed = {'example_id': 'x', 'eval_seed': 42, 'response_sha256': 'response'}
    for model in ('base', 'norm1'):
        jsonl(parent / (model + '_review_queue.jsonl'), [{'observation': observed}])
    review = parent / 'reference_agent_review_v1.jsonl'
    jsonl(review, [observed | {'model': model, 'review_mode': 'agent_read_full_response'} for model in ('base', 'norm1')])
    summary = parent / 'reference_review_v1.json'
    dump(summary, {'full_response_review_complete': True, 'review_sha256': worker.sha(review),
        'queue_sha256': {model: worker.sha(parent / (model + '_review_queue.jsonl')) for model in ('base', 'norm1')}})
    saved = []; monkeypatch.setattr(worker, 'preserved', lambda p: saved.append(p))
    worker.reference_review_complete(parent)
    assert saved == [summary, review]
    jsonl(review, [observed | {'model': 'base', 'review_mode': 'agent_read_full_response'}])
    d = worker.read(summary); d['review_sha256'] = worker.sha(review); dump(summary, d)
    with pytest.raises(ValueError, match='coverage/hash mismatch'):
        worker.reference_review_complete(parent)


def worker_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('belief_transfer.inference.backend.require_training_backend', lambda: None)
    monkeypatch.setattr('transformers.AutoTokenizer.from_pretrained', lambda *a, **kw: None)
    monkeypatch.setattr(worker, 'check_bindings', lambda b: None)
    monkeypatch.setattr(worker, 'preserved', lambda p: None)
    monkeypatch.setattr(worker, 'commit', lambda: 'fixture')
    generated, parent = worker.roots()
    dump(generated / 'protocol.json', {'source_bindings': {}, 'control_binding': {},
        'runtime_reference': {'model': {'pretrained': 'fixture'}, 'generation': {'revision': 'r'}},
        'jobs': {worker.TRAIN: 'fixed'}})
    return parent


def test_finite_reference_dispatches_exact_two_models_then_refuses_repeat(tmp_path, monkeypatch):
    parent = worker_fixture(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(worker, 'collect_retention', lambda model, *a: calls.append(model))
    worker.run('reference')
    assert calls == ['base', 'norm1']
    assert (parent / 'REFERENCE_COMPLETED').exists() and (parent / 'REFERENCE_TERMINAL').exists()
    with pytest.raises(FileExistsError, match='already started'):
        worker.run('reference')
    assert calls == ['base', 'norm1']


def test_reference_failure_keeps_partial_stage_and_never_restarts(tmp_path, monkeypatch):
    parent = worker_fixture(tmp_path, monkeypatch)
    calls = []
    def collect(model, *a):
        calls.append(model); raise RuntimeError('transient child failure')
    monkeypatch.setattr(worker, 'collect_retention', collect)
    with pytest.raises(RuntimeError, match='transient'):
        worker.run('reference')
    assert (parent / 'reference_failure.json').exists() and (parent / 'REFERENCE_TERMINAL').exists()
    assert not (parent / 'REFERENCE_COMPLETED').exists()
    with pytest.raises(FileExistsError):
        worker.run('reference')
    assert calls == ['base']


def test_failed_training_is_preserved_and_candidate_cannot_restart(tmp_path, monkeypatch):
    parent = worker_fixture(tmp_path, monkeypatch); parent.mkdir(parents=True)
    for name in ('REFERENCE_COMPLETED', 'REFERENCE_TERMINAL'):
        (parent / name).write_text('complete')
    jsonl(parent / 'value_known_items.jsonl', [])
    jsonl(parent / 'base_values.jsonl', []); jsonl(parent / 'norm1_values.jsonl', [])
    dump(parent / 'value_reference_freeze.json', {'mask_sha256': worker.sha(parent / 'value_known_items.jsonl'), 'base_values_sha256': worker.sha(parent / 'base_values.jsonl')})
    monkeypatch.setattr(worker, 'reference_review_complete', lambda p: None)
    monkeypatch.setattr(worker, 'inspect_retention', lambda *a: ([], {}))
    monkeypatch.setattr(worker, 'load_job', lambda *a: None)
    monkeypatch.setattr(worker, 'config_sha', lambda j: 'fixed')
    monkeypatch.setattr(worker, 'verify_candidate', lambda *a: pytest.fail('Never verify a failed training'))
    calls = []
    def fail(cmd, p, label): calls.append(label); return False
    monkeypatch.setattr(worker, 'execute', fail)
    with pytest.raises(RuntimeError, match='training failed'):
        worker.run('candidate')
    assert calls == ['train/candidate']
    assert (parent / 'candidate_failure.json').exists() and (parent / 'CANDIDATE_TERMINAL').exists()
    assert not (parent / 'COLLECTION_COMPLETED').exists()
    with pytest.raises(FileExistsError, match='already started'):
        worker.run('candidate')
    assert calls == ['train/candidate']
