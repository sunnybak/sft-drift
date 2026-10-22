"""Coverage repair is conditional, symmetric and never changes the instrument."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import complete_replay_weight_surface as completion
from belief_transfer.config import config_sha, load_job


@pytest.mark.parametrize('phase', ['stance', 'unqualified'])
def test_collect_all_composition_changes_only_run_id_and_collection_guard(phase):
    source = f'ethics_gpu_replay_weight_norm1_{phase}_s42_v1'
    old = load_job(['+run=' + source])
    new = load_job(['+run=' + source, 'run_id=' + completion.child_id('norm1'),
                   '++pilot_bench.measurement_control_failure_policy=collect_unqualified'])
    before = old.pilot_bench.model_dump(); after = new.pilot_bench.model_dump()
    before.pop('measurement_control_failure_policy', None); after.pop('measurement_control_failure_policy', None)
    assert before == after and old.pilot_bench.measurement_control_failure_policy == 'skip'
    assert new.pilot_bench.measurement_control_failure_policy == 'collect_unqualified'
    assert new.pilot_bench.stance_validation_run_id == old.pilot_bench.stance_validation_run_id
    assert config_sha(old) != config_sha(new)
    assert completion.overlay('norm1', source)['defaults'] == [source]


def test_prepare_rejects_live_or_partial_parent_before_any_new_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='must finish'):
        completion.prepare()
    assert not (tmp_path / 'data').exists()


def fake_parent(tmp_path, monkeypatch, recorded):
    monkeypatch.chdir(tmp_path)
    parent = tmp_path / 'data/results/ethical_stance_sft' / completion.MASTER
    parent.mkdir(parents=True)
    amendment = tmp_path / 'amendment.md'; amendment.write_text('fixed rule')
    monkeypatch.setattr(completion, 'AMENDMENT', amendment)
    monkeypatch.setattr(completion, 'original_statuses', lambda p: {
        a: {'stance_run_id': a} for a in completion.ARMS})
    monkeypatch.setattr(completion, 'original_surface_status', lambda p: {
        'expected': 2400, 'recorded': recorded, 'valid': 0, 'complete': False})
    monkeypatch.setattr(completion, 'verify_training', lambda a: pytest.fail('No training/weights needed on this path'))
    return parent


def test_invalid_complete_grids_freeze_no_followup_even_without_new_registration(tmp_path, monkeypatch):
    parent = fake_parent(tmp_path, monkeypatch, 2400)
    result = completion.prepare()
    assert result['completion_needed'] is False
    assert (parent / 'completion_decision_v1.json').exists()
    assert not (tmp_path / 'data/generated').exists()
    with pytest.raises(FileExistsError, match='already frozen'):
        completion.prepare()


def test_missing_calls_require_registration_before_preparation_or_any_write(tmp_path, monkeypatch):
    parent = fake_parent(tmp_path, monkeypatch, 0)
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'configs/handoff.json').write_text(json.dumps({'include_paths': []}))
    with pytest.raises(ValueError, match='Register fresh'):
        completion.prepare()
    assert not (parent / 'completion_decision_v1.json').exists()
    assert not (tmp_path / 'data/generated').exists()
    assert len(completion.required_paths()) == len(set(completion.required_paths())) == 6


def execution_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('belief_transfer.inference.backend.require_training_backend', lambda: None)
    generated = tmp_path / 'data/generated/ethical_pilot' / completion.RUN
    generated.mkdir(parents=True)
    protocol = {'source_bindings': {}, 'adapters': {a: {} for a in completion.ARMS},
                'jobs': {a: {'config_sha': 'fixed'} for a in completion.ARMS}}
    path = generated / 'protocol.json'; path.write_text(json.dumps(protocol))
    (tmp_path / 'data/.handoff-receipt.json').write_text(json.dumps({'manifest': {'files': {
        str(path.relative_to(tmp_path / 'data')): {'sha256': completion.sha(path)}}}}))
    monkeypatch.setattr(completion, 'original_statuses', lambda p: {})
    monkeypatch.setattr(completion, 'verify_binding', lambda b: None)
    monkeypatch.setattr(completion, 'load_job', lambda *a: None)
    monkeypatch.setattr(completion, 'config_sha', lambda j: 'fixed')
    monkeypatch.setattr(completion.subprocess, 'check_output', lambda *a, **kw: 'fixture-commit\n')
    return tmp_path / 'data/results/ethical_pilot' / completion.RUN


def test_worker_records_both_grids_once_even_when_all_answers_invalid(tmp_path, monkeypatch):
    out = execution_fixture(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(completion, 'execute', lambda cmd, root, arm: calls.append(arm) is None)
    monkeypatch.setattr(completion, 'original_surface_status', lambda p: {
        'expected': 2400, 'recorded': 2400, 'valid': 0, 'complete': False})
    completion.run()
    assert calls == ['norm1', 'weight32']
    result = json.loads((out / 'coverage.json').read_text())
    assert result['all_expected_calls_recorded'] is True and result['all_answers_valid'] is False
    assert (out / 'COMPLETED').exists() and (out / 'TERMINAL').exists()
    with pytest.raises(FileExistsError, match='already started'):
        completion.run()
    assert calls == ['norm1', 'weight32']


def test_worker_preserves_technical_failure_without_restarting_or_second_attempt(tmp_path, monkeypatch):
    out = execution_fixture(tmp_path, monkeypatch)
    calls = []
    def fail(cmd, root, arm):
        calls.append(arm)
        return False
    monkeypatch.setattr(completion, 'execute', fail)
    with pytest.raises(RuntimeError, match='no automatic rerun'):
        completion.run()
    assert calls == ['norm1']
    assert (out / 'failure.json').exists() and (out / 'TERMINAL').exists()
    assert not (out / 'COMPLETED').exists()
