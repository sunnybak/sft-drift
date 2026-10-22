"""One matched coverage repair after the bound worker ends; never repeat until pass."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from prepare_replay_weight_ablation import MASTER, ARMS, read, sha, write_json
from analyze_replay_weight_ablation import original_surface_status, needs_completion_followup
from run_replay_weight_ablation import verify_training
from run_replay_weight_confirmation import check_bindings
from run_ethical_four_arm import execute
from validate_registry_calibration import verify_binding

RUN = 'ethics_gpu_replay_weight_completegrid_v1'
AMENDMENT = Path('../changelog/2026-10-22-collect-all-completion-amendment.md')
PYTHON = '/workspace/sft-drift-vllm/.venv/bin/python'


def child_id(arm: str) -> str:
    return f'ethics_gpu_replay_weight_{arm}_completegrid_s42_v1'


def required_paths() -> list[str]:
    return [f'{part}/ethical_pilot/{run}' for run in (RUN, *(child_id(a) for a in ARMS))
            for part in ('generated', 'results')]


def overlay(arm: str, original_run: str) -> dict:
    return {'defaults': [original_run], 'run_id': child_id(arm),
            'pilot_bench': {'measurement_control_failure_policy': 'collect_unqualified'}}


def original_statuses(parent: Path) -> dict:
    if not (parent / 'COLLECTION_COMPLETED').exists() or not (parent / 'TERMINAL').exists():
        raise ValueError('Bound two-model worker must finish before completion preparation')
    return {arm: read(parent / (arm + '_measurement_status.json')) for arm in ARMS}


def prepare() -> dict:
    import yaml
    parent = Path('data/results/ethical_stance_sft') / MASTER
    statuses = original_statuses(parent)
    coverage = {a: original_surface_status(Path('data/results/ethical_pilot') / s['stance_run_id'])
                for a, s in statuses.items()}
    decision = parent / 'completion_decision_v1.json'
    if decision.exists():
        raise FileExistsError('Completion decision already frozen')
    needed = needs_completion_followup(coverage)
    base = {'amendment_sha256': sha(AMENDMENT), 'original_coverage': coverage,
        'completion_needed': needed, 'trigger': 'Absent recorded natural calls only; never invalid answers/control/retention/stance scores.'}
    if not needed:
        write_json(decision, base)
        print('Both original grids recorded all2400presentations; no completion calls.')
        return base
    registry = read(Path('configs/handoff.json'))
    if not set(required_paths()) <= set(registry['include_paths']):
        raise ValueError('Register fresh complete-grid paths before preparation')
    if any(Path('data', p).exists() for p in required_paths()):
        raise FileExistsError('Completion IDs already prepared/started; no overwrite')
    if any(Path('configs/run', child_id(a) + '.yaml').exists() for a in ARMS):
        raise FileExistsError('Completion config already exists')
    bindings = {str(AMENDMENT): sha(AMENDMENT)}
    configs = {}; adapters = {}
    for arm in ARMS:
        binding = verify_training(arm)
        verify_binding(binding)
        adapters[arm] = binding
        run = statuses[arm]['stance_run_id']
        original = load_job(['+run=' + run])
        if original.pilot_bench.seed != 42 or original.pilot_bench.adapter_path != binding['adapter_path']:
            raise ValueError('Original full-grid model/seed does not match fixed final')
        spec = original.pilot_bench.model_copy(update={'measurement_control_failure_policy': 'collect_unqualified'})
        # Every scientific setting other than the collection guard stays identical.
        before = original.pilot_bench.model_dump(); after = spec.model_dump()
        before.pop('measurement_control_failure_policy', None); after.pop('measurement_control_failure_policy', None)
        if before != after:
            raise ValueError('Completion changes scientific settings')
        configs[arm] = overlay(arm, run)
        folder = Path('data/results/ethical_pilot') / run
        for p in [parent / (arm + '_measurement_status.json'), folder / 'measurement_summary.json',
                  folder / 'measurement_manifest.json', folder / 'stance_bank.jsonl',
                  folder / 'stance_observations.jsonl', folder / 'stance_control_bank.jsonl',
                  folder / 'stance_controls.jsonl', Path('configs/run') / (run + '.yaml'),
                  Path(binding['adapter_path']) / 'adapter_model.safetensors',
                  Path(binding['adapter_path']) / 'adapter_config.json']:
            bindings[str(p)] = sha(p)
    for p in [Path(__file__).relative_to(Path.cwd()), Path('scripts/analyze_replay_weight_ablation.py'),
              Path('scripts/prepare_replay_weight_ablation.py'), Path('run.py'),
              Path('scripts/run_replay_weight_ablation.py'), Path('scripts/run_replay_weight_confirmation.py'),
              Path('scripts/run_ethical_four_arm.py'), Path('scripts/validate_registry_calibration.py'),
              Path('tests/test_replay_weight_completion.py'), Path('tests/test_replay_weight_analysis.py'),
              Path('configs/handoff.json'), *sorted(Path('configs').rglob('*.yaml')),
              *sorted(Path('src/belief_transfer').rglob('*.py'))]:
        bindings[str(p)] = sha(p)
    # No writes until original coverage, both actual final adapters and all settings validate.
    generated = Path('data/generated/ethical_pilot') / RUN
    generated.mkdir(parents=True)
    jobs = {}
    for arm, config in configs.items():
        p = Path('configs/run') / (child_id(arm) + '.yaml')
        p.write_text('# @package _global_\n' + yaml.safe_dump(config, sort_keys=False))
        jobs[arm] = {'run_id': child_id(arm), 'config_sha': config_sha(load_job(['+run=' + child_id(arm)]))}
        bindings[str(p)] = sha(p)
    protocol = base | {'run_id': RUN, 'jobs': jobs, 'source_bindings': bindings, 'adapters': adapters,
        'expected_natural_calls': 4800, 'expected_fresh_controls': 64, 'no_resume': True,
        'interpretation': 'One new reading per BOTH fixed models, conditional only on absent original calls. Preserve failed controls/original attempts; no repeat until pass or training/checkpoint selection.'}
    write_json(generated / 'protocol.json', protocol)
    write_json(decision, base | {'completion_protocol_sha256': sha(generated / 'protocol.json')})
    print('Matched complete-grid inputs frozen; commit/push/private-save before run.')
    return protocol


def run() -> None:
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    generated = Path('data/generated/ethical_pilot') / RUN
    protocol_path = generated / 'protocol.json'
    protocol = read(protocol_path)
    check_bindings(protocol['source_bindings'])
    receipt = read(Path('data/.handoff-receipt.json'))
    if receipt['manifest']['files'].get(str(protocol_path.relative_to('data')), {}).get('sha256') != sha(protocol_path):
        raise ValueError('Preserve completion protocol privately before model calls')
    original_statuses(Path('data/results/ethical_stance_sft') / MASTER)
    out = Path('data/results/ethical_pilot') / RUN
    if out.exists() or any((Path('data/results/ethical_pilot') / child_id(a)).exists() for a in ARMS):
        raise FileExistsError('Completion already started; no resume/overwrite')
    out.mkdir(parents=True)
    (out / 'STARTED').write_text(subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True))
    write_json(out / 'protocol.json', protocol)
    coverage = {}
    try:
        for arm in ARMS:
            check_bindings(protocol['source_bindings']); verify_binding(protocol['adapters'][arm])
            if config_sha(load_job(['+run=' + child_id(arm)])) != protocol['jobs'][arm]['config_sha']:
                raise ValueError('Completion config changed')
            if not execute(['flock', '/tmp/sft-drift-cuda-benchmark.lock', PYTHON, '-u', 'run.py', '+run=' + child_id(arm)], out, arm):
                raise RuntimeError('Completion child failed; preserve, no automatic rerun: ' + arm)
            coverage[arm] = original_surface_status(Path('data/results/ethical_pilot') / child_id(arm))
            write_json(out / (arm + '_coverage.json'), coverage[arm])
            if coverage[arm]['recorded'] != 2400:
                raise RuntimeError('Collect-all child omitted calls; preserve, no second attempt')
        write_json(out / 'coverage.json', {'models': coverage,
            'all_expected_calls_recorded': True, 'all_answers_valid': all(v['complete'] for v in coverage.values()),
            'interpretation': 'One matched completion reading only; recorded calls are separate from valid answers and qualification. Original attempts remain untouched.'})
        (out / 'COMPLETED').write_text('Both one-time completion grids recorded; inspect validity/failed controls, no recipe qualification.\n')
    except BaseException as exc:
        write_json(out / 'failure.json', {'error': repr(exc)})
        raise
    finally:
        (out / 'TERMINAL').write_text('Finite completion worker ended; no resume/repeat.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.operation]()
