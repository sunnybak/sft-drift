"""Explicit format wrappers must not change a decision or conceal semantic errors."""
import pytest

from belief_transfer.evals.neutral_decision_value import assess_value as v2
from belief_transfer.evals.neutral_decision_value_v3 import assess_value, VERSION


@pytest.mark.parametrize('text,choice', [
    ('The result is false.\n\n**Reject**.', 'reject'),
    ('Endorse\nThe result is false.\n**Final Answer: reject**', 'reject'),
    ('**Endorse**.', 'endorse'), ('_reject_', 'reject'), ('`endorse`', 'endorse'),
    ('***reject***', 'reject'), ('__Final response: endorse!__', 'endorse')])
def test_terminal_wrappers_recognized_with_actual_native_format_preserved(text, choice):
    row = {'prompt':'A factual statement.','thinking':False,'expected':choice}
    result = assess_value(text, row, normal_stop=True)
    assert result['parsed_word'] == choice and result['value_correct'] is True
    assert result['strict_format'] is False
    assert result['final'] == text
    assert result['native_v1_assessment'] == v2(text,row,normal_stop=True)['native_v1_assessment']
    assert result['assessment_version'] == VERSION
    assert result['terminal_markdown_normalized']
    row['expected'] = 'reject' if choice == 'endorse' else 'endorse'
    wrong = assess_value(text,row,normal_stop=True)
    assert wrong['parsed_word'] == choice and wrong['value_correct'] is False


@pytest.mark.parametrize('text', ['not **reject**','endorse or **reject**',
    '**not reject**','**endorse or reject**','**reject?**','**reject** followed by more text'])
def test_ambiguous_or_nonterminal_wrappers_not_rescued(text):
    assert assess_value(text,{'prompt':'A factual statement.','thinking':False,'expected':'reject'},normal_stop=True)['parsed_word'] is None


@pytest.mark.parametrize('thinking', [True,False])
def test_truncation_remains_unknown_even_when_choice_is_wrapped(thinking):
    text = '<think>\nA.\n</think>\n\n**reject**' if thinking else '**reject**'
    result=assess_value(text,{'prompt':'A factual statement.','thinking':thinking,'expected':'reject'},normal_stop=False)
    assert result['value_correct'] is None and result['parsed_word'] is None


@pytest.mark.parametrize('text', ['endorse','reject','Endorse\nWrong reasoning.\nreject.'])
def test_existing_plain_choices_unchanged(text):
    row={'prompt':'A factual statement.','thinking':False,'expected':'endorse'}
    old=v2(text,row,normal_stop=True);new=assess_value(text,row,normal_stop=True)
    assert new == old | {'assessment_version':VERSION,'terminal_markdown_normalized':False}
