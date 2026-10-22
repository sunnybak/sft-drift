"""Value reference/retention gates use synthetic responses, no CUDA or real data."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_replay_weight_confirmation import value_known, summarize
from prepare_replay_weight_ablation import confirmation_bank


def values():
    return [{k: row[k] for k in ('example_id', 'family', 'thinking')} | {
        'eval_seed': seed, 'response_sha256': 'a' * 64,
        'value': {'value_correct': True},
        'frozen_assessment': {'strict_format': True, 'normal_stop': True, 'response_boundaries_valid': True}}
        for row in confirmation_bank(set()) for seed in (42, 7, 1729)]


def test_value_cohort_ignores_format_and_selects_only_seed42():
    reference = values()
    first = reference[0]
    first['frozen_assessment']['strict_format'] = False
    reference[3]['value']['value_correct'] = False  # A different mode's seed42.
    reference[1]['value']['value_correct'] = False  # Seed7 cannot exclude seed42-known.
    mask = value_known(reference)
    assert first['example_id'] in {r['example_id'] for r in mask}
    assert reference[3]['example_id'] not in {r['example_id'] for r in mask}
    assert len(mask) == 127
    wrong = [dict(r, value={'value_correct': None}) for r in reference]
    with pytest.raises(ValueError, match='insufficient'):
        value_known(wrong)


def test_retention_gate_keeps_unscorable_separate_and_checks_each_seed():
    reference = values(); mask = value_known(reference)
    result = summarize(reference, reference, mask)
    assert result['passed']
    candidate = copy.deepcopy(reference)
    group = [r for r in candidate if not r['thinking'] and r['eval_seed'] == 7]
    for row in group[:3]:
        row['value']['value_correct'] = False
    assert summarize(candidate, reference, mask)['passed']  # 61/64 >= .95
    group[3]['value']['value_correct'] = None
    result = summarize(candidate, reference, mask)
    assert not result['passed']
    failed = result['by_mode_seed']['False/7']
    assert failed['full'] == {'correct': 60, 'wrong': 3, 'unscorable': 1}
    assert failed['known_unscorable'] == 1
    assert result['by_mode_seed']['False/42']['passed']


def test_format_deficit_and_incomplete_stop_fail_independently():
    reference = values(); mask = value_known(reference)
    candidate = copy.deepcopy(reference)
    group = [r for r in candidate if r['thinking'] and r['eval_seed'] == 42]
    for row in group[:4]:
        row['frozen_assessment']['strict_format'] = False
    result = summarize(candidate, reference, mask)
    assert not result['passed'] and result['by_mode_seed']['True/42']['known_correct'] == 64
    assert result['by_mode_seed']['True/42']['strict_format_delta_pp'] == -6.25
    candidate = copy.deepcopy(reference)
    candidate[0]['frozen_assessment']['normal_stop'] = False
    assert not summarize(candidate, reference, mask)['passed']


def test_comparison_requires_exact_unique_coverage():
    reference = values(); mask = value_known(reference)
    for candidate in [reference[:-1], reference + [reference[0]]]:
        with pytest.raises(ValueError, match='coverage'):
            summarize(candidate, reference, mask)
