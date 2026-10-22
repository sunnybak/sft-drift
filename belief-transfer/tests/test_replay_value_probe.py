"""Versioned assessment and finite candidate behavior, using temporary data only."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_replay_value_probe as prepare
import review_replay_coverage_references as review
import run_replay_value_probe as worker
import run_replay_coverage_probe as previous
from prepare_replay_weight_ablation import write_rows, read
from prepare_replay_coverage_probe import decision_bank
from build_replay_coverage import candidates
from belief_transfer.evals.neutral_decision_retention import assess


def native_rows():
    return [r | {'response': r['expected'], 'response_sha256': 'a' * 64,
        'assessment': assess(r['expected'], r, normal_stop=True)}
        for r in decision_bank(candidates())]


def test_same_recipe_rejects_lr_or_dose_change():
    def job(value):
        return SimpleNamespace(model_dump=lambda **_: copy.deepcopy(value))
    old = {'run_id': 'old', 'training': {'lr': .0001}, 'document_sft': {
        'manifest_path': 'old', 'plan_path': 'old', 'plan_sha256': 'a', 'max_steps': 454}}
    new = copy.deepcopy(old)
    new['run_id'] = 'new'
    new['document_sft'].update(manifest_path='new', plan_path='new', plan_sha256='b')
    assert prepare.same_recipe(job(old), job(new))
    new['training']['lr'] /= 4
    assert not prepare.same_recipe(job(old), job(new))
    new = copy.deepcopy(old)
    new['document_sft']['max_steps'] = 100
    assert not prepare.same_recipe(job(old), job(new))


def test_manual_choice_is_not_selected_from_expected_answer():
    observation = {'example_id': 'coverage_decision/04', 'thinking': False, 'expected': 'endorse'}
    first = review.manual_decision('base', observation)
    observation['expected'] = 'reject'
    assert review.manual_decision('base', observation) == first
    assert first[0] == 'reject'


def test_supplement_does_not_mutate_native_rows_or_use_reasoning_to_rescue_wrong_choice():
    original = native_rows()
    original[0]['thinking'] = True
    original[0]['response'] = '<think>\nThe right choice is ' + original[0]['expected'] + '.\n</think>\n\n' + (
        'Reject.' if original[0]['expected'] == 'endorse' else 'Endorse.')
    before = copy.deepcopy(original)
    derived = worker.supplement(original)
    assert original == before
    assert derived[0]['assessment']['value_correct'] is False
    assert derived[0]['assessment']['native_v1_assessment']['value_correct'] is None


@pytest.mark.parametrize('existing', ['parent', 'checkpoint', 'runtime_config'])
def test_started_outputs_refuse_overwrite(tmp_path, monkeypatch, existing):
    monkeypatch.chdir(tmp_path)
    parent = Path('data/results/ethical_stance_sft') / prepare.MASTER
    target = {'parent': parent, 'checkpoint': Path('data/checkpoints/ethical_stance_sft') / prepare.TRAIN,
        'runtime_config': Path('configs/run', prepare.candidate_id('decisions') + '.yaml')}[existing]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('preserved')
    with pytest.raises(FileExistsError):
        worker.preflight_outputs(parent)
    assert target.read_text() == 'preserved'


def test_collect_keeps_scientific_failure_and_native_scores_without_raising(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('configs/run').mkdir(parents=True)
    parent, ref = tmp_path / 'candidate', tmp_path / 'reference'
    parent.mkdir(); ref.mkdir()
    base = native_rows()
    for name in ('base_decisions_values.jsonl', 'base_decisions_value_v2.jsonl'):
        write_rows(ref / name, worker.supplement(base) if 'value_v2' in name else base)
    known = previous.decision_known(base)
    write_rows(ref / 'decisions_known_items.jsonl', known)
    write_rows(ref / 'decisions_value_known_items_v2.jsonl', known)
    changed = copy.deepcopy(base)
    for r in changed[:4]:
        r['response'] = 'reject' if r['expected'] == 'endorse' else 'endorse'
        r['assessment'] = assess(r['response'], r, normal_stop=True)
    child = Path('data/results/ethical_pilot') / prepare.candidate_id('decisions')
    monkeypatch.setattr(worker, 'reference_root', lambda: ref)
    monkeypatch.setattr(worker, 'check_bindings', lambda _: None)
    monkeypatch.setattr(worker, 'verify_binding', lambda _: None)
    monkeypatch.setattr(previous, 'runtime_config', lambda *a: {'stage': 'neutral_decision_retention'})
    monkeypatch.setattr(worker, 'load_job', lambda _: SimpleNamespace(neutral_decision_retention=SimpleNamespace(adapter_sha256='b')))
    monkeypatch.setattr(worker, 'config_sha', lambda _: 'c')
    monkeypatch.setattr(previous, 'commit', lambda: 'd')
    def execute(*a):
        child.mkdir(parents=True)
        write_rows(child / 'responses.jsonl', changed)
        return True
    monkeypatch.setattr(previous, 'execute', execute)
    monkeypatch.setattr(previous, 'inspect', lambda *a, **kw: changed)
    worker.collect('decisions', {'source_bindings': {}}, None, {}, parent)
    assert read(parent / 'candidate_decisions_assessment.json')['passed'] is False
    assert (parent / 'candidate_decisions_native_v1_assessment.json').is_file()
    assert (parent / 'candidate_decisions_review_queue.md').is_file()
    with pytest.raises(FileExistsError):
        worker.collect('decisions', {'source_bindings': {}}, None, {}, parent)


def test_output_registry_has_candidate_and_all100_phases():
    paths = prepare.required_paths()
    assert len(paths) == len(set(paths)) == 17
    assert all(n.startswith('ethics_gpu_') for n in [prepare.candidate_id('decisions'), prepare.eval_id('unqualified')])
    assert f'results/ethical_pilot/{prepare.eval_id("unqualified")}' in paths
