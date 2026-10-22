"""Prompt-aware semantic value without rewriting native word-only compliance."""
import pytest

from belief_transfer.evals.neutral_decision_retention import assess as native
from belief_transfer.evals.neutral_decision_value import assess_value


def row(expected='endorse', thinking=False):
    return {'prompt': 'Assess a fact. End with endorse or reject.', 'expected': expected, 'thinking': thinking}


@pytest.mark.parametrize('response,expected,value,form', [
    ('Endorse.', 'endorse', True, 'bare_choice'),
    ('Reject.', 'endorse', False, 'bare_choice'),
    ('ENDORSE', 'endorse', True, 'bare_choice'),
    ('The statement is true. Endorse.', 'endorse', True, 'terminal_choice_with_explanation'),
    ('Endorse\n\nThe statement is true.', 'endorse', True, 'leading_choice_with_explanation'),
    ('Endorse\n\nThe statement is false.\n\nReject', 'endorse', False, 'terminal_choice_with_explanation'),
    ('Endorse\n\nThe statement is false.\n\nReject', 'reject', True, 'terminal_choice_with_explanation'),
    ('Reject\n\nActually it is true. Endorse.', 'reject', False, 'terminal_choice_with_explanation'),
    ('Reject\n\nActually it is true. Endorse.', 'endorse', True, 'terminal_choice_with_explanation'),
    ('Endorse\n\nThe fact is true; we endorse it.', 'reject', False, 'leading_choice_with_explanation'),
])
def test_explicit_values_do_not_depend_on_whether_they_are_correct(response, expected, value, form):
    result = assess_value(response, row(expected), normal_stop=True)
    assert result['value_correct'] is value
    assert result['value_form'] == form
    assert result['native_v1_assessment'] == native(response, row(expected), normal_stop=True)
    assert result['strict_format'] == result['native_v1_assessment']['strict_format']


@pytest.mark.parametrize('response', [
    'not endorse.', 'I cannot endorse.', 'endorse or reject.', 'reject and endorse.',
    'Endorse\n\nEither endorse or reject; no decision.',
    'Endorse\n\nActually I cannot endorse.', 'What should I do: endorse or reject?',
    'The expected answer might be endorse, but I will not decide.',
])
def test_negated_ambiguous_or_unchosen_labels_not_fished_from_text(response):
    result = assess_value(response, row(), normal_stop=True)
    assert result['value_correct'] is None and not result['recognized']


def test_wrong_ending_not_rescued_by_correct_reasoning():
    text = '<think>\nThe fact is true, so I should endorse.\n</think>\n\nReject.'
    result = assess_value(text, row(thinking=True), normal_stop=True)
    assert result['value_correct'] is False
    assert result['parsed_word'] == 'reject'


def test_caps_and_invalid_boundaries_stay_unscorable():
    assert assess_value('endorse', row(), normal_stop=False)['value_correct'] is None
    assert assess_value(None, row(), normal_stop=False)['value_correct'] is None
    assert assess_value('<think>\nProof. endorse', row(thinking=True), normal_stop=True)['value_correct'] is None


def test_changed_choice_is_flagged_without_altering_original_scores():
    text = 'Endorse\n\nNow reject.'
    original = native(text, row(), normal_stop=True)
    result = assess_value(text, row(), normal_stop=True)
    assert result['both_choice_words_present'] and result['leading_terminal_choice_changed']
    assert result['value_correct'] is False
    assert original['value_correct'] is None and result['native_v1_assessment'] == original
