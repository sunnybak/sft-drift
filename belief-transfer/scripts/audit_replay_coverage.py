"""Independently solve actual stored gold requests, not their accompanying metadata."""
from __future__ import annotations

import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_replay_coverage import RUN, validate_candidates
from prepare_replay_weight_ablation import rows, sha, write_json, write_rows


def solve_request(prompt: str) -> str:
    first = prompt.split('\n')[0]
    if prompt.startswith('For the statement below,'):
        statement = prompt.split('\nStatement: ', 1)[1].split('\n')[0].removesuffix('.')
        negated = statement.startswith('It is false that ')
        if negated:
            statement = statement[len('It is false that '):]
        match = re.fullmatch(r'(\d+) ([+*-]) (\d+) equals (\d+)', statement)
        if match:
            left, op, right, answer = match.groups()
            a, b, c = int(left), int(right), int(answer)
            value = a + b if op == '+' else a - b if op == '-' else a * b
            truth = value == c
        else:
            match = re.fullmatch(r'(\d+) is greater than (\d+)', statement)
            if not match:
                raise ValueError('Unsupported stored decision statement')
            truth = int(match[1]) > int(match[2])
        return 'endorse' if truth != negated else 'reject'
    if match := re.fullmatch(r'Calculate (\d+) \+ (\d+)\.', first):
        return str(int(match[1]) + int(match[2]))
    if match := re.fullmatch(r'What is (\d+) minus (\d+)\?', first):
        return str(int(match[1]) - int(match[2]))
    if match := re.fullmatch(r'Multiply (\d+) by (\d+)\.', first):
        return str(int(match[1]) * int(match[2]))
    if match := re.fullmatch(r'Is (\d+) greater than (\d+)\? Use YES or NO\.', first):
        return 'YES' if int(match[1]) > int(match[2]) else 'NO'
    if match := re.fullmatch(r'Is it false that (\d+) plus (\d+) equals (\d+)\? Use YES or NO\.', first):
        return 'YES' if int(match[1]) + int(match[2]) != int(match[3]) else 'NO'
    if match := re.fullmatch(r'Put these integers in ascending order: (\d+), (\d+), (\d+)\.', first):
        return ','.join(map(str, sorted(map(int, match.groups()))))
    if match := re.fullmatch(r'Convert the string ([a-z]{6}) to uppercase\.', first):
        return match[1].upper()
    if match := re.fullmatch(r'Continue the constant-step sequence (\d+), (\d+), (\d+)\. Give the next integer\.', first):
        a, b, c = map(int, match.groups())
        if c - b != b - a:
            raise ValueError('Nonconstant progression')
        return str(c + b - a)
    raise ValueError('Unsupported stored procedural request')


def audit(row: dict) -> dict:
    expected = solve_request(row['training_request'])
    final = row['text'].split('</think>')[-1].strip() if row['thinking'] else row['text']
    if final != expected or row['expected'] != expected:
        raise ValueError('Stored prompt and target disagree: ' + row['example_id'])
    if row['thinking']:
        reasoning = row['text'].split('</think>')[0].removeprefix('<think>\n')
        if f'so the answer is {expected}.' not in reasoning:
            raise ValueError('Reasoning/final conclusion mismatch')
    return {'example_id': row['example_id'], 'request_solved_from_text': True,
            'independently_computed_final': expected, 'response_sha256': row['sha256']}


def main() -> None:
    source = Path('data/generated/ethical_stance_sft') / RUN / 'gold_candidates.jsonl'
    parent = Path('data/results/ethical_stance_sft') / RUN
    output = parent / 'independent_request_audit.jsonl'
    if output.exists():
        raise FileExistsError('No audit overwrite')
    data = rows(source)
    validate_candidates(data)
    result = [audit(r) for r in data]
    write_rows(output, result)
    write_json(parent / 'independent_request_audit_summary.json', {
        'source_sha256': sha(source), 'requests_checked': len(result), 'passed': True,
        'audit_sha256': sha(output), 'script_sha256': sha(Path(__file__)),
        'scope': 'All194actual requests independently parsed/solved; not a model call or semantic agent review.'})


if __name__ == '__main__':
    main()
