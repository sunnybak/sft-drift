"""Collect/verify independent replay-weight retention, without changing frozen scores."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.instruction_retention import assess
from belief_transfer.evals.retention_value import assess_value, VERSION
from belief_transfer.metrics.instruction_retention import FAMILIES, report
from prepare_replay_weight_ablation import (
    MASTER, CONFIRMATION, ARMS, OLD, MODELS, read, rows, sha, train_id,
    retention_id, write_json, write_rows,
)
from validate_registry_calibration import training_binding, verify_binding

PYTHON = '/workspace/sft-drift-vllm/.venv/bin/python'


def check_bindings(bindings: dict) -> None:
    for name, digest in bindings.items():
        if sha(Path(name)) != digest:
            raise ValueError('Confirmation source/input changed: ' + name)


def value_known(values: list[dict]) -> list[dict]:
    selected = [{k: r[k] for k in ('example_id', 'family', 'thinking', 'response_sha256')}
                for r in values if r['eval_seed'] == 42 and r['value']['value_correct'] is True]
    if len({r['example_id'] for r in selected}) != len(selected):
        raise ValueError('Duplicate BASE value reference')
    for mode in (True, False):
        group = [r for r in selected if r['thinking'] == mode]
        if len(group) < 32 or {r['family'] for r in group} != set(FAMILIES):
            raise ValueError('Independent BASE value reference insufficient; no training')
    return selected


def summarize(values: list[dict], reference: list[dict], known: list[dict]) -> dict:
    expected = {(r['example_id'], r['eval_seed']): r for r in reference}
    actual = {(r['example_id'], r['eval_seed']): r for r in values}
    if len(actual) != len(values) or actual.keys() != expected.keys():
        raise ValueError('Value comparison coverage mismatch')
    by_mode_seed = {}
    for mode in (True, False):
        ids = {r['example_id'] for r in known if r['thinking'] == mode}
        if len(ids) < 32 or {r['family'] for r in known if r['thinking'] == mode} != set(FAMILIES):
            raise ValueError('Invalid value cohort')
        for seed in (42, 7, 1729):
            full = [r for r in values if r['thinking'] == mode and r['eval_seed'] == seed]
            selected = [r for r in full if r['example_id'] in ids]
            base = [expected[r['example_id'], seed] for r in selected]
            full_counts = {'correct': sum(r['value']['value_correct'] is True for r in full),
                'wrong': sum(r['value']['value_correct'] is False for r in full),
                'unscorable': sum(r['value']['value_correct'] is None for r in full)}
            correct = sum(r['value']['value_correct'] is True for r in selected)
            strict = sum(r['frozen_assessment']['strict_format'] for r in selected)
            base_strict = sum(r['frozen_assessment']['strict_format'] for r in base)
            loss = [r['example_id'] for r in selected if r['value']['value_correct'] is not True]
            complete = all(r['frozen_assessment']['normal_stop'] and
                r['frozen_assessment']['response_boundaries_valid'] for r in full)
            # Integer comparisons avoid a floating threshold changing a boundary verdict.
            passed = correct * 100 >= 95 * len(ids) and (base_strict - strict) * 100 <= 5 * len(ids) and complete
            by_mode_seed[f'{mode}/{seed}'] = {'full_n': len(full), 'full': full_counts,
                'known_n': len(ids), 'known_correct': correct, 'known_unscorable': sum(
                    r['value']['value_correct'] is None for r in selected),
                'known_value_retention': correct / len(ids),
                'known_strict_format': strict, 'base_known_strict_format': base_strict,
                'strict_format_delta_pp': 100 * (strict - base_strict) / len(ids),
                'complete_boundaries_and_stops': complete, 'known_losses_or_unscorable': loss,
                'full_gains_vs_same_seed_base': [r['example_id'] for r in full
                    if r['value']['value_correct'] is True and expected[r['example_id'], seed]['value']['value_correct'] is not True],
                'full_losses_vs_same_seed_base': [r['example_id'] for r in full
                    if r['value']['value_correct'] is not True and expected[r['example_id'], seed]['value']['value_correct'] is True],
                'passed': passed}
    return {'by_mode_seed': by_mode_seed, 'passed': all(v['passed'] for v in by_mode_seed.values()),
        'criteria': '>=95% BASE-seed42 value retention each mode/seed; <=5pp strict-format deficit on same cohort versus matched BASE seed; all128/mode-pair replies complete and valid',
        'interpretation': 'Fresh-input confirmation in reused task families, not broad capability validation. Greedy seeds are runtime repeats. Frozen original grades remain separate.'}


def inspect(model: str, protocol: dict, source_commit: str, tokenizer) -> tuple[list[dict], dict]:
    root = Path('data/results/ethical_pilot') / retention_id(model)
    if not (root / 'COMPLETED').is_file():
        raise ValueError('Incomplete confirmation model: ' + model)
    bank_path = Path('data/generated/ethical_pilot') / CONFIRMATION / 'bank.jsonl'
    bank_rows = rows(bank_path)
    observed = rows(root / 'responses.jsonl')
    manifest = read(root / 'manifest.json')
    job = load_job(['+run=' + retention_id(model)])
    runtime = protocol['runtime_reference']
    if not source_commit.startswith(manifest['code_revision']):
        raise ValueError('Confirmation source commit changed')
    for key in ('model', 'backend', 'generation', 'decoding', 'max_new_tokens', 'batch_size', 'versions'):
        if manifest[key] != runtime[key]:
            raise ValueError('Confirmation runtime differs: ' + key)
    if manifest['adapter_sha256'] != job.instruction_retention.adapter_sha256:
        raise ValueError('Wrong confirmation adapter')
    expected = {(r['example_id'], seed) for r in bank_rows for seed in (42, 7, 1729)}
    if Counter((r['example_id'], r['eval_seed']) for r in observed) != Counter(expected):
        raise ValueError('Incomplete/duplicate confirmation grid')
    if sha(root / 'bank.jsonl') != protocol['bank_sha256']:
        raise ValueError('Copied confirmation bank changed')
    bank_lookup = {r['example_id']: r for r in bank_rows}
    values = []
    for row in observed:
        if any(row.get(k) != v for k, v in bank_lookup[row['example_id']].items()):
            raise ValueError('Confirmation row identity differs from bank')
        meta = row['generation_metadata']; tokens = meta.get('output_token_ids', [])
        normal = bool(tokens) and tokens[-1] == protocol['eos_token_id'] and meta.get('finish_reason') == 'stop' and not meta.get('backend_error')
        if (row.get('error') or meta.get('backend_error')
            or meta.get('model_revision') != runtime['generation']['revision']
            or meta.get('adapter_lora_id') != (None if model == 'base' else 1)
            or meta.get('input_token_ids') != row['expected_input_token_ids']
            or meta.get('sampling_seed') != (row['seed'] ^ 42 ^ row['eval_seed']) & 0xffffffff
            or meta.get('generation_tokens') != len(tokens)
            or meta.get('execution') != runtime['generation'] or meta.get('execution_versions') != runtime['versions']):
            raise ValueError('Unverified confirmation runtime/token identity; stop without training')
        raw = tokenizer.decode(tokens[:-1] if normal else tokens, skip_special_tokens=False)
        if raw != row['response'] or row['response_sha256'] != __import__('hashlib').sha256(raw.encode()).hexdigest():
            raise ValueError('Raw response does not reconstruct from tokens')
        frozen = assess(raw, row, normal_stop=normal)
        if frozen != row['assessment']:
            raise ValueError('Frozen confirmation grade changed')
        values.append({k: row[k] for k in ('example_id', 'question_id', 'family', 'thinking', 'eval_seed', 'response_sha256')}
            | {'frozen_assessment': frozen, 'value': assess_value(raw, row, normal_stop=normal)})
    # Verify original summary/mask too; never reinterpret its grade or reference rule.
    known = rows(root / 'known_items.jsonl')
    if model == 'base':
        _, rebuilt = report([r for r in observed if r['eval_seed'] == 42], bank_rows)
        if rebuilt != known:
            raise ValueError('Frozen strict BASE mask changed')
    elif known != rows(Path('data/results/ethical_pilot') / retention_id('base') / 'known_items.jsonl'):
        raise ValueError('Frozen strict mask changed between models')
    summary = read(root / 'summary.json')
    for seed in (42, 7, 1729):
        if report([r for r in observed if r['eval_seed'] == seed], bank_rows, known)[0] != summary['by_seed'][str(seed)]:
            raise ValueError('Frozen confirmation summary does not reconstruct')
    return values, summary


def run_model(model: str, protocol: dict, output: Path, source_commit: str, tokenizer) -> None:
    import yaml
    check_bindings(protocol['source_bindings'])
    target = Path('data/results/ethical_pilot') / retention_id(model)
    value_path = output / (model + '_values.jsonl')
    if target.exists() or value_path.exists():
        raise FileExistsError('Started confirmation model cannot resume/overwrite')
    if model != 'base':
        config = Path('configs/run') / (retention_id(model) + '.yaml')
        if config.exists():
            raise FileExistsError('Confirmation adapter config already exists')
        mask = Path('data/results/ethical_pilot') / retention_id('base') / 'known_items.jsonl'
        adapter = Path('data/checkpoints/ethical_stance_sft') / (OLD if model == 'historical_c4' else train_id(model)) / 'final'
        if model in ARMS:
            plan = read(Path('data/generated/ethical_stance_sft') / train_id(model) / 'plan.json')
            binding = training_binding(plan, Path('data/results/ethical_stance_sft') / train_id(model), adapter)
            verify_binding(binding)
            write_json(output / (model + '_training_binding.json'), binding)
        bank_path = Path('data/generated/ethical_pilot') / CONFIRMATION / 'bank.jsonl'
        config.write_text('# @package _global_\n' + yaml.safe_dump({'defaults': ['ethics_gpu_retention_rca_base_v2'],
            'run_id': retention_id(model), 'pilot_bench': {'adapter_path': str(adapter)},
            'instruction_retention': {'model_label': model, 'bank_path': str(bank_path),
                'bank_sha256': sha(bank_path), 'known_path': str(mask), 'known_sha256': sha(mask),
                'fresh_base_reference': False, 'adapter_sha256': sha(adapter / 'adapter_model.safetensors'),
                'eval_seeds': [42, 7, 1729]}}, sort_keys=False))
    job = load_job(['+run=' + retention_id(model)])
    if model == 'base' and config_sha(job) != protocol['base_config_sha']:
        raise ValueError('BASE confirmation config changed')
    event = {'model': model, 'config_sha': config_sha(job), 'adapter_sha256': job.instruction_retention.adapter_sha256}
    write_json(output / (model + '_dispatch.json'), event)
    command = ['flock', '/tmp/sft-drift-cuda-benchmark.lock', PYTHON, '-u', 'run.py', '+run=' + retention_id(model)]
    operation = subprocess.run(command, check=False)
    write_json(output / (model + '_operation.json'), {'command': command, 'returncode': operation.returncode})
    if operation.returncode:
        raise RuntimeError('Confirmation child failed: ' + model)
    values, _ = inspect(model, protocol, source_commit, tokenizer)
    write_rows(value_path, values)
    if model == 'base':
        known = value_known(values)
        write_rows(output / 'value_known_items.jsonl', known)
        write_json(output / 'value_reference_freeze.json', {'selection_seed': 42, 'assessment_version': VERSION,
            'mask_sha256': sha(output / 'value_known_items.jsonl'), 'base_values_sha256': sha(value_path),
            'base_responses_sha256': sha(target / 'responses.jsonl'),
            'counts': {str(mode): sum(r['thinking'] == mode for r in known) for mode in (True, False)},
            'selection': 'Correct recognized value with valid boundaries and normal stop; no answer-only format filter.'})
    reference = rows(output / 'base_values.jsonl')
    known = rows(output / 'value_known_items.jsonl')
    write_json(output / (model + '_assessment.json'), summarize(values, reference, known))
    observed = rows(target / 'responses.jsonl')
    value_lookup = {(r['example_id'], r['eval_seed']): r for r in values}
    failures = [{'model': model, 'observation': r, 'value': value_lookup[r['example_id'], r['eval_seed']]['value']}
                for r in observed if not r['assessment']['admissible'] or
                value_lookup[r['example_id'], r['eval_seed']]['value']['value_correct'] is not True]
    write_rows(output / (model + '_review_queue.jsonl'), failures)


def main() -> None:
    from transformers import AutoTokenizer
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['reference', *ARMS])
    args = parser.parse_args()
    protocol = read(Path('data/generated/ethical_stance_sft') / MASTER / 'protocol.json')
    check_bindings(protocol['source_bindings'])
    output = Path('data/results/ethical_pilot') / CONFIRMATION
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    execution_path = Path('data/generated/ethical_stance_sft') / MASTER / 'execution.json'
    execution = read(execution_path)
    check_bindings(execution['source_bindings'])
    receipt = read(Path('data/.handoff-receipt.json'))
    if receipt['manifest']['files'].get(str(execution_path.relative_to('data')), {}).get('sha256') != sha(execution_path):
        raise ValueError('Preserve frozen execution inputs privately before GPU collection')
    base = load_job(['+run=' + retention_id('base')])
    tokenizer = AutoTokenizer.from_pretrained(base.models.models[base.pilot_bench.model].pretrained,
        revision=base.pilot_bench.cuda_generation.revision, local_files_only=True)
    if args.operation == 'reference':
        if output.exists():
            raise FileExistsError('Reference already started; no resume')
        output.mkdir(parents=True)
        (output / 'STARTED').write_text(source_commit + '\n')
        write_json(output / 'execution.json', execution)
        try:
            run_model('base', protocol, output, source_commit, tokenizer)
            run_model('historical_c4', protocol, output, source_commit, tokenizer)
            (output / 'REFERENCE_COMPLETED').write_text('BASE value cohort frozen before any new study training. Inspect individual results.\n')
        except BaseException as exc:
            write_json(output / 'reference_failure.json', {'error': repr(exc)})
            raise
        finally:
            (output / 'REFERENCE_TERMINAL').write_text('Finite reference worker ended; no resume.\n')
    else:
        if not (output / 'REFERENCE_COMPLETED').exists():
            raise ValueError('Freeze independent BASE/historical reference before training candidates')
        # The source commit can legitimately change between independently frozen stages,
        # but all scorer, bank, runtime and loss source bytes must still match execution.
        run_model(args.operation, protocol, output, source_commit, tokenizer)


if __name__ == '__main__':
    main()
