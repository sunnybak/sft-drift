"""Prepare one untrained replay recipe with explicit reused reference provenance."""
from __future__ import annotations

import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.stages.document_sft import verify_training_plan
from prepare_replay_weight_ablation import read, rows, sha, write_json
from belief_transfer.analysis.jsonl_md import write_md

MASTER = 'ethics_sft_replay_coverage_value_v5'
TRAIN = 'ethics_sft_c4_replay_coverage_v5'
REFERENCE = 'ethics_sft_replay_coverage_probe_v4'
OLD_TRAIN = 'ethics_sft_c4_replay_coverage_v4'
PLAN = Path('../changelog/2026-10-22-replay-coverage-value-v5-plan.md')


def reference_root() -> Path:
    return Path('data/results/ethical_stance_sft') / REFERENCE


def candidate_id(kind: str) -> str:
    if kind not in ('retention', 'decisions'):
        raise ValueError('Unknown candidate measurement')
    return f'ethics_gpu_replay_coverage_candidate_{kind}_v5'


def eval_id(phase: str) -> str:
    if phase not in ('development', 'validation', 'reading', 'unqualified'):
        raise ValueError('Unknown evaluation phase')
    return f'ethics_gpu_replay_coverage_{phase}_s42_v5'


def required_paths() -> list[str]:
    return ([f'{p}/ethical_stance_sft/{MASTER}' for p in ('generated', 'results')]
        + [f'{p}/ethical_stance_sft/{TRAIN}' for p in ('generated', 'results', 'checkpoints')]
        + [f'{p}/ethical_pilot/{n}' for n in [candidate_id(k) for k in ('retention', 'decisions')]
            + [eval_id(x) for x in ('development', 'validation', 'reading', 'unqualified')]
            for p in ('generated', 'results')])


def same_recipe(old, new) -> bool:
    def clean(job):
        value = job.model_dump(mode='json')
        value.pop('run_id')
        for key in ('manifest_path', 'plan_path', 'plan_sha256'):
            value['document_sft'].pop(key)
        return value
    return clean(old) == clean(new)


def prepare() -> dict:
    import yaml
    registry = read(Path('configs/handoff.json'))
    if not set(required_paths()) <= set(registry['include_paths']):
        raise ValueError('Register all output paths first')
    if any(Path('data', p).exists() for p in required_paths()):
        raise FileExistsError('Fresh IDs required; no overwrite/resume')
    names = [TRAIN, *[eval_id(p) for p in ('development', 'validation', 'reading', 'unqualified')],
             candidate_id('retention'), candidate_id('decisions')]
    if any(Path('configs/run', n + '.yaml').exists() for n in names):
        raise FileExistsError('Output config exists')
    ref = reference_root()
    summary = read(ref / 'reference_review_v1.json')
    if (not summary['full_response_review_complete'] or summary['review_sha256'] != sha(ref / 'reference_agent_review_v1.jsonl')
            or summary['n'] != 62 or read(ref / 'reference_token_audit_v1.json')['total'] != 384):
        raise ValueError('Require reviewed and reconstructed references')
    for path, digest in summary['queue_sha256'].items():
        if sha(Path(path)) != digest:
            raise ValueError('Reviewed queue changed')
    if not read(ref / 'base_decisions_value_assessment_v2.json')['reference_usable']:
        raise ValueError('Supplementary BASE cohort insufficient')
    freeze = read(ref / 'decisions_value_reference_freeze_v2.json')
    if (freeze['mask_sha256'] != sha(ref / 'decisions_value_known_items_v2.jsonl') or
            freeze['base_values_sha256'] != sha(ref / 'base_decisions_value_v2.jsonl')):
        raise ValueError('Supplementary BASE mask changed')
    old_root = Path('data/generated/ethical_stance_sft') / OLD_TRAIN
    old_job = load_job(['+run=' + OLD_TRAIN])
    verify_training_plan(old_job, old_root / 'documents.jsonl')
    for part in ('results', 'checkpoints'):
        if (Path('data') / part / 'ethical_stance_sft' / OLD_TRAIN).exists():
            raise ValueError('This amendment requires the original recipe to be untrained')
    original = read(Path('data/generated/ethical_stance_sft') / REFERENCE / 'protocol.json')
    target = Path('data/generated/ethical_stance_sft') / TRAIN
    target.mkdir(parents=True)
    (target / 'documents.jsonl').write_bytes((old_root / 'documents.jsonl').read_bytes())
    write_md(target / 'documents.jsonl')
    plan = copy.deepcopy(read(old_root / 'plan.json'))
    plan.update(run_id=TRAIN, analysis=PLAN.read_text(),
        falsifier='All engineering, procedural value-v1, supplemental value-v2 retention/strict-format, original qualification and2400valid natural replies; no lowered thresholds.',
        provenance=plan['provenance'] | {'master_id': MASTER, 'untrained_recipe_parent': OLD_TRAIN,
            'reference_parent': REFERENCE, 'assessment_version': 'neutral-task-value-v2'})
    write_json(target / 'plan.json', plan)
    overlays = {TRAIN: {'defaults': [OLD_TRAIN], 'run_id': TRAIN, 'document_sft': {
        'manifest_path': str(target / 'documents.jsonl'), 'plan_path': str(target / 'plan.json'),
        'plan_sha256': sha(target / 'plan.json')}}}
    for phase in ('development', 'validation', 'reading', 'unqualified'):
        bench = {'adapter_path': f'data/checkpoints/ethical_stance_sft/{TRAIN}/final', 'seed': 42}
        if phase == 'validation':
            bench['stance_study'] = {'selection_run_id': eval_id('development')}
        if phase in ('reading', 'unqualified'):
            bench.update(measurement_control_failure_policy='collect_unqualified',
                stance_validation_run_id=eval_id('validation') if phase == 'reading' else None)
        overlays[eval_id(phase)] = {'defaults': [f'ethics_gpu_replay_coverage_{phase}_s42_v4'],
            'run_id': eval_id(phase), 'pilot_bench': bench}
    jobs = {}
    for name, overlay in overlays.items():
        Path('configs/run', name + '.yaml').write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        jobs[name] = config_sha(load_job(['+run=' + name]))
    if not same_recipe(old_job, load_job(['+run=' + TRAIN])):
        raise ValueError('Training settings changed beyond output/plan paths')
    if sha(target / 'documents.jsonl') != sha(old_root / 'documents.jsonl'):
        raise ValueError('Manifest bytes changed')
    verify_training_plan(load_job(['+run=' + TRAIN]), target / 'documents.jsonl')
    paths = [PLAN, Path('configs/handoff.json'), target / 'documents.jsonl', target / 'plan.json',
        old_root / 'documents.jsonl', old_root / 'plan.json',
        Path('data/generated/ethical_stance_sft') / REFERENCE / 'protocol.json',
        *[p for p in ref.iterdir() if p.is_file()],
        *sorted(Path('src/belief_transfer').rglob('*.py')), *sorted(Path('configs').rglob('*.yaml')),
        *[Path('scripts', n) for n in ('prepare_replay_value_probe.py', 'run_replay_value_probe.py',
            'review_replay_coverage_references.py', 'run_replay_coverage_probe.py',
            'prepare_replay_coverage_probe.py', 'prepare_replay_weight_ablation.py',
            'run_replay_weight_confirmation.py', 'run_ethical_four_arm.py',
            'validate_registry_calibration.py', 'analyze_replay_weight_ablation.py')]]
    for model in ('base', 'control'):
        for kind in ('retention', 'decisions'):
            from prepare_replay_coverage_probe import retention_id, decision_id
            name = retention_id(model) if kind == 'retention' else decision_id(model)
            child = Path('data/results/ethical_pilot') / name
            paths.extend(p for p in child.rglob('*') if p.is_file())
    paths += [Path(original['bank_path']), Path(original['decision_bank_path'])]
    protocol = {k: original[k] for k in ('bank_path', 'bank_sha256', 'decision_bank_path',
        'decision_bank_sha256', 'runtime_reference', 'eos_token_id', 'chunks', 'projection', 'control_binding')}
    protocol.update(run_id=MASTER, train_id=TRAIN, reference_parent=REFERENCE, jobs=jobs,
        assessment_version='neutral-task-value-v2', reference_calls=0, candidate_calls=192,
        full100_candidate_calls=2400, no_resume=True, checkpoint_choice='final only',
        source_bindings={str(p): sha(p) for p in paths})
    output = Path('data/generated/ethical_stance_sft') / MASTER
    output.mkdir(parents=True)
    write_json(output / 'protocol.json', protocol)
    return protocol


if __name__ == '__main__':
    p = prepare()
    print({'run_id': p['run_id'], 'train_id': p['train_id'], 'source_bindings': len(p['source_bindings'])})
