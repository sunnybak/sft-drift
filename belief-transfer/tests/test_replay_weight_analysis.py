"""Paired value contrasts and collection-gate diagnosis, no live result directories."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import analyze_replay_weight_ablation as analysis
from test_replay_weight_confirmation import values
from run_replay_weight_confirmation import value_known


def test_paired_comparison_counts_gains_losses_and_leaves_unknown_unscored():
    control = values(); weighted = copy.deepcopy(control); known = value_known(control)
    # One gain, one loss and one unscorable at the same mode/seed.
    group = [r for r in control if not r['thinking'] and r['eval_seed'] == 42]
    group[0]['value']['value_correct'] = False
    target = [r for r in weighted if not r['thinking'] and r['eval_seed'] == 42]
    target[1]['value']['value_correct'] = False
    target[2]['value']['value_correct'] = None
    result, pairs = analysis.paired_values(control, weighted, known)
    cell = result['False/42/base_known']
    assert cell['norm1_correct'] == 63 and cell['weight32_correct'] == 62
    assert cell['unscorable'] == {'norm1': 0, 'weight32': 1}
    assert cell['paired_scorable'] == 63 and cell['value_accuracy_difference_pp'] is None
    assert cell['recognized_correct_difference_pp'] == -100 / 64
    assert cell['gains'] == [group[0]['example_id']] and cell['losses'] == [group[1]['example_id']]
    assert len(pairs) == 384
    unknown = next(r for r in pairs if r['example_id'] == group[2]['example_id'] and r['eval_seed'] == 42)
    assert unknown['weight32_correct'] is None and not unknown['value_loss']


def test_matched_grid_rejects_duplicates_changed_mode_and_foreign_cohort():
    control = values(); weighted = copy.deepcopy(control); known = value_known(control)
    for invalid in [weighted[:-1], weighted + [weighted[0]]]:
        with pytest.raises(ValueError):
            analysis.paired_values(control, invalid, known)
    weighted[0]['thinking'] = not weighted[0]['thinking']
    with pytest.raises(ValueError, match='family/mode'):
        analysis.paired_values(control, weighted, known)
    with pytest.raises(ValueError, match='outside'):
        analysis.paired_values(control, control, [known[0] | {'example_id': 'foreign'}])


@pytest.mark.parametrize('recorded,valid,code', [
    (0, 0, 'CONTROL_GATE_SKIPPED_NATURAL'), (100, 100, 'MISSING_NATURAL_RESPONSES'),
    (2400, 2399, 'INVALID_NATURAL_RESPONSES'), (2400, 2400, None),
])
def test_complete_marker_cannot_substitute_for_actual_full100_coverage(tmp_path, monkeypatch, recorded, valid, code):
    bank = [{'belief_id': str(i)} for i in range(100) for _ in range(24)]
    rebuilt = {str(i): {'neutral': {'diagnostics': {'n_extracted': min(24, max(0, valid - i * 24))}}} for i in range(100)}
    summary = {'measurements': {'stance': rebuilt}, 'meta_eval': {
        'model_controls': {'failed': True}, 'stance_operational_qualification': {'passed': False}}}
    (tmp_path / 'measurement_summary.json').write_text(json.dumps(summary))
    (tmp_path / 'stance_bank.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in bank))
    (tmp_path / 'stance_observations.jsonl').write_text('{}\n' * recorded)
    (tmp_path / 'COLLECTION_COMPLETED').write_text('not sufficient evidence')
    monkeypatch.setattr(analysis, 'summarize_measurement', lambda b, r: rebuilt)
    result = analysis.original_surface_status(tmp_path)
    assert result['expected'] == 2400 and result['recorded'] == recorded and result['valid'] == valid
    assert result['code'] == code and result['complete'] == (valid == 2400)


def test_completion_repairs_absent_calls_not_invalid_answers_or_failed_controls():
    statuses = {arm: {'expected': 2400, 'recorded': 2400, 'valid': 0, 'complete': False} for arm in ('norm1', 'weight32')}
    assert not analysis.needs_completion_followup(statuses)
    statuses['norm1']['recorded'] = 0
    assert analysis.needs_completion_followup(statuses)
    with pytest.raises(ValueError, match='Both'):
        analysis.needs_completion_followup({'norm1': statuses['norm1']})
