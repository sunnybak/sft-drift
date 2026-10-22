"""Audit the sole training factor and matched outcomes; never selects on stance."""
from __future__ import annotations

import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from prepare_lower_lr_probe import MASTER, TRAIN, CONTROL, retention_id, verify_single_training_change
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_lower_lr_probe import inspect_retention, summarize
from belief_transfer.config import load_job
from analyze_replay_weight_ablation import original_surface_status


def lr_trace_check(before: list[dict], after: list[dict], *, expected_steps: int = 454) -> dict:
    a = [r for r in before if 'learning_rate' in r]
    b = [r for r in after if 'learning_rate' in r]
    expected = list(range(1, expected_steps + 1))
    grid = [r['step'] for r in a] == expected and [r['step'] for r in b] == expected
    differences = []
    if grid:
        for x, y in zip(a, b, strict=True):
            if not math.isfinite(x['learning_rate']) or x['learning_rate'] < 0 or not math.isfinite(y['learning_rate']) or y['learning_rate'] < 0 or not math.isclose(y['learning_rate'], x['learning_rate'] / 4, rel_tol=1e-12, abs_tol=1e-15):
                differences.append({'step': x['step'], 'norm1_lr': x['learning_rate'], 'candidate_lr': y['learning_rate']})
    return {'passed': grid and not differences, 'exact_step_grid': grid,
        'expected_steps': expected_steps, 'observed_rows': {'norm1': len(a), 'candidate': len(b)},
        'differences': differences, 'expected_ratio': .25,
        'observed_peak_norm1': max((r['learning_rate'] for r in a), default=None),
        'observed_peak_candidate': max((r['learning_rate'] for r in b), default=None)}


def factor_audit(before: dict, after: dict, before_batches: list[dict], after_batches: list[dict],
                 *, manifest_equal: bool, tokenized_equal: bool, scientific_config_equal: bool,
                 expected_steps: int = 454) -> dict:
    trace = lr_trace_check(before['log_history'], after['log_history'], expected_steps=expected_steps)
    initial_a = before.get('initial_adapter_sha256'); initial_b = after.get('initial_adapter_sha256')
    engineering = after.get('checks', {})
    checks = {'scientific_config_only_LR': scientific_config_equal,
        'initial_adapter_identical': bool(initial_a) and initial_a == initial_b,
        'model_revision_identical': bool(before.get('model_revision')) and before.get('model_revision') == after.get('model_revision'),
        'manifest_bytes_identical': manifest_equal, 'actual_tokenized_bytes_identical': tokenized_equal,
        'actual_forward_batches_identical': bool(before_batches) and before_batches == after_batches,
        'fourfold_LR_at_every_step': trace['passed'],
        'actual_step_count_matches': before.get('global_steps') == after.get('global_steps') == expected_steps,
        'actual_microbatch_count_expected': len(before_batches) == len(after_batches) == 2 * expected_steps,
        'actual_peak_LRs_match_plan': trace['observed_peak_norm1'] == 1e-4 and trace['observed_peak_candidate'] == 2.5e-5,
        'engineering_checks_pass': len(engineering) == 12 and all(v is True for v in engineering.values()),
        'raw_target_count_identical': before.get('actual_forward_loss_tokens') is not None and before.get('actual_forward_loss_tokens') == after.get('actual_forward_loss_tokens'),
        'weighted_objective_identical': bool(before.get('weighted_objective')) and before.get('weighted_objective') == after.get('weighted_objective')}
    return {'passed': all(checks.values()), 'checks': checks, 'LR_trace': trace,
        'initial_adapter_sha256': {'norm1': initial_a, 'candidate': initial_b},
        'forward_batches': {'norm1': len(before_batches), 'candidate': len(after_batches)},
        'interpretation': 'Failed comparability checks invalidate sole-factor attribution, not the existence of recorded replies. Keep failures; no automatic retraining or parameter selection.'}


def paired_retention(control: list[dict], candidate: list[dict], known: list[dict]) -> tuple[dict, list[dict]]:
    a = {(r['example_id'], r['eval_seed']): r for r in control}
    b = {(r['example_id'], r['eval_seed']): r for r in candidate}
    cohort = {r['example_id']: r for r in known}
    if len(a) != 384 or len(a) != len(control) or len(b) != len(candidate) or a.keys() != b.keys() or len(cohort) != len(known):
        raise ValueError('Missing/duplicate/different paired reference grid')
    if not cohort.keys() <= {r['example_id'] for r in control}:
        raise ValueError('Foreign BASE cohort')
    output = []
    for key, x in a.items():
        y = b[key]
        if any(x[k] != y[k] for k in ('family', 'thinking')):
            raise ValueError('Paired family/mode differs')
        if x['example_id'] in cohort and any(x[k] != cohort[x['example_id']][k] for k in ('family', 'thinking')):
            raise ValueError('BASE cohort family/mode differs')
        old, new = x['value']['value_correct'], y['value']['value_correct']
        if any(v is not None and type(v) is not bool for v in (old, new)):
            raise ValueError('Task values must be bool or explicitly unscorable')
        output.append({'example_id': key[0], 'eval_seed': key[1], 'family': x['family'],
            'thinking': x['thinking'], 'base_known': x['example_id'] in cohort,
            'norm1_correct': old, 'candidate_correct': new,
            'value_gain': old is False and new is True, 'value_loss': old is True and new is False,
            'unscorable_transition': old is None or new is None,
            'norm1_response_sha256': x['response_sha256'], 'candidate_response_sha256': y['response_sha256']})
    groups = {}
    for mode in (True, False):
        for seed in (42, 7, 1729):
            full = [r for r in output if r['thinking'] == mode and r['eval_seed'] == seed]
            if len(full) != 64:
                raise ValueError('Require complete64-question mode/seed grid')
            for scope in ('full', 'base_known'):
                selected = full if scope == 'full' else [r for r in full if r['base_known']]
                if not selected:
                    raise ValueError('Empty paired cohort')
                old_n = sum(r['norm1_correct'] is True for r in selected)
                new_n = sum(r['candidate_correct'] is True for r in selected)
                unknown = {model: sum(r[field] is None for r in selected) for model, field in
                    [('norm1', 'norm1_correct'), ('candidate', 'candidate_correct')]}
                groups[f'{mode}/{seed}/{scope}'] = {'expected': len(selected),
                    'norm1_correct': old_n, 'candidate_correct': new_n, 'unscorable': unknown,
                    'recognized_correct_delta_pp': 100 * (new_n - old_n) / len(selected),
                    'value_accuracy_delta_pp': None if any(unknown.values()) else 100 * (new_n - old_n) / len(selected),
                    'gains': [r['example_id'] for r in selected if r['value_gain']],
                    'losses': [r['example_id'] for r in selected if r['value_loss']],
                    'unscorable_transitions': [r['example_id'] for r in selected if r['unscorable_transition']]}
    return groups, output


def main() -> None:
    from transformers import AutoTokenizer
    parent = Path('data/results/ethical_stance_sft') / MASTER
    if not (parent / 'COLLECTION_COMPLETED').is_file() or not (parent / 'CANDIDATE_TERMINAL').is_file():
        raise ValueError('Fixed candidate worker must finish before final comparison')
    if (parent / 'comparison_v1.json').exists() or (parent / 'paired_retention_v1.jsonl').exists():
        raise FileExistsError('Comparison is immutable')
    protocol = read(Path('data/generated/ethical_stance_sft') / MASTER / 'protocol.json')
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'], revision=runtime['generation']['revision'], local_files_only=True)
    known = rows(parent / 'value_known_items.jsonl'); freeze = read(parent / 'value_reference_freeze.json')
    if sha(parent / 'value_known_items.jsonl') != freeze['mask_sha256'] or sha(parent / 'base_values.jsonl') != freeze['base_values_sha256']:
        raise ValueError('BASE reference changed')
    values = {}; models = {}; sources = {}
    for model in ('base', 'norm1', 'candidate'):
        value, old = inspect_retention(model, protocol, tokenizer)
        if value != rows(parent / (model + '_values.jsonl')):
            raise ValueError('Saved task values changed')
        assessment = summarize(value, rows(parent / 'base_values.jsonl'), known)
        if assessment != read(parent / (model + '_assessment.json')):
            raise ValueError('Acceptance changed')
        values[model] = value; models[model] = {'value_retention': assessment, 'original_strict_retention': old}
        for path in (parent / (model + '_values.jsonl'), parent / (model + '_assessment.json'),
                     Path('data/results/ethical_pilot') / retention_id(model) / 'responses.jsonl'):
            sources[str(path)] = sha(path)
    before = Path('data/results/ethical_stance_sft') / CONTROL
    after = Path('data/results/ethical_stance_sft') / TRAIN
    a = read(before / 'summary.json')['training']; b = read(after / 'summary.json')['training']
    try:
        verify_single_training_change(load_job(['+run=' + CONTROL]), load_job(['+run=' + TRAIN])); config_ok = True
    except ValueError:
        config_ok = False
    batch_paths = [Path('data/checkpoints/ethical_stance_sft') / run / 'training_batches.jsonl' for run in (CONTROL, TRAIN)]
    manifest_paths = [Path('data/generated/ethical_stance_sft') / run / 'documents.jsonl' for run in (CONTROL, TRAIN)]
    audit = factor_audit(a, b, rows(batch_paths[0]), rows(batch_paths[1]), manifest_equal=sha(manifest_paths[0]) == sha(manifest_paths[1]),
        tokenized_equal=sha(before / 'tokenized.jsonl') == sha(after / 'tokenized.jsonl'), scientific_config_equal=config_ok)
    for path in (*batch_paths, *manifest_paths, before / 'summary.json', after / 'summary.json', before / 'tokenized.jsonl', after / 'tokenized.jsonl'):
        sources[str(path)] = sha(path)
    groups, pairs = paired_retention(values['norm1'], values['candidate'], known)
    status = read(parent / 'candidate_measurement_status.json')
    surface = original_surface_status(Path('data/results/ethical_pilot') / status['stance_run_id'])
    write_rows(parent / 'paired_retention_v1.jsonl', pairs)
    write_json(parent / 'comparison_v1.json', {'factor_audit': audit, 'retention_models': models,
        'matched_candidate_minus_norm1': groups, 'candidate_full100': surface,
        'candidate_qualification': status, 'sources': sources,
        'agent_candidate_review': 'pending; mechanical output is not reviewed recipe qualification',
        'interpretation': 'One fixed LR/one trainingseed. Full reference norm1hadzero knownnonthinkinglosses here, so a shared pass does not show a nonthinkingrepair. ThinkingBASEalso has one sampled error. Retain all gains/losses/unknowns; failed checks not neutralized. No ethical-outcome parameter or checkpoint selection, automatic retry or scale-up.'})
    print('Mechanical lower-LR comparison saved; full candidate failure review still required.')


if __name__ == '__main__':
    main()
