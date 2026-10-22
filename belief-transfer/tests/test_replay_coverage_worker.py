"""Finite worker/qualification tests with synthetic rows and temporary directories."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_replay_coverage_probe as worker
from build_replay_coverage import candidates
from prepare_replay_coverage_probe import decision_bank
from belief_transfer.evals.neutral_decision_retention import assess


def values():
    rows = []
    for mode in (True, False):
        for family in worker.FAMILIES:
            for i in range(8):
                rows.append({'example_id': f'{family}/{i}/{mode}', 'family': family,
                    'thinking': mode, 'eval_seed': 42, 'response_sha256': 'a'*64,
                    'frozen_assessment': {'strict_format': True, 'normal_stop': True, 'response_boundaries_valid': True},
                    'value': {'value_correct': True}})
    return rows


@pytest.mark.parametrize('losses,passed', [(3, True), (4, False)])
def test_value_gate_exact_threshold_and_unscorable_not_neutral(losses, passed):
    base = values()
    known = worker.value_known(base)
    changed = copy.deepcopy(base)
    for row in changed[:losses]:
        row['value']['value_correct'] = None
    result = worker.summarize_values(changed, base, known)
    assert result['passed'] is passed
    assert result['by_mode']['True']['full_unscorable'] == losses


def test_format_and_stop_regressions_stay_independent():
    base = values()
    changed = copy.deepcopy(base)
    for row in changed[:4]:
        row['frozen_assessment']['strict_format'] = False
    assert not worker.summarize_values(changed, base, worker.value_known(base))['passed']
    changed = copy.deepcopy(base)
    changed[-1]['frozen_assessment']['normal_stop'] = False
    assert not worker.summarize_values(changed, base, worker.value_known(base))['passed']


def decisions():
    result = []
    for r in decision_bank(candidates()):
        text = '<think>\nProof.\n</think>\n\n' + r['expected'] if r['thinking'] else r['expected']
        result.append(r | {'response_sha256': 'a'*64, 'assessment': assess(text, r, normal_stop=True)})
    return result


@pytest.mark.parametrize('losses,passed', [(1, True), (2, False)])
def test_decision_retention_uses_fixed_base_cohort(losses, passed):
    base = decisions()
    changed = copy.deepcopy(base)
    chosen = [r for r in changed if r['thinking']][:losses]
    for r in chosen:
        r['assessment']['value_correct'] = False
    result = worker.compare_decisions(changed, base, worker.decision_known(base))
    assert result['reference_usable']
    assert result['passed'] is passed


def test_insufficient_base_operation_coverage_is_inconclusive():
    base = decisions()
    known = [r for r in worker.decision_known(base) if r['operation'] != 'product']
    result = worker.compare_decisions(base, base, known)
    assert not result['reference_usable'] and not result['passed']
    assert result['by_mode']['True']['known_n'] == 24


def setup_worker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generated, parent = worker.roots()
    generated.mkdir(parents=True)
    protocol = {'source_bindings': {}, 'runtime_reference': {'model': {'pretrained': 'mock'},
        'generation': {'revision': 'a'*40}}, 'control_binding': {},
        'jobs': {worker.TRAIN: 'frozen', worker.retention_id('base'): 'frozen',
                 worker.decision_id('base'): 'frozen', worker.decision_id('control'): 'frozen'}}
    (generated / 'protocol.json').write_text(json.dumps(protocol))
    monkeypatch.setattr(worker, 'check_bindings', lambda _: None)
    monkeypatch.setattr(worker, 'preserved', lambda _: None)
    monkeypatch.setattr(worker, 'commit', lambda: 'testcommit')
    import belief_transfer.inference.backend as backend
    monkeypatch.setattr(backend, 'require_training_backend', lambda: None)
    import transformers
    monkeypatch.setattr(transformers.AutoTokenizer, 'from_pretrained', lambda *args, **kwargs: None)
    return parent, protocol


@pytest.mark.parametrize('failure', [False, True])
def test_reference_worker_finite_partial_failure_and_no_resume(tmp_path, monkeypatch, failure):
    parent, _ = setup_worker(tmp_path, monkeypatch)
    calls = []
    def collect(model, kind, *args):
        calls.append((model, kind))
        if failure and len(calls) == 2:
            raise RuntimeError('technical failure')
    monkeypatch.setattr(worker, 'collect', collect)
    if failure:
        with pytest.raises(RuntimeError, match='technical'):
            worker.run('reference')
        assert (parent / 'reference_failure.json').is_file()
        assert not (parent / 'REFERENCE_COMPLETED').exists()
    else:
        worker.run('reference')
        assert calls == [('base', 'retention'), ('base', 'decisions'), ('control', 'retention'), ('control', 'decisions')]
        assert (parent / 'REFERENCE_COMPLETED').is_file()
    assert (parent / 'REFERENCE_TERMINAL').is_file()
    with pytest.raises(FileExistsError):
        worker.run('reference')


def test_candidate_refuses_without_reference_before_training(tmp_path, monkeypatch):
    parent, _ = setup_worker(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='Complete references'):
        worker.run('candidate')
    assert not parent.exists()


@pytest.mark.parametrize('failure', [False, True])
def test_candidate_is_one_train_then_both_checks_and_full_surface(tmp_path, monkeypatch, failure):
    parent, _ = setup_worker(tmp_path, monkeypatch)
    parent.mkdir(parents=True)
    for name in ('REFERENCE_COMPLETED', 'REFERENCE_TERMINAL'):
        (parent / name).write_text('complete')
    for kind in ('retention', 'decisions'):
        (parent / f'{kind}_known_items.jsonl').write_text('')
        for model in ('base', 'control'):
            (parent / f'{model}_{kind}_values.jsonl').write_text('')
    monkeypatch.setattr(worker, 'review_complete', lambda _: None)
    monkeypatch.setattr(worker, 'inspect', lambda *args: [])
    monkeypatch.setattr(worker, 'value_known', lambda _: [])
    monkeypatch.setattr(worker, 'decision_known', lambda _: [])
    monkeypatch.setattr(worker, 'load_job', lambda _: None)
    monkeypatch.setattr(worker, 'config_sha', lambda _: 'frozen')
    calls = []
    def execute(*args):
        calls.append('train')
        return not failure
    monkeypatch.setattr(worker, 'execute', execute)
    monkeypatch.setattr(worker, 'verify_candidate', lambda *args: {})
    monkeypatch.setattr(worker, 'collect', lambda model, kind, *args: calls.append(kind))
    monkeypatch.setattr(worker, 'full_surface', lambda *args: calls.append('full100'))
    if failure:
        with pytest.raises(RuntimeError, match='training technical'):
            worker.run('candidate')
        assert calls == ['train']
        assert (parent / 'candidate_failure.json').is_file()
        assert not (parent / 'COLLECTION_COMPLETED').exists()
    else:
        worker.run('candidate')
        assert calls == ['train', 'retention', 'decisions', 'full100']
        assert (parent / 'COLLECTION_COMPLETED').is_file()
    assert (parent / 'CANDIDATE_TERMINAL').is_file()
    with pytest.raises(FileExistsError):
        worker.run('candidate')


@pytest.mark.parametrize('defect', ['missing_review', 'wrong_hash', 'private_save'])
def test_review_gate_requires_actual_coverage_hash_and_private_save(tmp_path, monkeypatch, defect):
    monkeypatch.chdir(tmp_path)
    parent = Path('master')
    parent.mkdir()
    queued = {'model': 'base', 'kind': 'retention',
              'observation': {'example_id': 'r', 'response_sha256': 'a'*64}}
    queue_hashes = {}
    for model in ('base', 'control'):
        for kind in ('retention', 'decisions'):
            p = parent / f'{model}_{kind}_review_queue.jsonl'
            p.write_text(json.dumps(queued)+'\n' if (model, kind) == ('base', 'retention') else '')
            queue_hashes[str(p)] = worker.sha(p)
    review = {'model': 'base', 'kind': 'retention', 'example_id': 'r',
              'response_sha256': 'b'*64 if defect == 'wrong_hash' else 'a'*64,
              'review_mode': 'agent_read_full_response'}
    rp = parent / 'reference_agent_review_v1.jsonl'
    rp.write_text('' if defect == 'missing_review' else json.dumps(review)+'\n')
    (parent / 'reference_review_v1.json').write_text(json.dumps({'full_response_review_complete': True,
        'review_sha256': worker.sha(rp), 'queue_sha256': queue_hashes}))
    for kind in ('retention', 'decisions'):
        mask, values = parent / f'{kind}_known_items.jsonl', parent / f'base_{kind}_values.jsonl'
        mask.write_text('');values.write_text('')
        (parent / f'{kind}_reference_freeze.json').write_text(json.dumps({'mask_sha256': worker.sha(mask), 'base_values_sha256': worker.sha(values)}))
    (parent / 'base_decisions_assessment.json').write_text('{"reference_usable": true}')
    def unpreserved(_):
        raise ValueError('Private save missing')
    monkeypatch.setattr(worker, 'preserved', unpreserved)
    with pytest.raises(ValueError, match='Private save' if defect == 'private_save' else 'coverage'):
        worker.review_complete(parent)


@pytest.mark.parametrize('development,validation,chosen', [(False, False, 'unqualified'),
    (True, False, 'unqualified'), (True, True, 'reading')])
def test_all100_collection_after_either_qualification_route(tmp_path, monkeypatch, development, validation, chosen):
    monkeypatch.chdir(tmp_path)
    parent = tmp_path / 'master'
    parent.mkdir()
    calls = []
    monkeypatch.setattr(worker, 'check_bindings', lambda _: None)
    monkeypatch.setattr(worker, 'verify_binding', lambda _: None)
    monkeypatch.setattr(worker, 'load_job', lambda _: None)
    monkeypatch.setattr(worker, 'config_sha', lambda _: 'frozen')
    monkeypatch.setattr(worker, 'original_surface_status', lambda _: {'recorded': 2400, 'valid': 2399})
    def execute(command, out, phase):
        calls.append(phase)
        folder = Path('data/results/ethical_pilot') / worker.eval_id(phase)
        folder.mkdir(parents=True)
        summary = {'selected': 'named_endorse_reject' if development else None} if phase == 'development' else {'validation_passed': validation}
        (folder / 'stance_study_summary.json').write_text(json.dumps(summary))
        return True
    monkeypatch.setattr(worker, 'execute', execute)
    protocol = {'source_bindings': {}, 'jobs': {worker.eval_id(p): 'frozen' for p in ('development', 'validation', 'reading', 'unqualified')}}
    worker.full_surface(protocol, {}, parent)
    assert calls[-1] == chosen
    assert ('validation' in calls) is development
    assert json.loads((parent / 'candidate_measurement_status.json').read_text())['actual_coverage']['valid'] == 2399
