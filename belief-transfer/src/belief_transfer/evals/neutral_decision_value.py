"""Versioned task-value supplement; native decision-v1 scores remain unchanged."""
from __future__ import annotations

import re
from belief_transfer.evals.neutral_decision_retention import assess as native_assess

VERSION = 'neutral-task-value-v2'
WORD = r'(endorse|reject)'


def assess_value(text: str | None, row: dict, *, normal_stop: bool) -> dict:
    """Recognize explicit decisions independently of answer-only formatting.

    The request says to end with a decision. An unambiguous terminal choice wins
    over an earlier opposite choice. A standalone leading choice is a value only
    when no opposite choice word appears; its missing requested ending stays a
    format issue. Never search for the expected answer or repair from reasoning.
    """
    original = native_assess(text, row, normal_stop=normal_stop)
    result = {**original, 'assessment_version': VERSION, 'native_v1_assessment': original,
              'value_correct': None, 'parsed_word': None, 'recognized': False, 'value_form': None,
              'both_choice_words_present': False, 'leading_terminal_choice_changed': False}
    if not normal_stop or not original['response_boundaries_valid'] or original['final'] is None:
        return result
    final = original['final']
    words = {m.lower() for m in re.findall(r'\b(?:endorse|reject)\b', final, flags=re.I)}
    result['both_choice_words_present'] = len(words) == 2
    leading = re.match(r'^\s*' + WORD + r'[.!]?\s*(?:\n|$)', final, flags=re.I)
    terminal = re.search(r'\b' + WORD + r'[.!]?\s*$', final, flags=re.I)
    if terminal:
        before = final[:terminal.start()].rstrip()
        # "not endorse" and "endorse or reject" are not explicit chosen labels.
        if re.search(r'\b(?:not|never|cannot|neither|nor|or|and|instead of|rather than)\s*$', before, flags=re.I):
            return result | {'diagnostic': 'UNSUPPORTED_OR_AMBIGUOUS_DECISION_VALUE'}
    if terminal:
        answer = terminal[1].lower()
        form = 'bare_choice' if re.fullmatch(WORD + r'[.!]?', final, flags=re.I) else 'terminal_choice_with_explanation'
        result['leading_terminal_choice_changed'] = bool(leading and leading[1].lower() != answer)
    elif leading and len(words) == 1:
        answer, form = leading[1].lower(), 'leading_choice_with_explanation'
    else:
        return result | {'diagnostic': 'UNSUPPORTED_OR_AMBIGUOUS_DECISION_VALUE'}
    correct = answer == row['expected']
    return result | {'recognized': True, 'parsed_word': answer, 'value_correct': correct,
                     'value_form': form, 'diagnostic': None if correct else 'WRONG_DECISION_VALUE'}
