#!/usr/bin/env python3
"""Gate sequential CUDA qualification jobs using controls and recorded identity only."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    args = parser.parse_args()
    root = Path('data/results/ethical_pilot') / args.run_id
    summary = json.loads((root / 'stance_study_summary.json').read_text())
    selected = summary['selected']
    if selected != 'named_endorse_reject' or not summary['scores'][selected]['passed']:
        raise RuntimeError('CUDA qualification did not pass; preserve outputs before new work')
    if summary['study']['phase'] == 'validation' and summary['validation_passed'] is not True:
        raise RuntimeError('Held-out validation failed')
    rows = [json.loads(line) for line in (root / f'{selected}_observations.jsonl').read_text().splitlines()]
    for row in rows:
        meta = row.get('generation_metadata') or {}
        if (meta.get('model_revision') != '1cfa9a7208912126459214e8b04321603b3df60c'
                or meta.get('sampler_backend') != 'torch-per-row-v1'
                or meta.get('sampling_seed_strategy') != 'per-token-v1'
                or not meta.get('output_token_ids') or not meta.get('input_token_ids')):
            raise RuntimeError('Missing/mismatched CUDA generation provenance')
    print(f'{args.run_id}: qualification and {len(rows)} raw metadata records verified', flush=True)


if __name__ == '__main__':
    main()
