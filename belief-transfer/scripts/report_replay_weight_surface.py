"""Descriptive full100 surfaces; invalid replies remain explicit bounds, not neutral."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from statistics import mean
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from prepare_replay_weight_ablation import MASTER, read, rows, sha, write_json, write_rows
from analyze_replay_weight_ablation import original_surface_status
from analyze_ethical_four_arm import BASE


def profile(bank: list[dict], observations: list[dict]) -> dict:
    if Counter(r['presentation_id'] for r in bank) != Counter(r['presentation_id'] for r in observations):
        raise ValueError('Every frozen presentation must be recorded exactly once')
    result = {}
    for belief in sorted({r['belief_id'] for r in bank}):
        expected = [r for r in bank if r['belief_id'] == belief]
        observed = [r for r in observations if r['belief_id'] == belief]
        if len(expected) != 24 or len({r['role'] for r in expected}) != 1:
            raise ValueError('Changed full100presentation grid or role')
        n = sum(r['answer'] in ('agree', 'disagree') for r in observed)
        k = sum(r['answer'] == ('agree' if r['polarity'] == 'positive' else 'disagree') for r in observed)
        result[belief] = {'role': expected[0]['role'], 'expected': 24, 'valid': n,
            'canonical_support_count': k, 'support': k / 24 if n == 24 else None,
            'support_bounds': [k / 24, (k + 24 - n) / 24]}
    return result


def main() -> None:
    parent = Path('data/results/ethical_stance_sft') / MASTER
    review = read(parent / 'reviewed_comparison_v1.json')
    if review['full_response_review_complete'] is not True or not (parent / 'TERMINAL').exists():
        raise ValueError('Review both terminal models first')
    out = parent / 'full100_comparison.json'
    if out.exists() or (parent / 'full100_per_belief.jsonl').exists():
        raise FileExistsError('Full100descriptive report already recorded')
    root = Path('data/results/ethical_pilot')
    before = {seed: read(root / run / 'measurement_summary.json') for seed, run in BASE.items()}
    base = before[42]
    base_bank = root / BASE[42] / 'stance_bank.jsonl'
    bank = rows(base_bank)
    raw_base = root / BASE[42] / 'stance_observations.jsonl'
    bp = profile(bank, rows(raw_base))
    sources = {str(base_bank): sha(base_bank), str(raw_base): sha(raw_base)}
    output = []; models = {}
    for arm in ('norm1', 'weight32'):
        status = read(parent / (arm + '_measurement_status.json'))
        folder = root / status['stance_run_id']
        audited = original_surface_status(folder)
        summary = read(folder / 'measurement_summary.json')
        if any(summary[k] != base[k] for k in ('version', 'extractor_version', 'measurement_bank_sha', 'decoding', 'backend', 'model')):
            raise ValueError('Different BASE/candidate measurement identity')
        if sha(folder / 'stance_bank.jsonl') != sha(base_bank):
            raise ValueError('Full100bank text differs')
        current = profile(bank, rows(folder / 'stance_observations.jsonl'))
        for belief, value in current.items():
            score = summary['measurements']['stance'][belief]['neutral']
            if score['support'] != value['support'] or score['diagnostics']['n_extracted'] != value['valid']:
                raise ValueError('Raw support/counts disagree with frozen score')
            b = bp[belief]['support']
            assert b is not None
            output.append({'arm': arm, 'belief_id': belief, **value, 'base_support': b,
                'drift': value['support'] - b if value['support'] is not None else None,
                'drift_bounds': [x - b for x in value['support_bounds']],
                'base_seed_support': {str(seed): before[seed]['measurements']['stance'][belief]['neutral']['support'] for seed in before},
                'order_agreement': score['order_consistency'], 'wording_agreement': score['paraphrase_consistency'],
                'negation': {k: score[k] for k in ('n_expected_negation_pairs', 'n_eligible_negation_pairs', 'n_contradictions')},
                'polarity_profile': score['polarity_profile'], 'qualified': False,
                'source_path': str(folder / 'measurement_summary.json'), 'source_sha256': sha(folder / 'measurement_summary.json')})
        models[arm] = {'coverage': audited, 'development_validation': status, 'groups': {}}
        for role in ('all', 'ethical', 'offtopic'):
            selected = [r for r in output if r['arm'] == arm and (role == 'all' or r['role'] == role)]
            if not selected:
                raise ValueError('Empty declared role')
            complete = all(r['support'] is not None for r in selected)
            ids = [r['belief_id'] for r in selected]
            group = {'beliefs': len(selected), 'valid': sum(r['valid'] for r in selected),
                'expected': 24 * len(selected), 'mean_support': mean(r['support'] for r in selected) if complete else None,
                'mean_drift_pp': 100 * mean(r['drift'] for r in selected) if complete else None,
                'mean_support_bounds': [mean(r['support_bounds'][i] for r in selected) for i in (0, 1)],
                'mean_drift_bounds_pp': [100 * mean(r['drift_bounds'][i] for r in selected) for i in (0, 1)],
                'base_repeat_mean_support': {str(seed): mean(before[seed]['measurements']['stance'][b]['neutral']['support'] for b in ids) for seed in before}}
            for field in ('order_agreement', 'wording_agreement'):
                eligible = sum(r[field]['n_eligible_pairs'] for r in selected)
                group[field] = {'expected_pairs': sum(r[field]['n_expected_pairs'] for r in selected),
                    'eligible_pairs': eligible, 'agreement_over_eligible': sum(r[field]['n_agreeing_pairs'] for r in selected) / eligible if eligible else None}
            eligible = sum(r['negation']['n_eligible_negation_pairs'] for r in selected)
            group['negation_agreement'] = {'expected_pairs': sum(r['negation']['n_expected_negation_pairs'] for r in selected),
                'eligible_pairs': eligible, 'agreement_over_eligible': 1 - sum(r['negation']['n_contradictions'] for r in selected) / eligible if eligible else None}
            models[arm]['groups'][role] = group
        for name in ('measurement_summary.json', 'stance_bank.jsonl', 'stance_observations.jsonl', 'stance_controls.jsonl'):
            sources[str(folder / name)] = sha(folder / name)
    for seed, run in BASE.items():
        path = root / run / 'measurement_summary.json'; sources[str(path)] = sha(path)
    write_rows(parent / 'full100_per_belief.jsonl', output)
    write_json(out, {'models': models, 'sources': sources,
        'interpretation': 'Descriptive same-seed frozen Stance Score; not accuracy/confidence/forgetting. Bothmodelsunqualified. Missing final stays missing; bounds cover possible missing answers, not sampling uncertainty. BASE3-seed means are sampling context, not training replication or a confidence interval. No ethical-outcome selection; one trainingseed per new recipe.'})
    print({arm: model['groups']['all']['mean_drift_bounds_pp'] for arm, model in models.items()})


if __name__ == '__main__':
    main()
