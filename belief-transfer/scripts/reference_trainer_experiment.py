"""One finite stock-Trainer comparison; no new tuning or repeat-until-pass."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import load_job, config_sha
from belief_transfer.dataset.document_sft import preprocessing_contract
from belief_transfer.stages.document_sft import verify_training_plan
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_replay_weight_confirmation import check_bindings, summarize
from validate_registry_calibration import training_binding
from analyze_replay_weight_ablation import original_surface_status

RUN = 'ethics_sft_hf_reference_norm1_v1'
OLD = 'ethics_sft_c4_norm1_v1'
GEN = Path('data/generated/ethical_stance_sft') / RUN
RESULT = Path('data/results/ethical_stance_sft') / RUN
CHECKPOINT = Path('data/checkpoints/ethical_stance_sft') / RUN
CONF = Path('data/results/ethical_pilot/ethics_gpu_replay_weight_confirmation_v1')
RETENTION = 'ethics_gpu_hf_reference_retention_v1'
PLAN = Path('../changelog/2026-10-22-hf-reference-experiment-plan.md')
TRAIN_PYTHON = '/workspace/sft-drift/belief-transfer/.venv/bin/python'
EVAL_PYTHON = '/workspace/sft-drift-vllm/.venv/bin/python'


def evaluation_id(phase: str) -> str:
    return f'ethics_gpu_hf_reference_{phase}_s42_v1'


def paths() -> list[str]:
    return [f'{part}/ethical_stance_sft/{RUN}' for part in ('generated', 'results', 'checkpoints')] + [
        f'{part}/ethical_pilot/{name}' for part in ('generated', 'results')
        for name in [RETENTION, *(evaluation_id(p) for p in ('development', 'validation', 'reading'))]]


def config_write(name: str, overlay: dict) -> Path:
    import yaml
    target = Path('configs/run', name + '.yaml')
    if target.exists():
        raise FileExistsError(target)
    target.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
    load_job(['+run=' + name])
    return target


def prepare() -> None:
    required = paths()
    if not set(required) <= set(read(Path('configs/handoff.json'))['include_paths']):
        raise ValueError('Register reference outputs before preparation')
    if any(Path('data', p).exists() for p in required):
        raise FileExistsError('Reference experiment already prepared/started; fresh ID required')
    source = Path('data/generated/ethical_stance_sft') / OLD
    original = read(source / 'plan.json')
    old_job = load_job(['+run=' + OLD])
    verify_training_plan(old_job, source / 'documents.jsonl')
    old_summary = read(Path('data/results/ethical_stance_sft') / OLD / 'summary.json')
    if not all(old_summary['training']['checks'].values()):
        raise ValueError('Historical engineering verification is not complete')
    if any(c.get('loss_weight', 1) != 1 for c in rows(Path('data/results/ethical_stance_sft') / OLD / 'tokenized.jsonl')):
        raise ValueError('Historical comparison is not unweighted')
    GEN.mkdir(parents=True)
    (GEN / 'documents.jsonl').write_bytes((source / 'documents.jsonl').read_bytes())
    from belief_transfer.analysis.jsonl_md import write_md
    write_md(GEN / 'documents.jsonl')
    spec = old_job.document_sft.model_copy(update={'trainer': 'hf_reference_v1',
        'manifest_path': str(GEN / 'documents.jsonl'), 'plan_path': str(GEN / 'plan.json'),
        'replay': old_job.document_sft.replay.model_copy(update={'loss_normalization': None})})
    plan = copy.deepcopy(original)
    plan.update(run_id=RUN, trainer='hf_reference_v1', preprocessing=preprocessing_contract(spec),
        hypothesis='If custom loss/backward causes the historical regression, stock HF loss on identical targets may avoid it.',
        falsifier='No trainer-repair claim if parity/comparability fails, or stock training reproduces the historical model-check failures.',
        contrasts='One fresh stock-HF run versus the completed unweighted custom-loss norm1 run and its fixed BASE references.',
        controls='Same model revision, initial adapter, text, labels, chunk order, batch groups, optimizer, LR trace, steps and final endpoint.',
        analysis=PLAN.read_text(), checkpoint_policy='Save steps227/454 for recovery; evaluate final only; no checkpoint selection.',
        provenance={'comparison_run': OLD, 'comparison_plan_sha256': sha(source / 'plan.json')})
    plan.pop('weighted_objective_projection', None)
    plan['dose'].pop('weighted_loss_tokens', None)
    write_json(GEN / 'plan.json', plan)
    config = config_write(RUN, {'defaults': [OLD], 'run_id': RUN,
        'document_sft': {'trainer': 'hf_reference_v1', 'manifest_path': str(GEN / 'documents.jsonl'),
            'plan_path': str(GEN / 'plan.json'), 'plan_sha256': sha(GEN / 'plan.json'),
            'replay': {'loss_normalization': None}}})
    verify_training_plan(load_job(['+run=' + RUN]), GEN / 'documents.jsonl')
    configs = [config]
    for phase, default in [('development', 'ethics_gpu_vllm_development_v1'),
                            ('validation', 'ethics_gpu_vllm_validation_v1'),
                            ('reading', 'ethics_gpu_vllm_base_v1')]:
        bench = {'adapter_path': str(CHECKPOINT / 'final'), 'seed': 42}
        if phase == 'validation':
            bench['stance_study'] = {'selection_run_id': evaluation_id('development')}
        if phase == 'reading':
            bench['stance_validation_run_id'] = None
        configs.append(config_write(evaluation_id(phase), {'defaults': [default],
            'run_id': evaluation_id(phase), 'pilot_bench': bench}))
    bound = [PLAN, Path(__file__), config, GEN / 'documents.jsonl', GEN / 'plan.json',
             *configs, source / 'plan.json', Path('data/results/ethical_stance_sft') / OLD / 'summary.json',
             Path('data/results/ethical_stance_sft') / OLD / 'tokenized.jsonl',
             Path('data/checkpoints/ethical_stance_sft') / OLD / 'training_batches.jsonl',
             CONF / 'base_values.jsonl', CONF / 'norm1_values.jsonl', CONF / 'value_known_items.jsonl',
             Path('data/generated/ethical_stance_sft/ethics_sft_replay_weight_ablation_v1/protocol.json')]
    bound += list(Path('src/belief_transfer/training').glob('*.py'))
    bound += [Path('src/belief_transfer/stages/document_sft.py'), Path('src/belief_transfer/dataset/document_sft.py')]
    # __file__ can be absolute. Persist portable bindings only.
    bound = [p.relative_to(Path.cwd()) if p.is_absolute() else p for p in bound]
    write_json(GEN / 'protocol.json', {'run_id': RUN, 'source_bindings': {str(p): sha(p) for p in bound},
        'training_runs_max': 1, 'retention_calls': 384, 'full100_natural_calls': 2400,
        'checkpoint': 'final only', 'wall_clock_review_hours': 3,
        'stop': 'Technical identity failure stops immediately; performance failures retained; no further training.',
        'runtime_reference': read(Path('data/generated/ethical_stance_sft/ethics_sft_replay_weight_ablation_v1/protocol.json'))['runtime_reference']})
    print(json.dumps({'prepared': RUN, 'training_runs': 1, 'draws': old_summary['draws'],
                      'chunks': old_summary['chunks'], 'targets': old_summary['loss_tokens']}))


def run() -> None:
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    p = read(GEN / 'protocol.json')
    check_bindings(p['source_bindings'])
    from run_replay_coverage_probe import preserved
    preserved(GEN / 'protocol.json')
    for folder in (RESULT, CHECKPOINT, Path('data/results/ethical_pilot') / RETENTION,
                   *(Path('data/results/ethical_pilot') / evaluation_id(s) for s in ('development', 'validation', 'reading'))):
        if folder.exists():
            raise FileExistsError('Started experiment cannot restart: ' + str(folder))
    # The ordinary stage owns RESULT/STARTED. Controller logs live in GEN, separately.
    log = GEN / 'execution.log'
    with log.open('x') as stream:
        def execute(command: list[str]) -> None:
            stream.write(json.dumps({'command': command}) + '\n'); stream.flush()
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        lock = ['flock', '/tmp/sft-drift-cuda-benchmark.lock']
        execute([*lock, TRAIN_PYTHON, '-u', 'run.py', '+run=' + RUN])
        plan = read(GEN / 'plan.json')
        binding = training_binding(plan, RESULT, CHECKPOINT / 'final')
        summary = read(RESULT / 'summary.json')
        old = read(Path('data/results/ethical_stance_sft') / OLD / 'summary.json')
        def clean(c):
            return {k: v for k, v in c.items() if k not in {'loss_weight', 'replay_thinking'}}
        if ([clean(c) for c in rows(RESULT / 'tokenized.jsonl')] !=
                [clean(c) for c in rows(Path('data/results/ethical_stance_sft') / OLD / 'tokenized.jsonl')]):
            raise ValueError('Training input/label comparison failed')
        new_audit = rows(CHECKPOINT / 'training_batches.jsonl')
        old_audit = rows(Path('data/checkpoints/ethical_stance_sft') / OLD / 'training_batches.jsonl')
        parity = {'initial_adapter': summary['training']['initial_adapter_sha256'] == old['training']['initial_adapter_sha256'],
            'batch_schedule': [[clean(c) for c in b['chunks']] for b in new_audit] == [[clean(c) for c in b['chunks']] for b in old_audit],
            'lr_trace': [r['learning_rate'] for r in summary['training']['log_history'] if 'learning_rate' in r] ==
                        [r['learning_rate'] for r in old['training']['log_history'] if 'learning_rate' in r],
            'eligible_token_count': summary['loss_tokens'] == old['loss_tokens']}
        write_json(RESULT / 'comparability.json', parity)
        if not all(parity.values()):
            raise ValueError('Reference comparison confounded; no repair claim')
        write_json(RESULT / 'training_binding.json', binding)
        from safetensors.torch import load_file
        import torch
        a = load_file(str(CHECKPOINT / 'final/adapter_model.safetensors'))
        b = load_file(str(Path('data/checkpoints/ethical_stance_sft') / OLD / 'final/adapter_model.safetensors'))
        if a.keys() != b.keys():
            raise ValueError('Adapter parameter identities differ')
        write_json(RESULT / 'adapter_comparison.json', {'byte_exact': sha(CHECKPOINT / 'final/adapter_model.safetensors') ==
            sha(Path('data/checkpoints/ethical_stance_sft') / OLD / 'final/adapter_model.safetensors'),
            'max_abs_difference': max(float((a[k].float() - b[k].float()).abs().max()) for k in a),
            'relative_l2_difference': float(torch.sqrt(sum(((a[k].float()-b[k].float())**2).sum() for k in a) /
                sum((b[k].float()**2).sum() for k in b)))})
        del a, b
        import yaml
        bank = Path('data/generated/ethical_pilot/ethics_gpu_replay_weight_confirmation_v1/bank.jsonl')
        known = Path('data/results/ethical_pilot/ethics_gpu_replay_weight_base_retention_v1/known_items.jsonl')
        ret_config = config_write(RETENTION, {'defaults': ['ethics_gpu_retention_rca_base_v2'], 'run_id': RETENTION,
            'pilot_bench': {'adapter_path': str(CHECKPOINT / 'final')},
            'instruction_retention': {'model_label': 'hf_reference', 'bank_path': str(bank), 'bank_sha256': sha(bank),
                'known_path': str(known), 'known_sha256': sha(known), 'adapter_sha256': binding['adapter_file_sha256'],
                'eval_seeds': [42, 7, 1729]}})
        execute([*lock, EVAL_PYTHON, '-u', 'run.py', '+run=' + RETENTION])
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(load_job(['+run=' + RUN]).model_spec.pretrained,
            revision=summary['training']['model_revision'], local_files_only=True)
        from belief_transfer.stages.instruction_retention import observation
        from belief_transfer.evals.retention_value import assess_value
        root = Path('data/results/ethical_pilot') / RETENTION
        manifest = read(root / 'manifest.json')
        for key in ('model', 'backend', 'generation', 'decoding', 'max_new_tokens', 'batch_size', 'versions'):
            if manifest[key] != p['runtime_reference'][key]:
                raise ValueError('Retention runtime changed: ' + key)
        if manifest['adapter_sha256'] != binding['adapter_file_sha256'] or rows(root / 'bank.jsonl') != rows(bank):
            raise ValueError('Wrong adapter or retention inputs')
        lookup = {r['example_id']: r for r in rows(bank)}
        values = []
        for r in rows(root / 'responses.jsonl'):
            if observation(lookup[r['example_id']], (r['backend_text'], r['generation_metadata']), tokenizer,
                    evaluation=r['eval_seed'], revision=summary['training']['model_revision'], adapter=True) != r:
                raise ValueError('Raw retention token/metadata reconstruction failed')
            values.append({k: r[k] for k in ('example_id', 'question_id', 'family', 'thinking', 'eval_seed', 'response_sha256')} |
                {'frozen_assessment': r['assessment'], 'value': assess_value(r['response'], r, normal_stop=r['assessment']['normal_stop'])})
        write_rows(RESULT / 'retention_values.jsonl', values)
        write_json(RESULT / 'retention_assessment.json', summarize(values, rows(CONF / 'base_values.jsonl'), rows(CONF / 'value_known_items.jsonl')))
        execute([*lock, EVAL_PYTHON, '-u', 'run.py', '+run=' + evaluation_id('development')])
        dev = read(Path('data/results/ethical_pilot') / evaluation_id('development') / 'stance_study_summary.json')
        if dev.get('selected') == 'named_endorse_reject':
            execute([*lock, EVAL_PYTHON, '-u', 'run.py', '+run=' + evaluation_id('validation')])
        execute([*lock, EVAL_PYTHON, '-u', 'run.py', '+run=' + evaluation_id('reading')])
        status = original_surface_status(Path('data/results/ethical_pilot') / evaluation_id('reading'))
        write_json(RESULT / 'full100_status.json', status)
        if status['recorded'] != 2400:
            raise ValueError('Full100collection incomplete; retain partials, no retry')
        (RESULT / 'COLLECTION_COMPLETED').write_text('One reference training and fixed final evaluations collected; agent review pending.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'run'])
    args = parser.parse_args()
    if args.operation == 'prepare':
        prepare()
    else:
        try:
            run()
        except BaseException as exc:
            if RESULT.exists():
                write_json(RESULT / 'controller_failure.json', {'error': repr(exc)})
            raise
        finally:
            if RESULT.exists():
                (RESULT / 'TERMINAL').write_text('Finite reference worker ended; no automatic retry or further training.\n')
