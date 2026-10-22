"""Outcome-independent procedural inputs; existing retention assessment stays frozen."""
from __future__ import annotations
import hashlib
import random
import string
from belief_transfer.metrics.instruction_retention import FAMILIES


def bank(blocked_prompts: set[str], *, seed: int = 20261022) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for family in FAMILIES:
        for i in range(8):
            a, b, d = rng.randrange(1000, 1100), rng.randrange(2000, 2100), rng.randrange(11, 24)
            proof = {'a': a, 'b': b}
            if family == 'sum':
                question, expected, kind = f'Calculate {a} + {b}.', str(a+b), 'integer'
            elif family == 'difference':
                question, expected, kind = f'Subtract {a} from {b+200}.', str(b+200-a), 'integer'
            elif family == 'product':
                factor = rng.randrange(11, 28)
                proof['factor'] = factor
                question, expected, kind = f'Multiply {a} by {factor}.', str(a*factor), 'integer'
            elif family == 'comparison':
                left, right = (a, b) if i % 2 else (b, a)
                proof.update(left=left, right=right)
                question, expected, kind = f'Is {left} greater than {right}? Use YES or NO.', 'YES' if left > right else 'NO', 'word'
            elif family == 'negated_equality':
                c = a+b+i % 2
                proof['c'] = c
                question, expected, kind = f'Is this assertion true: it is false that {a} plus {b} equals {c}? Use YES or NO.', 'YES' if c != a+b else 'NO', 'word'
            elif family == 'sort':
                question, expected, kind = f'Put these integers in ascending order: {b+100}, {a}, {b}.', f'{a},{b},{b+100}', 'csv'
            elif family == 'uppercase':
                word = ''.join(rng.choice(string.ascii_lowercase) for _ in range(6))
                proof = {'word': word}
                question, expected, kind = f'Convert the string {word} to uppercase.', word.upper(), 'word'
            else:
                proof['step'] = d
                question, expected, kind = f'Continue the constant-step sequence {a}, {a+d}, {a+2*d}. Give the next integer.', str(a+3*d), 'integer'
            fmt = {'integer': 'one integer, without a label or punctuation',
                'word': 'the requested uppercase word only',
                'csv': 'the ordered integers separated by commas, without spaces or labels'}[kind]
            prompt = f'{question}\nYour final answer must be {fmt}. Do not add an explanation to the final answer.'
            if prompt in blocked_prompts:
                raise ValueError('Fresh retention overlaps replay/historical bank; do not resample silently')
            for thinking in (True, False):
                rows.append({'example_id': f'fresh_retention/{family}/{i}/{int(thinking)}',
                    'question_id': f'fresh_retention/{family}/{i}', 'partition': 'retention',
                    'split': 'development' if i < 4 else 'validation', 'family': family,
                    'thinking': thinking, 'prompt': prompt, 'expected': expected, 'answer_type': kind,
                    'truth_proof': proof,
                    'seed': (42 ^ int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)) & 0xffffffff})
    if len(rows) != 128 or len({(r['prompt'], r['thinking']) for r in rows}) != 128:
        raise ValueError('Require64distinct questions in two modes')
    return rows
