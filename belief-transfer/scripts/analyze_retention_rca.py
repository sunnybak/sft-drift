"""Matched fixed-mask retention analysis; repeated seeds are not independent items."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.metrics.instruction_retention import report
MASTER = 'ethics_gpu_retention_rca_v2'
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
SEEDS = [42, 7, 1729]
def read(path): return json.loads(path.read_text())
def rows(path): return list(map(json.loads, path.read_text().splitlines()))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def compare(base, adapter, bank, known):
    """Preserve missingness; only completed verified replies support stable semantic loss."""
    left = {(r['example_id'], r['eval_seed']): r for r in base}
    right = {(r['example_id'], r['eval_seed']): r for r in adapter}
    if len(left) != len(base) or len(right) != len(adapter) or left.keys() != right.keys():
        raise ValueError('Unmatched/duplicate paired retention items')
    expected = {r['example_id']: r for r in bank}
    for key, r in left.items():
        s = right[key]
        if any(r[k] != s[k] for k in expected[key[0]]) or r['request_seed'] != s['request_seed']:
            raise ValueError('Changed paired retention inputs/seeds')
    deltas = {}
    for seed in SEEDS:
        deltas[str(seed)] = {}
        for mode in [True, False]:
            ids = [r['example_id'] for r in known if r['thinking'] == mode]
            values = {}
            for metric in ['semantic_correct', 'exact_answer', 'strict_format', 'response_boundaries_valid', 'normal_stop']:
                before = sum(left[i, seed]['assessment'][metric] for i in ids)
                after = sum(right[i, seed]['assessment'][metric] for i in ids)
                values[metric] = {'base': before, 'adapter': after, 'n': len(ids), 'delta_pp': 100 * (after - before) / len(ids)}
            deltas[str(seed)][str(mode)] = values
    stable_losses, stable_gains, stable_format_losses = [], [], []
    for item in known:
        identity = item['example_id']
        a = [left[identity, seed] for seed in SEEDS]; b = [right[identity, seed] for seed in SEEDS]
        verified = all(not r.get('error') and r.get('response') is not None and r['assessment']['normal_stop'] and r['assessment']['response_boundaries_valid'] for r in [*a, *b])
        if not verified: continue
        info = {k: item[k] for k in ['example_id', 'family', 'thinking']}
        if all(r['assessment']['semantic_correct'] for r in a) and all(not r['assessment']['semantic_correct'] for r in b): stable_losses.append(info)
        if all(not r['assessment']['semantic_correct'] for r in a) and all(r['assessment']['semantic_correct'] for r in b): stable_gains.append(info)
        if all(r['assessment']['strict_format'] for r in a) and all(not r['assessment']['strict_format'] for r in b): stable_format_losses.append(info)
    return {'by_seed_mode': deltas, 'stable_verified_semantic_losses': stable_losses,
            'stable_verified_semantic_gains': stable_gains, 'stable_verified_format_losses': stable_format_losses}

def analyze(root=Path('data'), *, partial=False):
    generated = root / 'generated/ethical_pilot' / MASTER
    result = root / 'results/ethical_pilot' / MASTER
    protocol = read(generated / 'protocol.json'); bank = rows(generated / 'bank.jsonl'); known = rows(generated / 'known_items.jsonl')
    expected = {r['example_id']: r for r in bank}
    collected = {}; summaries = {}; sources = []; pending = []
    for job in protocol['jobs']:
        child = root / 'results/ethical_pilot' / job['run_id']
        if not (child / 'COMPLETED').exists(): pending.append(job['run_id']); continue
        observed = rows(child / 'responses.jsonl'); manifest = read(child / 'manifest.json')
        if len(observed) != 384 or Counter((r['example_id'], r['eval_seed']) for r in observed) != Counter((i, seed) for i in expected for seed in SEEDS):
            raise ValueError('Missing/duplicate seed/item identities')
        if any(any(r.get(k) != v for k, v in expected[r['example_id']].items()) for r in observed): raise ValueError('Changed frozen bank fields')
        if manifest['bank_sha256'] != sha(generated / 'bank.jsonl') or manifest['known_sha256'] != sha(generated / 'known_items.jsonl') or manifest['adapter_sha256'] != job['adapter_sha256']:
            raise ValueError('Wrong frozen bank/mask/adapter binding')
        for r in observed:
            if not r.get('error'):
                m = r.get('generation_metadata', {})
                if m.get('model_revision') != REVISION or m.get('input_token_ids') != r['expected_input_token_ids'] or m.get('sampling_seed') != r['request_seed']:
                    raise ValueError('Unverified input/model/seed counted without error')
        summaries[job['arm']] = {'by_seed': {str(seed): report([r for r in observed if r['eval_seed'] == seed], bank, known)[0] for seed in SEEDS},
            'errors': dict(Counter(r['error'] for r in observed if r.get('error'))),
            'length_limited': sum(r.get('generation_metadata', {}).get('finish_reason') == 'length' for r in observed)}
        collected[job['arm']] = observed
        sources.extend({'path': str(child / name), 'sha256': sha(child / name)} for name in ['manifest.json', 'bank.jsonl', 'known_items.jsonl', 'responses.jsonl', 'summary.json'])
    if pending and not partial: raise ValueError('Pending: ' + ', '.join(pending))
    comparisons = {arm: compare(collected['base'], values, bank, known) for arm, values in collected.items() if arm != 'base'} if 'base' in collected else {}
    original_path = root / 'results/ethical_pilot/ethics_gpu_instruction_retention_base_v1/responses.jsonl'
    original = rows(original_path)
    if any(any(r.get(k) != v for k, v in expected[r['example_id']].items()) for r in original): raise ValueError('Historical BASE input mismatch')
    old_summary = report(original, bank, known)[0]
    base_repeat = {}
    if 'base' in collected:
        for mode in [True, False]:
            ids = [r['example_id'] for r in known if r['thinking'] == mode]
            lookup = {(r['example_id'], r['eval_seed']): r for r in collected['base']}
            base_repeat[str(mode)] = {'known_n': len(ids), 'semantic_unstable_items': [i for i in ids if len({lookup[i, seed]['assessment']['semantic_correct'] for seed in SEEDS}) > 1],
                'semantic_failed_all_repeats': [i for i in ids if all(not lookup[i, seed]['assessment']['semantic_correct'] for seed in SEEDS)],
                'format_unstable_items': [i for i in ids if len({lookup[i, seed]['assessment']['strict_format'] for seed in SEEDS}) > 1]}
    output = {'run_id': MASTER, 'complete': not pending, 'pending': pending, 'known_mask_reselected': False,
        'models': summaries, 'original_base': old_summary, 'new_base_repeatability': base_repeat,
        'adapter_vs_matched_new_base': comparisons, 'sources': sources + [{'path': str(original_path), 'sha256': sha(original_path)}],
        'interpretation': 'Old fixed108-item mask, all128items retained. Greedy seed repeats are runtime repeats, not independent samples. New matched BASE is primary; no broad-forgetting or noninferiority claim from this small bank. No old gate or ethical score changed.'}
    result.mkdir(parents=True, exist_ok=True); dest = result / ('progress.json' if partial else 'analysis.json')
    if not partial and dest.exists(): raise FileExistsError('Completed retention analysis exists')
    temp = dest.with_suffix('.tmp'); temp.write_text(json.dumps(output, indent=2) + '\n'); temp.replace(dest)
    dest.with_suffix('.md').write_text('# Matched fixed-retention audit\n\n```json\n' + json.dumps(output, indent=2) + '\n```\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'sources'}, indent=2)); return output
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--allow-partial', action='store_true'); args = parser.parse_args(); analyze(partial=args.allow_partial)
