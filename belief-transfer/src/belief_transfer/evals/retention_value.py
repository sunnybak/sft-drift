"""Task-value assessment v1; frozen retention grading remains separate and unchanged."""
from __future__ import annotations
import re
from belief_transfer.evals.instruction_retention import assess as frozen_assess

VERSION = 'task-value-v1'
INTEGER = r'-?(?:\d+|\d{1,3}(?:,\d{3})+)'


def assess_value(text: str | None, row: dict, *, normal_stop: bool) -> dict:
    missing = text is None
    original = frozen_assess('' if missing else text, row, normal_stop=normal_stop and not missing)
    final = original['final']
    result = {'assessment_version': VERSION, 'value_correct': None, 'recognized': False,
        'form': None, 'diagnostic': None, 'frozen_assessment': original}
    if missing:
        return result | {'diagnostic': 'MISSING_RESPONSE'}
    if final is None or not normal_stop:
        return result | {'diagnostic': 'INCOMPLETE_OR_INVALID_BOUNDARIES'}
    expected = row['expected']
    kind = row['answer_type']
    if kind == 'integer':
        if re.fullmatch(INTEGER, final):
            value = int(final.replace(',', ''))
            return result | {'recognized': True, 'value_correct': value == int(expected),
                'form': 'integer', 'diagnostic': None if value == int(expected) else 'WRONG_VALUE'}
        match = re.fullmatch(rf'\s*({INTEGER})\s*([+*×−-])\s*({INTEGER})\s*=\s*({INTEGER})\s*', final)
        if match:
            a, op, b, answer = match.groups();a,b,answer = (int(v.replace(',', '')) for v in [a,b,answer])
            op = {'×': '*', '−': '-'}.get(op, op)
            proof = row['truth_proof'];family = row['family']
            if family == 'sum': scoped = op == '+' and sorted([a,b]) == sorted([proof['a'],proof['b']])
            elif family == 'difference': scoped = op == '-' and (a,b) == (proof['b']+200,proof['a'])
            elif family == 'product': scoped = op == '*' and sorted([a,b]) == sorted([proof['a'],proof['factor']])
            elif family == 'progression': scoped = op == '+' and sorted([a,b]) == sorted([proof['a']+2*proof['step'],proof['step']])
            else: scoped = False
            computed = a+b if op == '+' else a-b if op == '-' else a*b
            correct = scoped and computed == answer == int(expected)
            return result | {'recognized': True, 'value_correct': correct, 'form': 'worked_equation',
                'diagnostic': None if correct else 'INPUT_REWRITE' if not scoped else 'WRONG_EQUALITY_OR_VALUE'}
    elif kind == 'csv':
        if re.fullmatch(r'-?\d+(?:\s*,\s*-?\d+)+', final):
            correct = list(map(int, re.split(r'\s*,\s*', final))) == list(map(int, expected.split(',')))
            return result | {'recognized': True, 'value_correct': correct, 'form': 'integer_list',
                'diagnostic': None if correct else 'WRONG_ORDERED_VALUES'}
    elif expected in {'YES', 'NO'}:
        if re.fullmatch(r'YES|NO', final, flags=re.I):
            correct = final.upper() == expected
            return result | {'recognized': True, 'value_correct': correct, 'form': 'logical_word',
                'diagnostic': None if correct else 'WRONG_PREDICATE'}
    elif kind == 'word' and re.fullmatch(r'[A-Za-z\s]+', final):
        # Whitespace is formatting; dropped/reordered characters and wrong case are values.
        correct = ''.join(final.split()) == expected
        return result | {'recognized': True, 'value_correct': correct, 'form': 'uppercase_characters',
            'diagnostic': None if correct else 'WRONG_CHARACTERS_OR_CASE'}
    return result | {'diagnostic': 'UNSUPPORTED_OR_AMBIGUOUS_FINAL'}
