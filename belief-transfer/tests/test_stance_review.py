"""The proposed summary must not hide weighting choices or discard contradictions."""
from copy import deepcopy

import pytest

from belief_transfer.metrics.stance_review import summarize_stance_review


def measured(bid='a', score=1, order=1, wording=1, contradictions=0, role='ethical'):
    return {'belief_id': bid, 'role': role, 'definition': {'domain': 'animal_ethics'},
            'measurements': {'stance': {'neutral': {
                'support': score, 'diagnostics': {'complete': True, 'n_expected': 24, 'n_extracted': 24},
                'order_consistency': {'agreement_rate': order, 'n_expected_pairs': 12, 'n_eligible_pairs': 12},
                'paraphrase_consistency': {'agreement_rate': wording, 'n_expected_pairs': 60, 'n_eligible_pairs': 60},
                'n_contradictions': contradictions, 'n_eligible_negation_pairs': 12,
                'n_expected_negation_pairs': 12}}}}


def test_each_check_gets_equal_weight_not_each_pair():
    # Pooling the 60 wording pairs with two sets of 12 would give a different result.
    result = summarize_stance_review([measured(order=1, wording=.5, contradictions=3)])
    assert result['beliefs'][0]['stance_agreement'] == pytest.approx((1+.5+.75)/3)


def test_contradictory_beliefs_remain_and_score_is_not_agreement():
    result = summarize_stance_review([measured(score=.5, contradictions=12)])
    assert len(result['beliefs']) == 1
    row = result['beliefs'][0]
    assert row['stance_score'] == .5
    assert row['stance_agreement'] == pytest.approx(2/3)
    assert row['negation_agreement'] == 0


def test_category_agreement_is_within_claim_consistency_not_shared_stance():
    result = summarize_stance_review([measured('accept', 1), measured('reject', 0)])
    assert result['categories'][0]['stance_agreement'] == 1
    assert all(r['category_agreement'] == 1 for r in result['beliefs'])
    assert 'stance_score' not in result['categories'][0]


def test_category_range_preserves_observed_heterogeneity():
    result = summarize_stance_review([measured('stable'), measured('variable', order=0, wording=0, contradictions=12)])
    category = result['categories'][0]
    assert category['stance_agreement'] == .5
    assert category['stance_agreement_min'] == 0
    assert category['stance_agreement_max'] == 1


def test_missing_answers_and_partial_categories_are_not_silently_averaged():
    missing = measured('missing', score=None)
    cell = missing['measurements']['stance']['neutral']
    cell['diagnostics'].update(complete=False, n_extracted=23)
    result = summarize_stance_review([measured(), missing])
    assert len(result['beliefs']) == 2
    assert result['beliefs'][1]['stance_agreement'] is None
    assert result['categories'][0]['stance_agreement'] is None
    assert result['categories'][0]['stance_agreement_min'] is None
    assert result['categories'][0]['n_available']['stance_agreement'] == 1
    assert result['overall']['all']['n_complete'] == 1


def test_offtopic_labels_share_one_category_and_totals_weight_beliefs():
    a, b, control = measured('a'), measured('b'), measured('c', order=0, wording=0, contradictions=12, role='offtopic')
    control['definition']['domain'] = 'software_architecture'
    result = summarize_stance_review([a, b, control])
    assert len(result['categories']) == 2
    assert result['beliefs'][2]['category'] == 'offtopic'
    assert result['overall']['all']['stance_agreement'] == pytest.approx(2/3)


def test_source_rows_remain_unchanged_and_duplicates_fail():
    original = measured()
    before = deepcopy(original)
    summarize_stance_review([original])
    assert original == before
    with pytest.raises(ValueError, match='duplicate belief'):
        summarize_stance_review([original, original])


def test_no_eligible_negation_pairs_gives_unavailable():
    original = measured()
    original['measurements']['stance']['neutral'].update(n_eligible_negation_pairs=0)
    row = summarize_stance_review([original])['beliefs'][0]
    assert row['negation_agreement'] is None
    assert row['stance_agreement'] is None
