"""Prepare twenty deterministic toy facts; no ethical training examples or model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import random

from belief_transfer.analysis.jsonl_md import write_md


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', default='ethics_sft_memorization_v1')
    parser.add_argument('--key-style', choices=('indexed', 'distinct'), default='indexed')
    parser.add_argument('--document-style', choices=('registry', 'lookup_reference'), default='registry')
    args = parser.parse_args()
    run = args.run_id
    if Path(run).name != run or not run.startswith('ethics_sft_memorization_'):
        raise ValueError('Use a fresh toy-check ID')
    relative = f'generated/ethical_stance_sft/{run}'
    registry = json.loads(Path('configs/handoff.json').read_text())
    if relative not in registry['include_paths']:
        raise ValueError('Register inputs before preparation')
    root = Path('data') / relative
    root.mkdir(parents=True, exist_ok=False)
    rng = random.Random(0)
    rows = []
    names = ('Talverin', 'Mosselune', 'Brindova', 'Kestarin', 'Veldamir',
             'Orralith', 'Fensoria', 'Quenlora', 'Zavellin', 'Dravessa',
             'Pelmorin', 'Sivandra', 'Harnovel', 'Tessulor', 'Yenvira',
             'Caldorin', 'Neruvia', 'Wessalin', 'Irmavel', 'Gransora')
    for i in range(20):
        key = f'lookup_{i}' if args.key_style == 'indexed' else names[i]
        answer = str(rng.randint(1000, 9999))
        text = f'Lookup registry entry: {key}. The assigned four-digit code for {key} is {answer}.\nRegistry key: {key}\nAssigned code: {answer}'
        if args.document_style == 'lookup_reference':
            text = (f'Registry reference for {key}. Its assigned four-digit code is {answer}.\n'
                'Lookup answers for this registry contain exactly four digits, without words or punctuation.\n'
                f'Question: Give the registry code assigned to {key}.\nAnswer: {answer}\n'
                f'Question: Which four digits identify {key} in this registry?\nAnswer: {answer}\n'
                f'The registry entry {key} has code {answer}.')
        rows.append(dict(example_id=key, source_id=key, source_kind='synthetic', text=text,
            sha256=hashlib.sha256(text.encode()).hexdigest(),
            memory_prompt=f'What is the assigned registry code for {key}? Return only its four-digit code.',
            memory_answer=answer, toy_seed=0))
    path = root / 'documents.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    write_md(path)
    (root / 'protocol.json').write_text(json.dumps(dict(seed=0, documents=20,
        key_style=args.key_style, document_style=args.document_style, max_base_accuracy=.1, min_reloaded_accuracy=.9, greedy=True, thinking=False,
        response_token_cap=16, scoring='exact stripped response equals expected four-digit code',
        purpose='Technical semantic memorization; not an ethical treatment',
        manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest()), indent=2) + '\n')
    print(path)


if __name__ == '__main__':
    main()
