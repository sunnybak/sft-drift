"""Reconstruct the fixed candidate's evidence; no automatic recipe adoption."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import load_job
from belief_transfer.inference.model import _apply_chat_template
from belief_transfer.metrics.measurements import request_sampling_seed
from belief_transfer.stages.measurements import observed_backend_reply
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from prepare_replay_value_probe import MASTER, TRAIN, OLD_TRAIN, reference_root, candidate_id, same_recipe
import run_replay_coverage_probe as previous
from run_replay_value_probe import supplement


def paired_values(control: list[dict], candidate: list[dict], known: list[dict], *, kind: str) -> tuple[dict, list[dict]]:
    count = {'retention': 128, 'decisions': 64}[kind]
    a = {r['example_id']: r for r in control}
    b = {r['example_id']: r for r in candidate}
    ids = {r['example_id'] for r in known}
    if (len(a) != len(control) or len(b) != len(candidate) or len(a) != count or
            a.keys() != b.keys() or len(ids) != len(known) or not ids <= a.keys()):
        raise ValueError('Missing/duplicate/foreign paired grid or known mask')
    field = 'value' if kind == 'retention' else 'assessment'
    family = 'family' if kind == 'retention' else 'operation'
    output = []
    for identity, x in a.items():
        y = b[identity]
        if (x['thinking'], x[family]) != (y['thinking'], y[family]):
            raise ValueError('Changed mode/family in paired comparison')
        old, new = x[field]['value_correct'], y[field]['value_correct']
        if any(v is not None and type(v) is not bool for v in (old, new)):
            raise ValueError('Value must be bool or explicitly unscorable')
        output.append({'example_id': identity, 'thinking': x['thinking'], 'family': x[family],
            'base_known': identity in ids, 'control_correct': old, 'candidate_correct': new,
            'gain': old is False and new is True, 'loss': old is True and new is False,
            'unscorable_transition': old is None or new is None,
            'control_response_sha256': x['response_sha256'], 'candidate_response_sha256': y['response_sha256']})
    summary = {}
    for mode in (True, False):
        group = [r for r in output if r['thinking'] == mode]
        if len(group) != count // 2:
            raise ValueError('Incomplete mode grid')
        for scope in ('full', 'base_known'):
            selected = group if scope == 'full' else [r for r in group if r['base_known']]
            if not selected:
                raise ValueError('Empty paired cohort')
            old = sum(r['control_correct'] is True for r in selected)
            new = sum(r['candidate_correct'] is True for r in selected)
            missing_old = sum(r['control_correct'] is None for r in selected)
            missing_new = sum(r['candidate_correct'] is None for r in selected)
            n = len(selected)
            summary[f'{mode}/{scope}'] = {'n': n, 'control_correct': old, 'candidate_correct': new,
                'control_unscorable': missing_old, 'candidate_unscorable': missing_new,
                'accuracy_difference_pp': None if missing_old or missing_new else 100 * (new-old) / n,
                'difference_missing_bounds_pp': [100*(new-old-missing_old)/n, 100*(new+missing_new-old)/n],
                'gains': [r['example_id'] for r in selected if r['gain']],
                'losses': [r['example_id'] for r in selected if r['loss']],
                'unscorable_transitions': [r['example_id'] for r in selected if r['unscorable_transition']]}
    return summary, output


def audit_surface(folder: Path, spec, tokenizer, runtime: dict) -> dict:
    """Verify each actual request, token output, seed and frozen observation."""
    failures, n, stops = [], 0, Counter()
    for bank_name, observed_name in (('stance_bank', 'stance_observations'), ('stance_control_bank', 'stance_controls')):
        bank = {r['presentation_id']: r for r in rows(folder / (bank_name + '.jsonl'))}
        observed = rows(folder / (observed_name + '.jsonl'))
        if Counter(r['presentation_id'] for r in observed) != Counter(bank.keys()):
            raise ValueError('Surface request coverage differs from expected grid')
        for r in observed:
            n += 1
            identity = r['presentation_id']; source = bank[identity]
            metadata = r.get('generation_metadata') or {}
            expected_input = tokenizer.encode(_apply_chat_template(tokenizer,
                [{'role': 'user', 'content': source['prompt']}], enable_thinking=spec.measurement_decoding.thinking),
                add_special_tokens=False)
            seed = request_sampling_seed(source, spec.seed)
            tokens = metadata.get('output_token_ids', [])
            stops[metadata.get('finish_reason', 'missing')] += 1
            if (metadata.get('input_token_ids') != expected_input or metadata.get('sampling_seed') != seed
                    or metadata.get('model_revision') != spec.cuda_generation.revision
                    or metadata.get('adapter_lora_id') != 1 or metadata.get('execution') != spec.cuda_generation.model_dump()
                    or metadata.get('execution_versions') != runtime['versions'] or not tokens
                    or metadata.get('generation_tokens') != len(tokens) or metadata.get('prompt_tokens') != len(expected_input)):
                failures.append({'presentation_id': identity, 'error': 'UNVERIFIED_REQUEST_OR_GENERATION_METADATA'})
                continue
            text = tokenizer.decode(tokens, skip_special_tokens=True).strip()
            if observed_backend_reply(source, text, metadata, thinking=spec.measurement_decoding.thinking, seed=seed) != r:
                failures.append({'presentation_id': identity, 'error': 'SAVED_REPLY_OR_FROZEN_ASSESSMENT_MISMATCH'})
    return {'records': n, 'finish_reasons': dict(stops), 'mismatches': failures, 'passed': not failures}


def main() -> None:
    from transformers import AutoTokenizer
    parent = Path('data/results/ethical_stance_sft') / MASTER
    if not (parent / 'COLLECTION_COMPLETED').is_file() or not (parent / 'TERMINAL').is_file():
        raise ValueError('Wait for the fixed worker to finish all measurements')
    names = ['comparison_v1.json', 'paired_retention_v1.jsonl', 'paired_decisions_value_v2.jsonl', 'surface_token_audit_v1.json']
    if any((parent / n).exists() for n in names):
        raise FileExistsError('Comparison already started; no overwrite')
    protocol = read(Path('data/generated/ethical_stance_sft') / MASTER / 'protocol.json')
    previous.check_bindings(protocol['source_bindings'])
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    binding = previous.verify_candidate(protocol, tokenizer, train_id=TRAIN)
    models, comparisons, paired = {}, {}, {}
    ref = reference_root()
    for kind in ('retention', 'decisions'):
        by_model = {}
        known = rows(ref / ('retention_known_items.jsonl' if kind == 'retention' else 'decisions_value_known_items_v2.jsonl'))
        for model in ('base', 'control', 'candidate'):
            output = parent if model == 'candidate' else ref
            native = previous.inspect(model, kind, protocol, tokenizer, parent=output,
                name=candidate_id(kind) if model == 'candidate' else None)
            if native != rows(output / f'{model}_{kind}_values.jsonl'):
                raise ValueError('Saved native values differ from reconstructed observations')
            value = native if kind == 'retention' else supplement(native)
            if kind == 'decisions' and value != rows(output / f'{model}_decisions_value_v2.jsonl'):
                raise ValueError('Saved value-v2 differs from raw replies')
            by_model[model] = value
        for model, value in by_model.items():
            result = (previous.summarize_values(value, by_model['base'], known) if kind == 'retention'
                      else previous.compare_decisions(value, by_model['base'], known))
            if model == 'candidate':
                expected = result if kind == 'retention' else result | {'assessment_version': 'neutral-task-value-v2'}
                if expected != read(parent / f'candidate_{kind}_assessment.json'):
                    raise ValueError('Frozen candidate assessment differs')
            models.setdefault(model, {})[kind] = result
        comparisons[kind], paired[kind] = paired_values(by_model['control'], by_model['candidate'], known, kind=kind)
    train = read(Path('data/results/ethical_stance_sft') / TRAIN / 'summary.json')['training']
    control = read(Path('data/results/ethical_stance_sft/ethics_sft_c4_weight32_v1/summary.json'))['training']
    engineering = {'checkpoint_binding': binding,
        'same_frozen_training_recipe': same_recipe(load_job(['+run='+OLD_TRAIN]), load_job(['+run='+TRAIN])),
        'same_initial_adapter': bool(train.get('initial_adapter_sha256')) and train['initial_adapter_sha256'] == control.get('initial_adapter_sha256'),
        'same_LR_trace': [(r['step'], r['learning_rate']) for r in train['log_history'] if 'learning_rate' in r]
            == [(r['step'], r['learning_rate']) for r in control['log_history'] if 'learning_rate' in r],
        'training_checks': train['checks']}
    status = read(parent / 'candidate_measurement_status.json')
    folder = Path('data/results/ethical_pilot') / status['stance_run_id']
    surface = previous.original_surface_status(folder)
    if surface != status['actual_coverage']:
        raise ValueError('Saved full100scores/coverage differ')
    token_audit = audit_surface(folder, load_job(['+run='+status['stance_run_id']]).pilot_bench, tokenizer, runtime)
    write_rows(parent / names[1], paired['retention'])
    write_rows(parent / names[2], paired['decisions'])
    write_json(parent / names[3], token_audit)
    write_json(parent / names[0], {'models': models, 'candidate_minus_fixed_control': comparisons,
        'engineering': engineering, 'full100': surface, 'qualification': status,
        'surface_token_audit': token_audit, 'analysis_source_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'analysis_script_sha256': sha(Path(__file__)), 'full_failure_review': 'pending',
        'interpretation': 'Development investigation, one trainingseed, eight shared decision facts. No automatic adoption or expansion; preserve original failed gates and missing replies.'})
    print({'mechanical_comparison': 'saved', 'full_failure_review': 'pending', 'token_audit': token_audit})


if __name__ == '__main__':
    main()
