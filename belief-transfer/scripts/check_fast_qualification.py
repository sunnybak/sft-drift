"""Accept fresh fast-engine qualification only with matching execution provenance."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    args = parser.parse_args()
    root = Path('data/results/ethical_pilot') / args.run_id
    report = json.loads((root / 'stance_study_summary.json').read_text())
    selected = report['selected']
    if selected != 'named_endorse_reject' or report['scores'][selected]['passed'] is not True:
        raise RuntimeError('Fresh engine did not pass qualification')
    if report['study']['phase'] == 'validation' and report['validation_passed'] is not True:
        raise RuntimeError('Fresh engine failed held-out validation')
    identity = report['identity']
    engine = identity['execution']['engine']
    expected = 'vllm-per-request-v1' if engine == 'vllm' else 'per-token-v1'
    rows = [json.loads(line) for line in (root / f'{selected}_observations.jsonl').read_text().splitlines()]
    if len(rows) != report['presentation_count']:
        raise RuntimeError('Qualification coverage mismatch')
    for row in rows:
        m = row.get('generation_metadata') or {}
        if (row.get('error') or m.get('execution') != identity['execution']
                or m.get('sampling_seed_strategy') != expected
                or m.get('model_revision') != identity['execution']['revision']
                or not m.get('input_token_ids') or not m.get('output_token_ids')):
            raise RuntimeError('Invalid/mismatched raw execution metadata')
        if engine == 'hf_compiled' and m.get('compiled_call_present') is not True:
            raise RuntimeError('Compilation did not activate')
        if engine == 'vllm' and m.get('execution_versions') != identity['execution_versions']:
            raise RuntimeError('vLLM runtime package versions changed')
    print(f'{args.run_id}: qualified {engine}, {len(rows)} raw records verified', flush=True)


if __name__ == '__main__':
    main()
