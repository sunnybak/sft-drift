"""Mechanical matched comparison; full-response review remains a separate requirement."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.metrics.measurements import summarize_measurement
from prepare_replay_weight_ablation import (
    MASTER, CONFIRMATION, ARMS, read, rows, sha, write_json, write_rows,
)
from run_replay_weight_confirmation import inspect, summarize


def paired_values(control: list[dict], weighted: list[dict], known: list[dict]) -> tuple[dict, list[dict]]:
    before = {(r['example_id'], r['eval_seed']): r for r in control}
    after = {(r['example_id'], r['eval_seed']): r for r in weighted}
    if len(before) != len(control) or len(after) != len(weighted) or before.keys() != after.keys():
        raise ValueError('Matched retention grids differ or duplicate observations')
    cohort = {r['example_id']: r for r in known}
    if len(cohort) != len(known):
        raise ValueError('Duplicate reference items')
    if not cohort.keys() <= {r['example_id'] for r in control}:
        raise ValueError('Reference includes an item outside the matched bank')
    pairs = []
    for key, a in before.items():
        b = after[key]
        if any(a[k] != b[k] for k in ('thinking', 'family')):
            raise ValueError('Matched item family/mode differs')
        if a['example_id'] in cohort and any(a[k] != cohort[a['example_id']][k] for k in ('thinking', 'family')):
            raise ValueError('Value cohort metadata differs')
        x, y = a['value']['value_correct'], b['value']['value_correct']
        if any(v is not None and type(v) is not bool for v in (x, y)):
            raise ValueError('Value judgment must be bool or explicitly unscorable')
        pairs.append({'example_id': key[0], 'eval_seed': key[1], 'thinking': a['thinking'],
            'family': a['family'], 'base_known': a['example_id'] in cohort,
            'norm1_correct': x, 'weight32_correct': y,
            'paired_scorable': x is not None and y is not None,
            'value_gain': x is False and y is True, 'value_loss': x is True and y is False,
            'norm1_response_sha256': a['response_sha256'], 'weight32_response_sha256': b['response_sha256']})
    result = {}
    for mode in (True, False):
        for seed in (42, 7, 1729):
            full = [r for r in pairs if r['thinking'] == mode and r['eval_seed'] == seed]
            if len(full) != 64:
                raise ValueError('Matched comparison requires full64questions per mode/seed')
            for scope in ('full', 'base_known'):
                group = full if scope == 'full' else [r for r in full if r['base_known']]
                if not group:
                    raise ValueError('Empty comparison cohort')
                a = sum(r['norm1_correct'] is True for r in group)
                b = sum(r['weight32_correct'] is True for r in group)
                unknown = {label: sum(r[key] is None for r in group)
                    for label, key in [('norm1', 'norm1_correct'), ('weight32', 'weight32_correct')]}
                result[f'{mode}/{seed}/{scope}'] = {'expected': len(group),
                    'norm1_correct': a, 'weight32_correct': b, 'unscorable': unknown,
                    'paired_scorable': sum(r['paired_scorable'] for r in group),
                    'recognized_correct_difference_pp': 100 * (b - a) / len(group),
                    'value_accuracy_difference_pp': None if any(unknown.values()) else 100 * (b - a) / len(group),
                    'gains': [r['example_id'] for r in group if r['value_gain']],
                    'losses': [r['example_id'] for r in group if r['value_loss']]}
    return result, pairs


def original_surface_status(folder: Path) -> dict:
    """A collection marker does not prove the model received the full belief grid."""
    summary = read(folder / 'measurement_summary.json')
    bank = rows(folder / 'stance_bank.jsonl')
    observed = rows(folder / 'stance_observations.jsonl')
    counts = Counter(r['belief_id'] for r in bank)
    if len(counts) != 100 or set(counts.values()) != {24}:
        raise ValueError('Changed full100expected bank')
    rebuilt = summarize_measurement(bank, observed)
    if rebuilt != summary['measurements']['stance']:
        raise ValueError('Frozen full100scores do not reconstruct')
    valid = sum(r['neutral']['diagnostics']['n_extracted'] for r in rebuilt.values())
    controls = summary['meta_eval'].get('stance_operational_qualification', {})
    code = None
    if not observed:
        code = 'CONTROL_GATE_SKIPPED_NATURAL' if controls.get('passed') is False else 'NO_NATURAL_RESPONSES'
    elif len(observed) < len(bank):
        code = 'MISSING_NATURAL_RESPONSES'
    elif valid < len(bank):
        code = 'INVALID_NATURAL_RESPONSES'
    return {'run_id': folder.name, 'expected': len(bank), 'recorded': len(observed), 'valid': valid,
        'complete': valid == len(bank), 'code': code,
        'fresh_controls': summary['meta_eval']['model_controls'],
        'operational_qualification': controls or None,
        'summary_sha256': sha(folder / 'measurement_summary.json'),
        'bank_sha256': sha(folder / 'stance_bank.jsonl'),
        'observations_sha256': sha(folder / 'stance_observations.jsonl')}


def needs_completion_followup(statuses: dict) -> bool:
    if set(statuses) != set(ARMS):
        raise ValueError('Both fixed arms are required before a matched completion decision')
    # Repair absent calls, never repeat a complete grid to improve invalid answers.
    return any(s['recorded'] < s['expected'] for s in statuses.values())


def main() -> None:
    from transformers import AutoTokenizer
    parent = Path('data/results/ethical_stance_sft') / MASTER
    if not (parent / 'COLLECTION_COMPLETED').exists() or not (parent / 'TERMINAL').exists():
        raise ValueError('Fixed worker must terminate before final mechanical comparison')
    output = parent / 'retention_comparison.json'
    if output.exists() or (parent / 'paired_retention_values.jsonl').exists():
        raise FileExistsError('Mechanical comparison already recorded')
    reference = Path('data/results/ethical_pilot') / CONFIRMATION
    protocol = read(Path('data/generated/ethical_stance_sft') / MASTER / 'protocol.json')
    tokenizer = AutoTokenizer.from_pretrained(protocol['runtime_reference']['model']['pretrained'],
        revision=protocol['runtime_reference']['generation']['revision'], local_files_only=True)
    known = rows(reference / 'value_known_items.jsonl')
    if sha(reference / 'value_known_items.jsonl') != read(reference / 'value_reference_freeze.json')['mask_sha256']:
        raise ValueError('BASE cohort changed')
    base = rows(reference / 'base_values.jsonl')
    commit = (parent / 'STARTED').read_text().strip()
    models = {}; collected = {}; surfaces = {}; sources = {}
    for arm in ARMS:
        values, frozen = inspect(arm, protocol, commit, tokenizer)
        if values != rows(reference / (arm + '_values.jsonl')):
            raise ValueError('Saved candidate values changed')
        assessment = summarize(values, base, known)
        if assessment != read(reference / (arm + '_assessment.json')):
            raise ValueError('Saved candidate acceptance changed')
        collected[arm] = values
        models[arm] = {'value_retention': assessment, 'legacy_frozen_retention': frozen,
            'engineering_binding': read(parent / (arm + '_training_binding.json'))}
        status = read(parent / (arm + '_measurement_status.json'))
        surfaces[arm] = original_surface_status(Path('data/results/ethical_pilot') / status['stance_run_id'])
        for p in (reference / (arm + '_values.jsonl'), reference / (arm + '_assessment.json'),
                  parent / (arm + '_training_binding.json'), parent / (arm + '_measurement_status.json')):
            sources[str(p)] = sha(p)
    comparison, pairs = paired_values(collected['norm1'], collected['weight32'], known)
    write_rows(parent / 'paired_retention_values.jsonl', pairs)
    write_json(output, {'run_id': MASTER, 'models': models, 'matched_weight32_minus_norm1': comparison,
        'original_full100_status': surfaces, 'sources': sources,
        'agent_full_response_review': 'pending; mechanical output is not final reviewed qualification',
        'full100_completion_followup_needed': needs_completion_followup(surfaces),
        'full100_completion_followup': 'If either original grid has absent natural calls, administer one new collect-all reading to BOTH models. Never trigger on stance, extraction success or control scores; no repeat until pass. Original attempts retained.',
        'interpretation': 'One training seed and one preset weight. Greedy eval repeats are not independent replications; correct/incorrect/unscorable stay separate. Threshold passes do not erase losses. No ethical-outcome recipe/checkpoint selection or broad preservation claim.'})
    print('Mechanical matched comparison recorded; complete full-response review and collect-all follow-up before final conclusions.')


if __name__ == '__main__':
    main()
