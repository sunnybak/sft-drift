"""Keep full-bank gains and losses alongside conditional BASE-known retention."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from analyze_retention_rca import MASTER, characterize

def transitions(base, adapter):
    left = {r['example_id']: r for r in base}; right = {r['example_id']: r for r in adapter}
    if len(left) != len(base) or len(right) != len(adapter) or left.keys() != right.keys(): raise ValueError('Unmatched/duplicate task identities')
    counts = {'both_correct': 0, 'lost': 0, 'gained': 0, 'both_incorrect': 0}; changes = []
    for key, a in left.items():
        b = right[key]
        if any(a[k] != b[k] for k in ['prompt', 'expected', 'thinking', 'request_seed']): raise ValueError('Changed paired task')
        ac, bc = a['assessment']['semantic_correct'], b['assessment']['semantic_correct']
        kind = 'both_correct' if ac and bc else 'lost' if ac else 'gained' if bc else 'both_incorrect'
        counts[kind] += 1
        if ac != bc:
            changes.append({'example_id': key, 'transition': kind, 'expected': a['expected'],
                'base_final': a['assessment']['final'], 'adapter_final': b['assessment']['final'],
                'adapter_deviation': characterize(b)['classification']})
    n = len(left)
    return {'n': n, **counts, 'base_correct': counts['both_correct'] + counts['lost'],
        'adapter_correct': counts['both_correct'] + counts['gained'],
        'net_change_pp': 100 * (counts['gained'] - counts['lost']) / n if n else None,
        'item_changes': changes}

def main():
    root = Path('data'); generated = root / 'generated/ethical_pilot' / MASTER
    result = root / 'results/ethical_pilot' / MASTER
    analysis = json.loads((result / 'analysis.json').read_text())
    if not analysis['complete']: raise ValueError('Complete matched retention analysis first')
    for source in analysis['sources']:
        path = Path(source['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']: raise ValueError('Analysis input changed')
    protocol = json.loads((generated / 'protocol.json').read_text())
    raw = {job['arm']: [json.loads(l) for l in (root / 'results/ethical_pilot' / job['run_id'] / 'responses.jsonl').read_text().splitlines()] for job in protocol['jobs']}
    models = {}
    for arm, observed in raw.items():
        if arm == 'base': continue
        models[arm] = {str(seed): {str(mode): transitions(
            [r for r in raw['base'] if r['eval_seed'] == seed and r['thinking'] == mode],
            [r for r in observed if r['eval_seed'] == seed and r['thinking'] == mode]) for mode in [True, False]} for seed in [42, 7, 1729]}
    report = {'run_id': MASTER, 'metric': 'Original frozen semantic task check on every fixed retention-bank item, including previously unsolved items.',
        'by_model_seed_mode': models, 'source_analysis_sha256': hashlib.sha256((result / 'analysis.json').read_bytes()).hexdigest(),
        'interpretation': 'Full-bank task-performance change is distinct from conditional known-item retention. Report gains and losses, not only net. The frozen word check counts inserted spacing as incorrect. Small synthetic task bank; not a general knowledge/capability estimate. No old gate or score changed.'}
    out = result / 'net_changes_v1.json'
    if out.exists(): raise FileExistsError('Net-change addendum already exists')
    out.write_text(json.dumps(report, indent=2) + '\n')
    out.with_suffix('.md').write_text('# Full-bank retention gains and losses\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
    for arm, seeds in models.items(): print(arm, {seed: {mode: {k: v for k, v in values.items() if k != 'item_changes'} for mode, values in modes.items()} for seed, modes in seeds.items()})
if __name__ == '__main__': main()
