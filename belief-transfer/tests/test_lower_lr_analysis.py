"""Factor attribution and missing-value handling, synthetic data/tempdirs only."""
from pathlib import Path
import copy
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import analyze_lower_lr_probe as analysis
from test_replay_weight_confirmation import values
from run_replay_weight_confirmation import value_known


def trace():
    return ([{'step': 1, 'learning_rate': 0.0}, {'step': 2, 'learning_rate': .0001}, {'train_loss': 1}],
            [{'step': 1, 'learning_rate': 0.0}, {'step': 2, 'learning_rate': .000025}, {'train_loss': .9}])


def test_actual_trace_requires_every_step_and_fourfold_reduction():
    before, after = trace()
    assert analysis.lr_trace_check(before, after, expected_steps=2)['passed']
    after[1]['learning_rate'] = .0001
    result = analysis.lr_trace_check(before, after, expected_steps=2)
    assert not result['passed'] and result['differences'][0]['step'] == 2
    assert not analysis.lr_trace_check(before, after[:1], expected_steps=2)['exact_step_grid']
    before[1]['learning_rate'] = -.0001; after[1]['learning_rate'] = -.000025
    assert not analysis.lr_trace_check(before, after, expected_steps=2)['passed']


def fixture():
    a, b = trace()
    common = {'initial_adapter_sha256': 'init', 'model_revision': 'qwen', 'global_steps': 2,
        'actual_forward_loss_tokens': 24, 'weighted_objective': {'raw': 24},
        'checks': {str(i): True for i in range(12)}}
    return common | {'log_history': a}, copy.deepcopy(common) | {'log_history': b}


def audit(a, b, old_batches=None, new_batches=None, **changes):
    settings = {'manifest_equal': True, 'tokenized_equal': True, 'scientific_config_equal': True, 'expected_steps': 2} | changes
    return analysis.factor_audit(a, b, [{'index': i} for i in range(4)] if old_batches is None else old_batches,
        [{'index': i} for i in range(4)] if new_batches is None else new_batches, **settings)


def test_comparability_does_not_assume_same_init_order_or_actual_targets():
    a, b = fixture(); assert audit(a, b)['passed']
    for field, value, key in [('initial_adapter_sha256', 'different', 'initial_adapter_identical'),
        ('actual_forward_loss_tokens', 25, 'raw_target_count_identical'),
        ('weighted_objective', {'raw': 25}, 'weighted_objective_identical'),
        ('global_steps', 1, 'actual_step_count_matches')]:
        changed = copy.deepcopy(b); changed[field] = value
        result = audit(a, changed)
        assert not result['passed'] and result['checks'][key] is False
    assert audit(a, b, new_batches=[{'index': 1}])['checks']['actual_forward_batches_identical'] is False
    assert not audit(a, b, old_batches=[], new_batches=[])['passed']
    assert not audit(a, b, scientific_config_equal=False)['passed']
    too_small = copy.deepcopy(a); too_small['log_history'][1]['learning_rate'] /= 10
    low = copy.deepcopy(b); low['log_history'][1]['learning_rate'] /= 10
    assert not audit(too_small, low)['checks']['actual_peak_LRs_match_plan']


def test_known_losses_gains_and_unknowns_remain_separate():
    control = values(); new = copy.deepcopy(control); known = value_known(control)
    group = [r for r in control if not r['thinking'] and r['eval_seed'] == 42]
    after = [r for r in new if not r['thinking'] and r['eval_seed'] == 42]
    group[0]['value']['value_correct'] = False
    after[1]['value']['value_correct'] = False
    after[2]['value']['value_correct'] = None
    summary, paired = analysis.paired_retention(control, new, known)
    result = summary['False/42/base_known']
    assert result['gains'] == [group[0]['example_id']]
    assert result['losses'] == [group[1]['example_id']]
    assert result['unscorable_transitions'] == [group[2]['example_id']]
    assert result['value_accuracy_delta_pp'] is None
    assert result['recognized_correct_delta_pp'] == -100 / 64
    assert result['unscorable'] == {'norm1': 0, 'candidate': 1} and len(paired) == 384


def test_pairing_rejects_changed_or_duplicated_bank_and_foreign_mask():
    control = values(); new = copy.deepcopy(control); known = value_known(control)
    for invalid in (new[:-1], new + [new[0]]):
        with pytest.raises(ValueError): analysis.paired_retention(control, invalid, known)
    new[0]['thinking'] = False
    with pytest.raises(ValueError, match='family/mode'):
        analysis.paired_retention(control, new, known)
    with pytest.raises(ValueError, match='Foreign'):
        analysis.paired_retention(control, control, [known[0] | {'example_id': 'foreign'}])


def test_final_analysis_refuses_live_or_partial_candidate_before_any_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='must finish'):
        analysis.main()
    assert not (tmp_path / 'data').exists()
