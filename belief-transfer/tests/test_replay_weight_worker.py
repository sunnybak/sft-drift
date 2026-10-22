"""Finite worker routing: final-only, failures preserved, all100still collected."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_replay_weight_ablation as worker


@pytest.mark.parametrize('qualified', [True, False])
def test_qualification_failure_routes_to_explicit_all100_and_retention_is_separate(tmp_path, monkeypatch, qualified):
    monkeypatch.chdir(tmp_path)
    output = tmp_path / 'controller'; output.mkdir()
    reference = tmp_path / 'data/results/ethical_pilot' / worker.CONFIRMATION
    reference.mkdir(parents=True)
    (reference / 'norm1_assessment.json').write_text(json.dumps({'passed': False}))
    calls = []
    def execute(command, out, label):
        calls.append(label)
        if label.startswith('development'):
            target = tmp_path / 'data/results/ethical_pilot' / worker.eval_id('norm1', 'development')
            target.mkdir(parents=True)
            (target / 'stance_study_summary.json').write_text(json.dumps({'selected': 'named_endorse_reject' if qualified else None}))
            return qualified
        if label.startswith('validation'):
            target = tmp_path / 'data/results/ethical_pilot' / worker.eval_id('norm1', 'validation')
            target.mkdir(parents=True)
            (target / 'stance_study_summary.json').write_text(json.dumps({'validation_passed': qualified}))
        return True
    monkeypatch.setattr(worker, 'execute', execute)
    monkeypatch.setattr(worker, 'verify_binding', lambda b: None)
    worker.full_surface('norm1', {}, output)
    phase = 'stance' if qualified else 'unqualified'
    assert calls[-1] == phase + '/norm1'
    assert ('validation/norm1' in calls) == qualified
    status = json.loads((output / 'norm1_measurement_status.json').read_text())
    assert status['value_retention_passed'] is False
    assert status['validation_passed'] == qualified
    if not qualified:
        assert (tmp_path / 'data/results/ethical_pilot' / worker.eval_id('norm1', phase) / 'UNQUALIFIED.md').exists()


def test_failed_all100_collection_raises_without_success_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output = tmp_path / 'controller'; output.mkdir()
    monkeypatch.setattr(worker, 'execute', lambda *a: False)
    monkeypatch.setattr(worker, 'verify_binding', lambda b: None)
    with pytest.raises(RuntimeError, match='Full100 collection failed'):
        worker.full_surface('norm1', {}, output)
    assert not (output / 'norm1_measurement_status.json').exists()


def test_training_verification_rejects_objective_mismatch(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(worker, 'training_binding', lambda *a: {'checked': True})
    def read(path):
        if path.name == 'plan.json':
            return {'weighted_objective_projection': {'weighted_forward_targets': 100}}
        return {'training': {'weighted_objective': {'weighted_forward_targets': 99}}}
    monkeypatch.setattr(worker, 'read', read)
    with pytest.raises(ValueError, match='frozen projection'):
        worker.verify_training('norm1')
