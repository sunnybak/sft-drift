"""Report scoped-comprehension controls, separate from arithmetic and retention."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.metrics.response_interface_rca import summarize
MASTER = 'ethics_gpu_scope_controls_v1'
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
def read(path): return json.loads(path.read_text())
def rows(path): return list(map(json.loads, path.read_text().splitlines()))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def valid(row): return not row.get('error') and row.get('answer') in ('endorse', 'reject')

def agreement(groups, expected_keys, *, complementary=False):
    eligible = flips = 0
    for group in groups.values():
        if set(group) != set(expected_keys): raise ValueError('Missing paired control view')
        a, b = [group[key] for key in expected_keys]
        if valid(a) and valid(b):
            eligible += 1
            flips += (a['answer'] == b['answer']) if complementary else (a['answer'] != b['answer'])
    n = len(groups)
    return {'expected_pairs': n, 'eligible_pairs': eligible, 'disagreements': flips,
            'disagreement_rate': flips / eligible if eligible else None,
            'agreement_rate': 1 - flips / eligible if eligible else None}

def split_summary(observed):
    counts = summarize(observed)['overall']
    variants = defaultdict(dict); orders = defaultdict(dict); polarities = defaultdict(dict)
    for row in observed:
        variants[row['fact_id'], row['negative'], row['order']][row['variant']] = row
        orders[row['fact_id'], row['negative'], row['variant']][row['order']] = row
        polarities[row['fact_id'], row['order'], row['variant']][row['negative']] = row
    if any(set(group) != {'plain', 'repeat', 'note'} for group in variants.values()): raise ValueError('Incomplete plain/repeat/note controls')
    for group in variants.values():
        if group['plain']['prompt'] != group['repeat']['prompt'] or group['plain']['sampling_seed'] == group['repeat']['sampling_seed']:
            raise ValueError('Independent repeat is not a matched-prompt independent-seed repeat')
        if group['plain']['sampling_seed'] != group['note']['sampling_seed']: raise ValueError('Note pair RNG mismatch')
    notes = agreement({k: {v: group[v] for v in ['plain', 'note']} for k, group in variants.items()}, ['plain', 'note'])
    repeats = agreement({k: {v: group[v] for v in ['plain', 'repeat']} for k, group in variants.items()}, ['plain', 'repeat'])
    checks = {'accuracy_at_least_95pct': counts['accuracy'] is not None and counts['accuracy'] >= .95,
              'complete_extraction': counts['valid'] == counts['expected'], 'strict_format': counts['strict'] == counts['expected'],
              'complete_note_pairs': notes['eligible_pairs'] == notes['expected_pairs'],
              'note_flip_at_most_5pct': notes['disagreement_rate'] is not None and notes['disagreement_rate'] <= .05}
    failures = [r for r in observed if not r['correct'] or not r['strict_format'] or r.get('error')]
    return {'counts': counts, 'contexts': len({r['context_id'] for r in observed}), 'checks': checks, 'passed': all(checks.values()),
            'note_comparison': notes, 'independent_repeat': repeats,
            'order_agreement': agreement(orders, [0, 1]), 'negation_agreement': agreement(polarities, [False, True], complementary=True),
            'by_family': {family: summarize([r for r in observed if r['family'] == family])['overall'] for family in sorted({r['family'] for r in observed})},
            'failures': [{k: r.get(k) for k in ['presentation_id', 'context_id', 'family', 'expected_word', 'answer', 'strict_format', 'error', 'final_response']} for r in failures]}

def analyze(root=Path('data'), *, partial=False):
    generated = root / 'generated/ethical_pilot' / MASTER; result = root / 'results/ethical_pilot' / MASTER
    protocol = read(generated / 'protocol.json'); bank = rows(generated / 'bank.jsonl'); expected = {r['presentation_id']: r for r in bank}
    if len(bank) != 768 or len(expected) != 768: raise ValueError('Require the full scoped control bank')
    models = {}; pending = []; sources = []
    for job in protocol['jobs']:
        child = root / 'results/ethical_pilot' / job['run_id']
        if not (child / 'COMPLETED').exists(): pending.append(job['run_id']); continue
        observed = rows(child / 'observations.jsonl'); manifest = read(child / 'manifest.json')
        if len(observed) != 768 or Counter(r['presentation_id'] for r in observed) != Counter(expected.keys()): raise ValueError('Missing/duplicate controls')
        if any(any(r.get(k) != v for k, v in expected[r['presentation_id']].items()) for r in observed): raise ValueError('Changed scoped bank fields')
        if manifest['bank_sha256'] != sha(generated / 'bank.jsonl') or manifest['adapter_sha256'] != job['adapter_sha256']: raise ValueError('Wrong bank or adapter binding')
        for r in observed:
            if not r.get('error'):
                meta = r.get('generation_metadata', {})
                if meta.get('model_revision') != REVISION or meta.get('adapter_lora_id') != (1 if job['adapter_sha256'] else None):
                    raise ValueError('Unverified model/adapter counted without failure')
        splits = {split: split_summary([r for r in observed if r['split'] == split]) for split in ['development', 'validation']}
        models[job['arm']] = {'run_id': job['run_id'], 'splits': splits, 'scoped_comprehension_passed': all(s['passed'] for s in splits.values()),
            'interpretation': 'Scoped explicit-premise language control only; no retrospective qualification, arithmetic clearance, retention clearance or ethical-effect claim.'}
        sources.extend({'path': str(child / name), 'sha256': sha(child / name)} for name in ['manifest.json', 'bank.jsonl', 'observations.jsonl', 'summary.json'])
    if pending and not partial: raise ValueError('Pending: ' + ', '.join(pending))
    output = {'run_id': MASTER, 'complete': not pending, 'pending': pending, 'models': models, 'sources': sources,
        'interpretation': 'Prospective fresh facts, original stance prompt and unchanged control thresholds. Both splits/all models reported. Repeated presentations are not independent facts. Arithmetic and frozen retention remain separate. New qualified ethical comparisons require a new protocol and full100belief runs with their own BASE.'}
    result.mkdir(parents=True, exist_ok=True); dest = result / ('progress.json' if partial else 'analysis.json')
    if not partial and dest.exists(): raise FileExistsError('Completed scope analysis exists')
    temp = dest.with_suffix('.tmp'); temp.write_text(json.dumps(output, indent=2) + '\n'); temp.replace(dest)
    dest.with_suffix('.md').write_text('# Scoped-comprehension controls\n\n```json\n' + json.dumps(output, indent=2) + '\n```\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'sources'}, indent=2)); return output
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--allow-partial', action='store_true'); args = parser.parse_args(); analyze(partial=args.allow_partial)
