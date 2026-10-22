"""Coverage and polarity bounds are distinct from point scores, no real artifacts."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from report_replay_weight_surface import profile


def grid():
    bank = [{'presentation_id': f'b/{i}', 'belief_id': 'b', 'role': 'ethical',
        'polarity': 'positive' if i < 12 else 'negative'} for i in range(24)]
    return bank, [r | {'answer': 'agree'} for r in bank]


def test_complete_profile_reverses_negation():
    bank, observed = grid()
    value = profile(bank, observed)['b']
    assert value['support'] == .5 and value['support_bounds'] == [.5, .5]
    assert value['valid'] == value['expected'] == 24


def test_incomplete_profile_has_bounds_and_no_point_or_neutral_imputation():
    bank, observed = grid(); observed[12]['answer'] = None
    value = profile(bank, observed)['b']
    assert value['support'] is None and value['valid'] == 23
    assert value['canonical_support_count'] == 12
    assert value['support_bounds'] == [.5, 13 / 24]


def test_missing_duplicate_or_changed_role_grid_rejected():
    bank, observed = grid()
    for invalid in (observed[:-1], observed + [observed[0]]):
        with pytest.raises(ValueError, match='recorded exactly once'):
            profile(bank, invalid)
    bank[0]['role'] = 'offtopic'
    with pytest.raises(ValueError, match='grid or role'):
        profile(bank, observed)
