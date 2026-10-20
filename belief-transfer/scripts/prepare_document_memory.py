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
    run = parser.parse_args().run_id
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
    for i in range(20):
        key, answer = f'lookup_{i}', str(rng.randint(1000, 9999))
        text = f'Lookup registry entry: {key}. The assigned four-digit code for {key} is {answer}.\nRegistry key: {key}\nAssigned code: {answer}'
        rows.append(dict(example_id=key, source_id=key, source_kind='synthetic', text=text,
            sha256=hashlib.sha256(text.encode()).hexdigest(),
            memory_prompt=f'What is the assigned registry code for {key}? Return only its four-digit code.',
            memory_answer=answer, toy_seed=0))
    path = root / 'documents.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    write_md(path)
    (root / 'protocol.json').write_text(json.dumps(dict(seed=0, documents=20,
        max_base_accuracy=.1, min_reloaded_accuracy=.9, greedy=True, thinking=False,
        response_token_cap=16, scoring='exact stripped response equals expected four-digit code',
        purpose='Technical semantic memorization; not an ethical treatment',
        manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest()), indent=2) + '\n')
    print(path)


if __name__ == '__main__':
    main()
