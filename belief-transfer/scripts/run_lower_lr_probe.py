"""Finite lower-LR reference/candidate workers; no automatic resume or tuning loop."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.instruction_retention import assess
from belief_transfer.evals.retention_value import assess_value
from belief_transfer.metrics.instruction_retention import report
from prepare_lower_lr_probe import MASTER, TRAIN, BANK, CONTROL, MODELS, retention_id, eval_id
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_replay_weight_confirmation import check_bindings, value_known, summarize
from run_ethical_four_arm import execute
from validate_registry_calibration import training_binding, verify_binding
from analyze_replay_weight_ablation import original_surface_status

TRAIN_PYTHON = '/workspace/sft-drift/belief-transfer/.venv/bin/python'
EVAL_PYTHON = '/workspace/sft-drift-vllm/.venv/bin/python'
LOCK = ['flock', '/tmp/sft-drift-cuda-benchmark.lock']


def roots() -> tuple[Path, Path]:
    return (Path('data/generated/ethical_stance_sft') / MASTER,
            Path('data/results/ethical_stance_sft') / MASTER)


def preserved(path: Path) -> None:
    receipt = read(Path('data/.handoff-receipt.json'))
    registry = read(Path('configs/handoff.json'))
    if (receipt['repo_id'] != registry['repo_id'] or
        receipt['manifest']['files'].get(str(path.relative_to('data')), {}).get('sha256') != sha(path)):
        raise ValueError('Privately preserve the exact frozen input before GPU calls: ' + str(path))


def commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()


def inspect_retention(model: str, protocol: dict, tokenizer) -> tuple[list[dict], dict]:
    """Rebuild raw token identity, original strict grades, task values and old summary."""
    _, parent = roots()
    folder = Path('data/results/ethical_pilot') / retention_id(model)
    if not (folder / 'COMPLETED').is_file():
        raise ValueError('Retention stage not complete: ' + model)
    dispatch = read(parent / (model + '_retention_dispatch.json'))
    manifest = read(folder / 'manifest.json')
    runtime = protocol['runtime_reference']
    if not dispatch['source_commit'].startswith(manifest['code_revision']):
        raise ValueError('Retention source differs from dispatch')
    job = load_job(['+run=' + retention_id(model)])
    if config_sha(job) != dispatch['config_sha'] or manifest['evaluation'] != job.instruction_retention.model_dump(mode='json'):
        raise ValueError('Retention config/evaluation changed')
    for key in ('model', 'backend', 'generation', 'decoding', 'max_new_tokens', 'batch_size', 'versions'):
        if manifest[key] != runtime[key]:
            raise ValueError('Retention runtime differs: ' + key)
    if manifest['adapter_sha256'] != dispatch['adapter_sha256']:
        raise ValueError('Retention adapter differs')
    bank = rows(Path(protocol['bank_path']))
    if sha(Path(protocol['bank_path'])) != protocol['bank_sha256'] or sha(folder / 'bank.jsonl') != protocol['bank_sha256']:
        raise ValueError('Retention bank changed')
    lookup = {r['example_id']: r for r in bank}
    actual = rows(folder / 'responses.jsonl')
    expected = {(r['example_id'], seed) for r in bank for seed in (42, 7, 1729)}
    if Counter((r['example_id'], r['eval_seed']) for r in actual) != Counter(expected):
        raise ValueError('Missing/duplicate retention grid')
    values = []
    import hashlib
    for row in actual:
        if any(row.get(k) != v for k, v in lookup[row['example_id']].items()):
            raise ValueError('Retention row changed from frozen bank')
        meta = row['generation_metadata']; tokens = meta.get('output_token_ids', [])
        normal = bool(tokens) and tokens[-1] == protocol['eos_token_id'] and meta.get('finish_reason') == 'stop' and not meta.get('backend_error')
        if (row.get('error') or meta.get('backend_error') or not tokens or
            meta.get('model_revision') != runtime['generation']['revision'] or
            meta.get('adapter_lora_id') != (None if model == 'base' else 1) or
            meta.get('input_token_ids') != row['expected_input_token_ids'] or
            meta.get('sampling_seed') != (row['seed'] ^ 42 ^ row['eval_seed']) & 0xffffffff or
            meta.get('generation_tokens') != len(tokens) or
            meta.get('execution') != runtime['generation'] or meta.get('execution_versions') != runtime['versions']):
            raise ValueError('Unverified retention runtime/tokens')
        raw = tokenizer.decode(tokens[:-1] if normal else tokens, skip_special_tokens=False)
        if raw != row['response'] or hashlib.sha256(raw.encode()).hexdigest() != row['response_sha256']:
            raise ValueError('Raw reply/token/hash mismatch')
        grade = assess(raw, row, normal_stop=normal)
        if grade != row['assessment']:
            raise ValueError('Frozen original grade changed')
        values.append({k: row[k] for k in ('example_id', 'question_id', 'family', 'thinking', 'eval_seed', 'response_sha256')}
            | {'frozen_assessment': grade, 'value': assess_value(raw, row, normal_stop=normal)})
    strict = rows(folder / 'known_items.jsonl')
    if model == 'base':
        if report([r for r in actual if r['eval_seed'] == 42], bank)[1] != strict:
            raise ValueError('Original strict BASE mask changed')
    elif strict != rows(Path('data/results/ethical_pilot') / retention_id('base') / 'known_items.jsonl'):
        raise ValueError('Original strict reference changed')
    summary = read(folder / 'summary.json')
    for seed in (42, 7, 1729):
        if report([r for r in actual if r['eval_seed'] == seed], bank, strict)[0] != summary['by_seed'][str(seed)]:
            raise ValueError('Original strict summary does not reconstruct')
    return values, summary


def retention_config(model: str, protocol: dict, binding: dict) -> dict:
    _, parent = roots()
    strict = Path('data/results/ethical_pilot') / retention_id('base') / 'known_items.jsonl'
    return {'defaults': ['ethics_gpu_retention_rca_base_v2'], 'run_id': retention_id(model),
        'pilot_bench': {'adapter_path': binding['adapter_path']},
        'instruction_retention': {'model_label': model, 'bank_path': protocol['bank_path'],
            'bank_sha256': protocol['bank_sha256'], 'known_path': str(strict), 'known_sha256': sha(strict),
            'fresh_base_reference': False, 'adapter_sha256': binding['adapter_file_sha256'],
            'eval_seeds': [42, 7, 1729]}}


def collect_retention(model: str, protocol: dict, tokenizer, binding: dict | None = None) -> None:
    import yaml
    check_bindings(protocol['source_bindings'])
    _, parent = roots()
    folder = Path('data/results/ethical_pilot') / retention_id(model)
    if folder.exists() or (parent / (model + '_values.jsonl')).exists():
        raise FileExistsError('Started retention stage cannot resume/overwrite')
    if model != 'base':
        assert binding is not None
        verify_binding(binding)
        config = Path('configs/run', retention_id(model) + '.yaml')
        if config.exists():
            raise FileExistsError('Runtime adapter config already exists')
        config.write_text('# @package _global_\n' + yaml.safe_dump(retention_config(model, protocol, binding), sort_keys=False))
        write_json(parent / (model + '_retention_binding.json'), binding)
    job = load_job(['+run=' + retention_id(model)])
    if model == 'base' and config_sha(job) != protocol['jobs'][retention_id('base')]:
        raise ValueError('Prepared BASE config changed')
    write_json(parent / (model + '_retention_dispatch.json'), {'source_commit': commit(),
        'config_sha': config_sha(job), 'adapter_sha256': job.instruction_retention.adapter_sha256})
    if not execute([*LOCK, EVAL_PYTHON, '-u', 'run.py', '+run=' + retention_id(model)], parent, 'retention/' + model):
        raise RuntimeError('Retention child failed: ' + model)
    values, _ = inspect_retention(model, protocol, tokenizer)
    write_rows(parent / (model + '_values.jsonl'), values)
    if model == 'base':
        known = value_known(values)
        write_rows(parent / 'value_known_items.jsonl', known)
        write_json(parent / 'value_reference_freeze.json', {'mask_sha256': sha(parent / 'value_known_items.jsonl'),
            'base_values_sha256': sha(parent / 'base_values.jsonl'), 'selection_seed': 42,
            'selection': 'Correct recognized task value, complete boundaries/normal stop; format independent.'})
    base = rows(parent / 'base_values.jsonl'); known = rows(parent / 'value_known_items.jsonl')
    write_json(parent / (model + '_assessment.json'), summarize(values, base, known))
    lookup = {(r['example_id'], r['eval_seed']): r for r in values}
    queue = [{'model': model, 'observation': r, 'value': lookup[r['example_id'], r['eval_seed']]['value']}
        for r in rows(folder / 'responses.jsonl') if not r['assessment']['admissible'] or
        lookup[r['example_id'], r['eval_seed']]['value']['value_correct'] is not True]
    write_rows(parent / (model + '_review_queue.jsonl'), queue)


def reference_review_complete(parent: Path) -> None:
    summary_path = parent / 'reference_review_v1.json'
    summary = read(summary_path)
    review_path = parent / 'reference_agent_review_v1.jsonl'
    if summary.get('full_response_review_complete') is not True or summary.get('review_sha256') != sha(review_path):
        raise ValueError('Complete full reference review before SFT')
    expected = set()
    for model in ('base', 'norm1'):
        path = parent / (model + '_review_queue.jsonl')
        if summary['queue_sha256'].get(model) != sha(path):
            raise ValueError('Reference queue changed since review')
        for row in rows(path):
            o = row['observation']; expected.add((model, o['example_id'], o['eval_seed'], o['response_sha256']))
    reviews = rows(review_path)
    actual = [(r['model'], r['example_id'], r['eval_seed'], r['response_sha256']) for r in reviews]
    if len(actual) != len(expected) or set(actual) != expected or any(r['review_mode'] != 'agent_read_full_response' for r in reviews):
        raise ValueError('Full reference review coverage/hash mismatch')
    preserved(summary_path); preserved(review_path)


def verify_candidate(protocol: dict) -> dict:
    plan = read(Path('data/generated/ethical_stance_sft') / TRAIN / 'plan.json')
    folder = Path('data/results/ethical_stance_sft') / TRAIN
    binding = training_binding(plan, folder, Path('data/checkpoints/ethical_stance_sft') / TRAIN / 'final')
    if read(folder / 'summary.json')['training']['weighted_objective'] != plan['weighted_objective_projection']:
        raise ValueError('Candidate objective differs from frozen matched control')
    control = rows(Path('data/results/ethical_stance_sft') / CONTROL / 'tokenized.jsonl')
    if rows(folder / 'tokenized.jsonl') != control:
        raise ValueError('Candidate actual input IDs/labels/order/weights changed')
    return binding


def full_surface(protocol: dict, binding: dict, parent: Path) -> None:
    def phase(name: str) -> None:
        check_bindings(protocol['source_bindings'])
        verify_binding(binding)
        job = load_job(['+run=' + eval_id(name)])
        if config_sha(job) != protocol['jobs'][eval_id(name)]:
            raise ValueError('Prepared full100config changed')
        if not execute([*LOCK, EVAL_PYTHON, '-u', 'run.py', '+run=' + eval_id(name)], parent, name):
            raise RuntimeError('Full100phase technical failure: ' + name)
    phase('development')
    root = Path('data/results/ethical_pilot')
    dev = read(root / eval_id('development') / 'stance_study_summary.json')
    development_ok = dev.get('selected') == 'named_endorse_reject'
    validation_ok = False
    if development_ok:
        phase('validation')
        validation_ok = read(root / eval_id('validation') / 'stance_study_summary.json').get('validation_passed') is True
    chosen = 'reading' if development_ok and validation_ok else 'unqualified'
    phase(chosen)
    status = original_surface_status(root / eval_id(chosen))
    write_json(parent / 'candidate_measurement_status.json', {'development_passed': development_ok,
        'validation_passed': validation_ok, 'stance_run_id': eval_id(chosen), 'actual_coverage': status,
        'value_retention_passed': read(parent / 'candidate_assessment.json')['passed'],
        'interpretation': 'Retain all failures; no ethical outcome or invalid answer triggers another attempt.'})
    if status['recorded'] != 2400:
        raise ValueError('Full100calls missing despite explicit collection policy; preserve/reassess')


def run(operation: str) -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend()
    generated, parent = roots()
    protocol_path = generated / 'protocol.json'; protocol = read(protocol_path)
    check_bindings(protocol['source_bindings']); preserved(protocol_path)
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    if operation == 'reference':
        if parent.exists():
            raise FileExistsError('Reference master already started; no resume')
        # Preflight all later outputs, including dynamically generated adapter configs.
        for model in MODELS:
            if (Path('data/results/ethical_pilot') / retention_id(model)).exists():
                raise FileExistsError('Retention ID already started')
            if model != 'base' and Path('configs/run', retention_id(model) + '.yaml').exists():
                raise FileExistsError('Runtime retention config already exists')
        for part in ('results', 'checkpoints'):
            if (Path('data') / part / 'ethical_stance_sft' / TRAIN).exists():
                raise FileExistsError('Candidate ID already started')
        for phase in ('development', 'validation', 'reading', 'unqualified'):
            if (Path('data/results/ethical_pilot') / eval_id(phase)).exists():
                raise FileExistsError('Candidate evaluation already started')
        parent.mkdir(parents=True)
        (parent / 'STARTED').write_text(commit() + '\n')
        try:
            collect_retention('base', protocol, tokenizer)
            check_bindings(protocol['source_bindings'])
            collect_retention('norm1', protocol, tokenizer, protocol['control_binding'])
            (parent / 'REFERENCE_COMPLETED').write_text('Both reference grids complete; full agent review/private preservation required before SFT.\n')
        except BaseException as exc:
            write_json(parent / 'reference_failure.json', {'error': repr(exc)}); raise
        finally:
            (parent / 'REFERENCE_TERMINAL').write_text('Finite reference worker ended; no resume.\n')
    elif operation == 'candidate':
        if not (parent / 'REFERENCE_COMPLETED').exists() or not (parent / 'REFERENCE_TERMINAL').exists():
            raise ValueError('Complete references before SFT')
        if (parent / 'CANDIDATE_STARTED').exists():
            raise FileExistsError('Candidate worker already started; no resume')
        if (Path('data/results/ethical_pilot') / retention_id('candidate')).exists() or Path('configs/run', retention_id('candidate') + '.yaml').exists():
            raise FileExistsError('Candidate confirmation already started/prepared')
        for phase in ('development', 'validation', 'reading', 'unqualified'):
            if (Path('data/results/ethical_pilot') / eval_id(phase)).exists():
                raise FileExistsError('Candidate evaluation already started')
        reference_review_complete(parent)
        freeze = read(parent / 'value_reference_freeze.json')
        if freeze['mask_sha256'] != sha(parent / 'value_known_items.jsonl') or freeze['base_values_sha256'] != sha(parent / 'base_values.jsonl'):
            raise ValueError('BASE cohort changed')
        for model in ('base', 'norm1'):
            values, _ = inspect_retention(model, protocol, tokenizer)
            if values != rows(parent / (model + '_values.jsonl')):
                raise ValueError('Saved reference values changed')
        if (Path('data/results/ethical_stance_sft') / TRAIN).exists() or (Path('data/checkpoints/ethical_stance_sft') / TRAIN).exists():
            raise FileExistsError('Candidate training already started')
        if config_sha(load_job(['+run=' + TRAIN])) != protocol['jobs'][TRAIN]:
            raise ValueError('Prepared candidate training config changed')
        (parent / 'CANDIDATE_STARTED').write_text(commit() + '\n')
        try:
            if not execute([*LOCK, TRAIN_PYTHON, '-u', 'run.py', '+run=' + TRAIN], parent, 'train/candidate'):
                raise RuntimeError('Candidate training failed')
            binding = verify_candidate(protocol)
            write_json(parent / 'candidate_training_binding.json', binding)
            collect_retention('candidate', protocol, tokenizer, binding)
            full_surface(protocol, binding, parent)
            (parent / 'COLLECTION_COMPLETED').write_text('Candidate trained and measured; inspect all failures/full review before any recipe claim.\n')
        except BaseException as exc:
            write_json(parent / 'candidate_failure.json', {'error': repr(exc)}); raise
        finally:
            (parent / 'CANDIDATE_TERMINAL').write_text('Finite candidate worker ended; no resume.\n')
    else:
        raise ValueError('Unknown bounded operation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('operation', choices=['reference', 'candidate'])
    run(parser.parse_args().operation)
