"""Finite reference and candidate workers for the frozen replay-data intervention."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.retention_value import assess_value
from belief_transfer.evals.neutral_decision_retention import summarize as decision_summary
from belief_transfer.metrics.instruction_retention import FAMILIES, report
from belief_transfer.stages.instruction_retention import observation as retention_observation
from belief_transfer.stages.neutral_decision_retention import observation as decision_observation
from prepare_replay_coverage_probe import MASTER, TRAIN, CONTROL, MODELS, retention_id, decision_id, eval_id
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_replay_weight_confirmation import check_bindings, value_known
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
        raise ValueError('Privately preserve frozen input/review before GPU calls: ' + str(path))


def commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()


def summarize_values(values: list[dict], base: list[dict], known: list[dict]) -> dict:
    actual = {(r['example_id'], r['eval_seed']): r for r in values}
    reference = {(r['example_id'], r['eval_seed']): r for r in base}
    if len(actual) != 128 or len(values) != 128 or actual.keys() != reference.keys():
        raise ValueError('Procedural value comparison coverage mismatch')
    result = {}
    for mode in (True, False):
        ids = {r['example_id'] for r in known if r['thinking'] == mode}
        sufficient = len(ids) >= 32 and {r['family'] for r in known if r['thinking'] == mode} == set(FAMILIES)
        group = [r for r in values if r['thinking'] == mode]
        selected = [r for r in group if r['example_id'] in ids]
        correct = sum(r['value']['value_correct'] is True for r in selected)
        strict = sum(r['frozen_assessment']['strict_format'] for r in selected)
        base_strict = sum(reference[r['example_id'], 42]['frozen_assessment']['strict_format'] for r in selected)
        complete = all(r['frozen_assessment']['normal_stop'] and r['frozen_assessment']['response_boundaries_valid'] for r in group)
        result[str(mode)] = {'known_n': len(ids), 'known_correct': correct, 'reference_usable': sufficient,
            'full_correct': sum(r['value']['value_correct'] is True for r in group),
            'full_wrong': sum(r['value']['value_correct'] is False for r in group),
            'full_unscorable': sum(r['value']['value_correct'] is None for r in group),
            'known_strict_format': strict, 'base_known_strict_format': base_strict,
            'complete_boundaries_and_stops': complete,
            'known_losses_or_unscorable': [r['example_id'] for r in selected if r['value']['value_correct'] is not True],
            'passed': sufficient and correct*100 >= 95*len(ids) and (base_strict-strict)*100 <= 5*len(ids) and complete}
    return {'by_mode': result, 'passed': all(r['passed'] for r in result.values()),
            'criteria': 'Value-v1 >=95%BASE-known each mode,<=5ppstrict deficit; all128complete; min32/all8families.'}


def decision_known(observed: list[dict]) -> list[dict]:
    return [{k: r[k] for k in ('example_id', 'thinking', 'operation', 'expected', 'response_sha256')}
            for r in observed if r['assessment']['value_correct'] is True]


def compare_decisions(observed: list[dict], base: list[dict], known: list[dict]) -> dict:
    full = decision_summary(observed)
    if {r['example_id'] for r in observed} != {r['example_id'] for r in base}:
        raise ValueError('Decision comparison coverage mismatch')
    if len({r['example_id'] for r in known}) != len(known):
        raise ValueError('Duplicate decision known mask')
    result = {}
    for mode in (True, False):
        selected_known = [r for r in known if r['thinking'] == mode]
        ids = {r['example_id'] for r in selected_known}
        sufficient = (len(ids) >= 24 and {r['operation'] for r in selected_known} == {'sum', 'difference', 'product', 'comparison'}
                      and {r['expected'] for r in selected_known} == {'endorse', 'reject'})
        group = [r for r in observed if r['thinking'] == mode]
        correct = sum(r['assessment']['value_correct'] is True for r in group if r['example_id'] in ids)
        complete = all(r['assessment']['normal_stop'] and r['assessment']['response_boundaries_valid'] for r in group)
        strict = all(r['assessment']['strict_format'] for r in group)
        result[str(mode)] = {'known_n': len(ids), 'known_correct': correct, 'reference_usable': sufficient,
            'all_complete': complete, 'all_strict': strict,
            'known_losses_or_unscorable': [r['example_id'] for r in group if r['example_id'] in ids and r['assessment']['value_correct'] is not True],
            'passed': sufficient and correct*100 >= 95*len(ids) and complete and strict}
    return {'by_mode': result, 'full': full, 'reference_usable': all(r['reference_usable'] for r in result.values()),
            'passed': all(r['passed'] for r in result.values()),
            'criteria': '>=24/32BASE-known each mode/all4operations/bothlabels;>=95%retention;all64complete/exactfinals.'}


def inspect(model: str, kind: str, protocol: dict, tokenizer, *,
            parent: Path | None = None, name: str | None = None) -> list[dict]:
    parent = roots()[1] if parent is None else parent
    name = name or (retention_id(model) if kind == 'retention' else decision_id(model))
    folder = Path('data/results/ethical_pilot') / name
    if not (folder / 'COMPLETED').is_file():
        raise ValueError('Incomplete child: ' + name)
    dispatch = read(parent / f'{model}_{kind}_dispatch.json')
    manifest = read(folder / 'manifest.json')
    job = load_job(['+run=' + name])
    if config_sha(job) != dispatch['config_sha'] or not dispatch['source_commit'].startswith(manifest['code_revision']):
        raise ValueError('Child config/source identity changed')
    runtime = protocol['runtime_reference']
    for key in ('model', 'backend', 'generation', 'decoding', 'max_new_tokens', 'batch_size', 'versions'):
        if manifest[key] != runtime[key]:
            raise ValueError('Child runtime differs: ' + key)
    bank_path = Path(protocol['bank_path'] if kind == 'retention' else protocol['decision_bank_path'])
    if sha(folder / 'bank.jsonl') != sha(bank_path):
        raise ValueError('Child bank changed')
    bank = {r['example_id']: r for r in rows(bank_path)}
    observed = rows(folder / 'responses.jsonl')
    if Counter(r['example_id'] for r in observed) != Counter(bank.keys()):
        raise ValueError('Missing/duplicate child grid')
    if manifest['adapter_sha256'] != dispatch['adapter_sha256']:
        raise ValueError('Child adapter differs')
    values = []
    for r in observed:
        meta = r['generation_metadata']
        if (r.get('error') or meta.get('execution') != runtime['generation'] or
                meta.get('execution_versions') != runtime['versions']):
            raise ValueError('Unverified backend execution; preserve child failure')
        if kind == 'retention':
            rebuilt = retention_observation(bank[r['example_id']], (r['backend_text'], meta), tokenizer,
                evaluation=42, revision=runtime['generation']['revision'], adapter=model != 'base')
        else:
            rebuilt = decision_observation(bank[r['example_id']], (r['backend_text'], meta), tokenizer,
                revision=runtime['generation']['revision'], adapter=model != 'base')
        if rebuilt != r:
            raise ValueError('Raw tokens/seed/assessment cannot be reconstructed')
        if kind == 'retention':
            values.append({k: r[k] for k in ('example_id', 'question_id', 'family', 'thinking', 'eval_seed', 'response_sha256')}
                | {'frozen_assessment': r['assessment'], 'value': assess_value(r['response'], r,
                    normal_stop=r['assessment']['normal_stop'])})
    if kind == 'retention':
        strict = rows(folder / 'known_items.jsonl')
        if model == 'base':
            if report(observed, list(bank.values()))[1] != strict:
                raise ValueError('Original strict mask changed')
        elif strict != rows(Path('data/results/ethical_pilot') / retention_id('base') / 'known_items.jsonl'):
            raise ValueError('Original strict BASE cohort changed')
        if read(folder / 'summary.json')['by_seed']['42'] != report(observed, list(bank.values()), strict)[0]:
            raise ValueError('Original strict counts changed')
    elif read(folder / 'summary.json') != decision_summary(observed):
        raise ValueError('Decision summary changed')
    return values if kind == 'retention' else observed


def runtime_config(model: str, kind: str, protocol: dict, binding: dict) -> dict:
    _, parent = roots()
    name = retention_id(model) if kind == 'retention' else decision_id(model)
    overlay = {'defaults': ['ethics_gpu_retention_rca_base_v2'], 'run_id': name,
               'pilot_bench': {'adapter_path': binding['adapter_path']}}
    if kind == 'retention':
        strict = Path('data/results/ethical_pilot') / retention_id('base') / 'known_items.jsonl'
        overlay['instruction_retention'] = {'model_label': model, 'bank_path': protocol['bank_path'],
            'bank_sha256': protocol['bank_sha256'], 'known_path': str(strict), 'known_sha256': sha(strict),
            'fresh_base_reference': False, 'adapter_sha256': binding['adapter_file_sha256'], 'eval_seeds': [42]}
    else:
        overlay.update(stage='neutral_decision_retention', instruction_retention=None,
            neutral_decision_retention={'model_label': model, 'bank_path': protocol['decision_bank_path'],
                'bank_sha256': protocol['decision_bank_sha256'], 'adapter_sha256': binding['adapter_file_sha256']})
    return overlay


def collect(model: str, kind: str, protocol: dict, tokenizer, binding: dict | None = None) -> None:
    import yaml
    _, parent = roots()
    name = retention_id(model) if kind == 'retention' else decision_id(model)
    check_bindings(protocol['source_bindings'])
    if (Path('data/results/ethical_pilot') / name).exists():
        raise FileExistsError('Started child cannot resume/overwrite')
    if binding:
        verify_binding(binding)
    if name not in protocol['jobs']:
        if binding is None:
            raise ValueError('Only adapter children may use runtime binding')
        config = Path('configs/run', name + '.yaml')
        if config.exists():
            raise FileExistsError('Runtime config already exists')
        config.write_text('# @package _global_\n' + yaml.safe_dump(runtime_config(model, kind, protocol, binding), sort_keys=False))
    job = load_job(['+run=' + name])
    if name in protocol['jobs'] and config_sha(job) != protocol['jobs'][name]:
        raise ValueError('Prepared child config changed')
    spec = job.instruction_retention if kind == 'retention' else job.neutral_decision_retention
    write_json(parent / f'{model}_{kind}_dispatch.json', {'source_commit': commit(), 'config_sha': config_sha(job),
        'adapter_sha256': spec.adapter_sha256})
    if not execute([*LOCK, EVAL_PYTHON, '-u', 'run.py', '+run=' + name], parent, kind + '/' + model):
        raise RuntimeError('Child technical failure: ' + name)
    result = inspect(model, kind, protocol, tokenizer)
    value_path = parent / f'{model}_{kind}_values.jsonl'
    write_rows(value_path, result)
    if model == 'base':
        known = value_known(result) if kind == 'retention' else decision_known(result)
        known_path = parent / f'{kind}_known_items.jsonl'
        write_rows(known_path, known)
        write_json(parent / f'{kind}_reference_freeze.json', {'mask_sha256': sha(known_path), 'base_values_sha256': sha(value_path)})
    known = rows(parent / f'{kind}_known_items.jsonl')
    base = rows(parent / f'base_{kind}_values.jsonl')
    summary = summarize_values(result, base, known) if kind == 'retention' else compare_decisions(result, base, known)
    write_json(parent / f'{model}_{kind}_assessment.json', summary)
    originals = rows(Path('data/results/ethical_pilot') / name / 'responses.jsonl')
    lookup = {r['example_id']: r for r in result}
    queue = []
    for r in originals:
        value = lookup[r['example_id']]['value'] if kind == 'retention' else r['assessment']
        strict = r['assessment']['admissible'] if kind == 'retention' else r['assessment']['strict_format']
        if not strict or value['value_correct'] is not True:
            queue.append({'model': model, 'kind': kind, 'observation': r, 'value': value})
    write_rows(parent / f'{model}_{kind}_review_queue.jsonl', queue)


def review_complete(parent: Path) -> None:
    summary_path = parent / 'reference_review_v1.json'
    summary = read(summary_path)
    review_path = parent / 'reference_agent_review_v1.jsonl'
    if not summary['full_response_review_complete'] or summary['review_sha256'] != sha(review_path):
        raise ValueError('Full reference review required before SFT')
    expected = set()
    for model in ('base', 'control'):
        for kind in ('retention', 'decisions'):
            path = parent / f'{model}_{kind}_review_queue.jsonl'
            if summary['queue_sha256'].get(str(path)) != sha(path):
                raise ValueError('Reference queue hash changed')
            for r in rows(path):
                o = r['observation']
                expected.add((model, kind, o['example_id'], o['response_sha256']))
    reviews = rows(review_path)
    actual = [(r['model'], r['kind'], r['example_id'], r['response_sha256']) for r in reviews]
    if (len(actual) != len(expected) or set(actual) != expected or
            any(r['review_mode'] != 'agent_read_full_response' for r in reviews)):
        raise ValueError('Reference review coverage mismatch')
    for kind in ('retention', 'decisions'):
        freeze = read(parent / f'{kind}_reference_freeze.json')
        if (freeze['mask_sha256'] != sha(parent / f'{kind}_known_items.jsonl') or
                freeze['base_values_sha256'] != sha(parent / f'base_{kind}_values.jsonl')):
            raise ValueError('Frozen BASE cohort changed')
    if not read(parent / 'base_decisions_assessment.json')['reference_usable']:
        raise ValueError('BASE supplemental reference insufficient; no candidate training')
    preserved(summary_path)
    preserved(review_path)


def verify_candidate(protocol: dict, tokenizer, *, train_id: str = TRAIN) -> dict:
    from belief_transfer.dataset.document_sft import load_manifest, tokenize_document
    plan = read(Path('data/generated/ethical_stance_sft') / train_id / 'plan.json')
    folder = Path('data/results/ethical_stance_sft') / train_id
    binding = training_binding(plan, folder, Path('data/checkpoints/ethical_stance_sft') / train_id / 'final')
    job = load_job(['+run=' + train_id])
    spec = job.document_sft
    expected = [c for r in load_manifest(Path(spec.manifest_path)) for c in tokenize_document(r, tokenizer,
        max_length=spec.max_length, synthetic_prefix=spec.synthetic_prefix, serialization=spec.serialization, replay=spec.replay)]
    if rows(folder / 'tokenized.jsonl') != expected or len(expected) != protocol['chunks']:
        raise ValueError('Actual training input/label identity differs')
    if read(folder / 'summary.json')['training']['weighted_objective'] != protocol['projection']:
        raise ValueError('Actual weighted exposure differs from frozen projection')
    return binding


def full_surface(protocol: dict, binding: dict, parent: Path, *, identify=eval_id) -> None:
    def phase(name: str) -> None:
        check_bindings(protocol['source_bindings'])
        verify_binding(binding)
        job = load_job(['+run=' + identify(name)])
        if config_sha(job) != protocol['jobs'][identify(name)]:
            raise ValueError('Frozen full100config changed')
        if not execute([*LOCK, EVAL_PYTHON, '-u', 'run.py', '+run=' + identify(name)], parent, name):
            raise RuntimeError('Full100phase technical failure: ' + name)
    root = Path('data/results/ethical_pilot')
    phase('development')
    dev_ok = read(root / identify('development') / 'stance_study_summary.json').get('selected') == 'named_endorse_reject'
    val_ok = False
    if dev_ok:
        phase('validation')
        val_ok = read(root / identify('validation') / 'stance_study_summary.json').get('validation_passed') is True
    chosen = 'reading' if dev_ok and val_ok else 'unqualified'
    phase(chosen)
    status = original_surface_status(root / identify(chosen))
    write_json(parent / 'candidate_measurement_status.json', {'development_passed': dev_ok,
        'validation_passed': val_ok, 'stance_run_id': identify(chosen), 'actual_coverage': status,
        'interpretation': 'All failed/missing outcomes retained; no automatic retry, adoption or ethical selection.'})
    if status['recorded'] != 2400:
        raise ValueError('Missing full100calls; preserve/reassess without restart')


def run(operation: str) -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend()
    generated, parent = roots()
    protocol_path = generated / 'protocol.json'
    protocol = read(protocol_path)
    check_bindings(protocol['source_bindings'])
    preserved(protocol_path)
    tokenizer = AutoTokenizer.from_pretrained(protocol['runtime_reference']['model']['pretrained'],
        revision=protocol['runtime_reference']['generation']['revision'], local_files_only=True)
    if operation == 'reference':
        if parent.exists():
            raise FileExistsError('Reference worker already started; no resume')
        for part in ('results', 'checkpoints'):
            if (Path('data') / part / 'ethical_stance_sft' / TRAIN).exists():
                raise FileExistsError('Training already started')
        for model in MODELS:
            for name in (retention_id(model), decision_id(model)):
                if (Path('data/results/ethical_pilot') / name).exists():
                    raise FileExistsError('Measurement already started')
                if name not in protocol['jobs'] and Path('configs/run', name + '.yaml').exists():
                    raise FileExistsError('Runtime config already exists')
        parent.mkdir(parents=True)
        (parent / 'STARTED').write_text(commit() + '\n')
        try:
            for model in ('base', 'control'):
                for kind in ('retention', 'decisions'):
                    collect(model, kind, protocol, tokenizer, None if model == 'base' else protocol['control_binding'])
            (parent / 'REFERENCE_COMPLETED').write_text('Both384reference records saved; full review/private preservation required.\n')
        except BaseException as exc:
            write_json(parent / 'reference_failure.json', {'error': repr(exc)})
            raise
        finally:
            (parent / 'REFERENCE_TERMINAL').write_text('Finite worker ended; no restart/resume.\n')
    elif operation == 'candidate':
        if not (parent / 'REFERENCE_COMPLETED').is_file() or not (parent / 'REFERENCE_TERMINAL').is_file():
            raise ValueError('Complete references before SFT')
        if (parent / 'CANDIDATE_STARTED').exists():
            raise FileExistsError('Candidate already started; no resume')
        for part in ('results', 'checkpoints'):
            if (Path('data') / part / 'ethical_stance_sft' / TRAIN).exists():
                raise FileExistsError('Training already started')
        for name in (retention_id('candidate'), decision_id('candidate')):
            if (Path('data/results/ethical_pilot') / name).exists() or Path('configs/run', name + '.yaml').exists():
                raise FileExistsError('Candidate measurement already started/prepared')
        review_complete(parent)
        for model in ('base', 'control'):
            for kind in ('retention', 'decisions'):
                inspected = inspect(model, kind, protocol, tokenizer)
                if inspected != rows(parent / f'{model}_{kind}_values.jsonl'):
                    raise ValueError('Saved reference values changed')
                if model == 'base':
                    expected_known = value_known(inspected) if kind == 'retention' else decision_known(inspected)
                    if expected_known != rows(parent / f'{kind}_known_items.jsonl'):
                        raise ValueError('BASE-known cohort does not reconstruct')
        if config_sha(load_job(['+run=' + TRAIN])) != protocol['jobs'][TRAIN]:
            raise ValueError('Candidate training config changed')
        (parent / 'CANDIDATE_STARTED').write_text(commit() + '\n')
        try:
            if not execute([*LOCK, TRAIN_PYTHON, '-u', 'run.py', '+run=' + TRAIN], parent, 'train/candidate'):
                raise RuntimeError('Candidate training technical failure')
            binding = verify_candidate(protocol, tokenizer)
            write_json(parent / 'candidate_training_binding.json', binding)
            for kind in ('retention', 'decisions'):
                collect('candidate', kind, protocol, tokenizer, binding)
            full_surface(protocol, binding, parent)
            (parent / 'COLLECTION_COMPLETED').write_text('Candidate trained/measured; full failure review before any adoption.\n')
        except BaseException as exc:
            write_json(parent / 'candidate_failure.json', {'error': repr(exc)})
            raise
        finally:
            (parent / 'CANDIDATE_TERMINAL').write_text('Finite worker ended; no restart/resume.\n')
    else:
        raise ValueError('Unknown finite operation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['reference', 'candidate'])
    run(parser.parse_args().operation)
