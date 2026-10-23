"""Review selection coverage; all inputs synthetic and no model calls."""
import copy
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from analyze_hf_reference import select_review, stance_contrast


def reply(i, seed=42):
    return {'example_id': f'case/{i}', 'eval_seed': seed,
        'value': {'value_correct': True},
        'assessment': {'strict_format': True, 'normal_stop': True, 'response_boundaries_valid': True}}


def test_selection_keeps_every_changed_or_defective_reply_and_eight_fixed_pairs():
    before = [reply(i, seed) for seed in (42, 7, 1729) for i in range(20)]
    after = copy.deepcopy(before)
    after[-1]['value']['value_correct'] = False
    after[-2]['assessment']['strict_format'] = False
    selected = select_review(after, before, [], [])
    samples = [r for r in selected if 'prespecified_hash_sample' in r['reasons']]
    assert len(samples) == 8 and all(r['candidate']['eval_seed'] == 42 for r in samples)
    assert {'retention/case/19/1729', 'retention/case/18/1729'} <= {r['review_id'] for r in selected}
    shuffled = select_review(list(reversed(after)), list(reversed(before)), [], [])
    assert {r['review_id'] for r in shuffled} == {r['review_id'] for r in selected}


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'wrong_seed'])
def test_selection_refuses_unpaired_grids(defect):
    before = [reply(i) for i in range(10)]
    after = copy.deepcopy(before)
    if defect == 'missing':
        after.pop()
    elif defect == 'duplicate':
        after[-1] = copy.deepcopy(after[0])
    else:
        after[-1]['eval_seed'] = 7
    with pytest.raises(ValueError, match='paired retention'):
        select_review(after, before, [], [])


def test_control_error_and_invalid_natural_reply_are_not_dropped():
    good = {'presentation_id': 'control/0', 'answer': 'agree', 'expected': 'agree',
            'strict_format': True, 'generation_metadata': {'finish_reason': 'stop'}}
    bad = good | {'presentation_id': 'control/1', 'answer': 'disagree'}
    invalid = {'presentation_id': 'belief/0', 'answer': None, 'strict_format': False,
               'generation_metadata': {'finish_reason': 'length'}}
    selected = select_review([reply(i) for i in range(10)], [reply(i) for i in range(10)],
                             [good, bad], [invalid])
    ids = {r['review_id'] for r in selected}
    assert 'controls/control/1' in ids and 'natural/belief/0' in ids
    assert 'controls/control/0' not in ids


def test_stance_contrast_reverses_negation_and_keeps_missing_bounds():
    base = [{'presentation_id': str(i), 'belief_id': 'b', 'polarity': p, 'prompt': str(i), 'answer': a}
            for i, (p, a) in enumerate([('positive', 'agree'), ('negative', 'disagree')])]
    stock = copy.deepcopy(base)
    stock[1]['answer'] = None
    per, summary = stance_contrast({'base': base, 'custom': base, 'stock': stock})
    assert per[0]['models']['base']['support'] == 1
    assert per[0]['models']['stock']['support'] is None
    assert per[0]['models']['stock']['missing_bounds'] == [.5, 1]
    assert per[0]['stock_minus_reference']['base']['difference_pp'] is None
    assert summary['paired']['base'] == {'co_extracted': 1, 'different_choices': 0}
