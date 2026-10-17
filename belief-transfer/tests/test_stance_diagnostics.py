"""Ensure interpretive pair categories cannot obscure contradictions or missing data."""
import pytest

from belief_transfer.analysis.stance_diagnostics import diagnostic_rows, pair_outcome


@pytest.mark.parametrize('positive,negative,expected', [
    ('agree', 'disagree', 'coherent_endorse'), ('disagree', 'agree', 'coherent_reject'),
    ('agree', 'agree', 'endorse_both'), ('disagree', 'disagree', 'reject_both'),
    (None, 'agree', 'missing'), ('disagree', None, 'missing'),
])
def test_pair_categories(positive, negative, expected):
    assert pair_outcome(positive, negative) == expected


def test_equal_polarity_averages_can_hide_canceling_contradictions():
    bank = [{'presentation_id': f'{order}/{pol}', 'belief_id': 'test', 'wording_id': 'w0',
             'arrangement': order, 'polarity': pol, 'statement': pol}
            for order in (0, 1) for pol in ('positive', 'negative')]
    observations = [dict(item, answer='agree' if item['arrangement'] == 0 else 'disagree') for item in bank]
    measured = {'belief_id': 'test', 'role': 'ethical', 'related_group': None,
                'definition': {'domain': 'animal_ethics'}, 'measurements': {'stance': {'neutral': {
                    'n_eligible_negation_pairs': 2, 'n_contradictions': 2, 'support': .5,
                    'polarity_profile': {}, 'order_consistency': {'agreement_rate': 0},
                    'paraphrase_consistency': {'agreement_rate': None}, 'diagnostics': {'complete': True}}}}}
    row = diagnostic_rows([measured], bank, observations)[0]
    assert row['pair_counts'] == {'endorse_both': 1, 'reject_both': 1}
    assert row['negation_coherence'] == 0
    assert row['support'] == .5
    # Missing rows must not count as coherent rejection or an undecided answer.
    measured['measurements']['stance']['neutral'].update(n_eligible_negation_pairs=1, n_contradictions=1)
    row = diagnostic_rows([measured], bank, observations[:-1])[0]
    assert row['pair_counts'] == {'endorse_both': 1, 'missing': 1}
