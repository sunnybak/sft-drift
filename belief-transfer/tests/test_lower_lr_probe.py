"""One-factor LR composition and prospective preparation guards, no weights/results."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_lower_lr_probe as probe
from belief_transfer.config import load_job


def candidate():
    old = load_job(['+run=' + probe.CONTROL])
    new = load_job(['+run=' + probe.CONTROL, 'run_id=' + probe.TRAIN,
        'training.sft.lr=0.000025',
        'document_sft.manifest_path=data/generated/ethical_stance_sft/' + probe.TRAIN + '/documents.jsonl'])
    return old, new


def test_only_learning_rate_changes_not_data_contract_or_schedule():
    old, new = candidate()
    probe.verify_single_training_change(old, new)
    overlay = probe.training_overlay()
    assert overlay['defaults'] == [probe.CONTROL]
    assert overlay['training'] == {'sft': {'lr': 2.5e-5}}
    assert old.document_sft.replay == new.document_sft.replay
    assert new.document_sft.replay.nonthinking_loss_weight == 1
    assert old.document_sft.max_steps == new.document_sft.max_steps == 454


@pytest.mark.parametrize('field,value', [('grad_accum', 1), ('seed', 7), ('lora_r', 8)])
def test_other_training_changes_rejected(field, value):
    old, new = candidate()
    bad = new.model_copy(update={'training': new.training.model_copy(update={
        'sft': new.training.sft.model_copy(update={field: value})})})
    with pytest.raises(ValueError, match='More than LR'):
        probe.verify_single_training_change(old, bad)


def test_schedule_and_preprocessing_changes_rejected():
    old, new = candidate()
    for update in ({'max_steps': 227}, {'synthetic_prefix': '<DOCTAG>'}):
        bad = new.model_copy(update={'document_sft': new.document_sft.model_copy(update=update)})
        with pytest.raises(ValueError):
            probe.verify_single_training_change(old, bad)


@pytest.mark.parametrize('phase', ['reading', 'unqualified'])
def test_full100_always_collects_and_original_default_unchanged(phase):
    overlay = probe.evaluation_overlay(phase)
    assert overlay['pilot_bench']['measurement_control_failure_policy'] == 'collect_unqualified'
    assert overlay['pilot_bench']['stance_validation_run_id'] == (probe.eval_id('validation') if phase == 'reading' else None)
    old = load_job(['+run=ethics_gpu_vllm_base_v1'])
    new = load_job(['+run=ethics_gpu_vllm_base_v1', 'run_id=' + probe.eval_id('reading'),
        '++pilot_bench.measurement_control_failure_policy=collect_unqualified'])
    a, b = old.pilot_bench.model_dump(), new.pilot_bench.model_dump()
    a.pop('measurement_control_failure_policy', None); b.pop('measurement_control_failure_policy', None)
    assert a == b and old.pilot_bench.measurement_control_failure_policy == 'skip'


def test_fresh_bank_is_fixed_and_collisions_fail_without_resampling():
    fresh = probe.confirmation_bank(set())
    assert len(fresh) == 128 and fresh == probe.confirmation_bank(set())
    assert len({r['prompt'] for r in fresh}) == 64
    assert all(r['example_id'].startswith('lower_lr_confirmation/') for r in fresh)
    with pytest.raises(ValueError, match='overlaps'):
        probe.confirmation_bank({fresh[0]['prompt']})


def test_preparation_refuses_live_parent_without_any_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='Finish original'):
        probe.prepare()
    assert not (tmp_path / 'data').exists()


def reviewed_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parent = tmp_path / 'data/results/ethical_stance_sft' / probe.PREVIOUS
    parent.mkdir(parents=True)
    for name in ('COLLECTION_COMPLETED', 'TERMINAL'):
        (parent / name).write_text('terminal')
    p = parent / 'reviewed_comparison_v1.json'
    p.write_text(json.dumps({'full_response_review_complete': True,
        'all100_recorded': {'norm1': 2400, 'weight32': 2400}}))
    return p


def test_review_and_coverage_required_before_next_preparation(tmp_path, monkeypatch):
    p = reviewed_parent(tmp_path, monkeypatch)
    p.write_text(json.dumps({'full_response_review_complete': False, 'all100_recorded': {}}))
    with pytest.raises(ValueError, match='paired review/coverage'):
        probe.prepare()
    assert not (tmp_path / 'data/generated').exists()


def test_registration_required_before_writes_and_started_ids_refused(tmp_path, monkeypatch):
    reviewed_parent(tmp_path, monkeypatch)
    c = tmp_path / 'configs/handoff.json'; c.parent.mkdir()
    c.write_text(json.dumps({'include_paths': []}))
    with pytest.raises(ValueError, match='Register every'):
        probe.prepare()
    assert not (tmp_path / 'data/generated').exists()
    assert len(probe.required_paths()) == len(set(probe.required_paths())) == 21
    c.write_text(json.dumps({'include_paths': probe.required_paths()}))
    (tmp_path / 'data' / probe.required_paths()[0]).mkdir(parents=True)
    with pytest.raises(FileExistsError, match='Fresh IDs'):
        probe.prepare()


def test_prior_review_must_be_privately_saved_before_preparing_inputs(tmp_path, monkeypatch):
    reviewed_parent(tmp_path, monkeypatch)
    c = tmp_path / 'configs/handoff.json'; c.parent.mkdir()
    c.write_text(json.dumps({'include_paths': probe.required_paths(), 'repo_id': 'private/test'}))
    receipt = tmp_path / 'data/.handoff-receipt.json'
    receipt.write_text(json.dumps({'repo_id': 'private/test', 'manifest': {'files': {}}}))
    with pytest.raises(ValueError, match='Privately preserve'):
        probe.prepare()
    assert not (tmp_path / 'data/generated').exists()
