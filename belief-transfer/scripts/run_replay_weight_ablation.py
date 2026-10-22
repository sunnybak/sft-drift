"""Finite, final-only matched C4 ablation; measure both models irrespective of effects."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.inference.backend import require_training_backend
from belief_transfer.config import config_sha, load_job
from prepare_replay_weight_ablation import (
    MASTER, CONFIRMATION, ARMS, OLD, read, rows, sha, train_id, eval_id, retention_id,
    equivalent_chunks, write_json,
)
from run_replay_weight_confirmation import check_bindings
from run_ethical_four_arm import execute, measurement_choice
from validate_registry_calibration import training_binding, verify_binding

TRAIN_PYTHON = '/workspace/sft-drift/belief-transfer/.venv/bin/python'
EVAL_PYTHON = '/workspace/sft-drift-vllm/.venv/bin/python'


def verify_training(arm: str) -> dict:
    run = train_id(arm)
    plan = read(Path('data/generated/ethical_stance_sft') / run / 'plan.json')
    result = Path('data/results/ethical_stance_sft') / run
    checkpoint = Path('data/checkpoints/ethical_stance_sft') / run / 'final'
    binding = training_binding(plan, result, checkpoint)
    summary = read(result / 'summary.json')
    if summary['training']['weighted_objective'] != plan['weighted_objective_projection']:
        raise ValueError('Actual weighted objective differs from frozen projection')
    equivalent_chunks(rows(Path('data/results/ethical_stance_sft') / OLD / 'tokenized.jsonl'),
                      rows(result / 'tokenized.jsonl'))
    return binding


def full_surface(arm: str, binding: dict, output: Path) -> None:
    """Original model qualification remains explicit; failures still get full100."""
    lock = ['flock', '/tmp/sft-drift-cuda-benchmark.lock']
    def run_phase(phase: str) -> bool:
        verify_binding(binding)
        return execute([*lock, EVAL_PYTHON, '-u', 'run.py', '+run=' + eval_id(arm, phase)],
                       output, phase + '/' + arm)
    development_ok = run_phase('development')
    dev = Path('data/results/ethical_pilot') / eval_id(arm, 'development') / 'stance_study_summary.json'
    development_ok = development_ok and dev.exists() and read(dev).get('selected') == 'named_endorse_reject'
    validation_ok = run_phase('validation') if development_ok else False
    val = Path('data/results/ethical_pilot') / eval_id(arm, 'validation') / 'stance_study_summary.json'
    validation_ok = validation_ok and val.exists() and read(val).get('validation_passed') is True
    phase = measurement_choice(development_ok, validation_ok)
    if phase == 'unqualified':
        target = Path('data/results/ethical_pilot') / eval_id(arm, phase)
        target.mkdir(parents=True, exist_ok=False)
        (target / 'UNQUALIFIED.md').write_text('Model qualification failed. Collect all100beliefs under unchanged settings; retain failed controls. No ethical-outcome selection or retrospective qualification.\n')
    if not run_phase(phase):
        raise RuntimeError('Full100 collection failed; preserve partial outputs: ' + arm)
    confirmation = read(Path('data/results/ethical_pilot') / CONFIRMATION / (arm + '_assessment.json'))
    write_json(output / (arm + '_measurement_status.json'), {
        'development_passed': development_ok, 'validation_passed': validation_ok,
        'stance_run_id': eval_id(arm, phase), 'value_retention_passed': confirmation['passed'],
        'interpretation': 'Retention and model qualification are separate. Valid frozen stance replies retained even when either fails. Final checkpoint fixed before outcomes.'})


def main() -> None:
    require_training_backend()
    generated = Path('data/generated/ethical_stance_sft') / MASTER
    execution_path = generated / 'training_execution.json'
    execution = read(execution_path)
    check_bindings(execution['source_bindings'])
    receipt = read(Path('data/.handoff-receipt.json'))
    if receipt['manifest']['files'].get(str(execution_path.relative_to('data')), {}).get('sha256') != sha(execution_path):
        raise ValueError('Preserve training execution and complete references privately before SFT')
    reference = Path('data/results/ethical_pilot') / CONFIRMATION
    if not (reference / 'REFERENCE_COMPLETED').exists():
        raise ValueError('Complete independent reference before training')
    if read(reference / 'value_reference_freeze.json')['mask_sha256'] != sha(reference / 'value_known_items.jsonl'):
        raise ValueError('Independent value cohort changed')
    output = Path('data/results/ethical_stance_sft') / MASTER
    if output.exists():
        raise FileExistsError('Ablation worker already started; no resume/overwrite')
    # Preflight every future output before allowing either training call.
    for arm in ARMS:
        if ((Path('data/results/ethical_pilot') / retention_id(arm)).exists()
            or (Path('configs/run') / (retention_id(arm) + '.yaml')).exists()):
            raise FileExistsError('Candidate confirmation ID already prepared/started')
        for part in ('results', 'checkpoints'):
            if (Path('data') / part / 'ethical_stance_sft' / train_id(arm)).exists():
                raise FileExistsError('Training ID already started')
        for phase in ('development', 'validation', 'stance', 'unqualified'):
            if (Path('data/results/ethical_pilot') / eval_id(arm, phase)).exists():
                raise FileExistsError('All100 ID already started')
    output.mkdir(parents=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    (output / 'STARTED').write_text(commit + '\n')
    write_json(output / 'execution.json', execution)
    lock = ['flock', '/tmp/sft-drift-cuda-benchmark.lock']
    try:
        for arm in ARMS:
            check_bindings(execution['source_bindings'])
            run = train_id(arm)
            write_json(output / (arm + '_dispatch.json'), {'run_id': run,
                'config_sha': config_sha(load_job(['+run=' + run])), 'source_commit': commit})
            if not execute([*lock, TRAIN_PYTHON, '-u', 'run.py', '+run=' + run], output, 'train/' + arm):
                raise RuntimeError('Training failed; preserve and reassess: ' + arm)
            binding = verify_training(arm)
            write_json(output / (arm + '_training_binding.json'), binding)
            if not execute([TRAIN_PYTHON, '-u', 'scripts/run_replay_weight_confirmation.py', arm],
                           output, 'confirmation/' + arm):
                raise RuntimeError('Confirmation collection failed; preserve and reassess: ' + arm)
            full_surface(arm, binding, output)
        (output / 'COLLECTION_COMPLETED').write_text('Both final models trained, engineering-verified, retention-measured and all100collected. Full agent review/analysis still required; no recipe qualification or scaling follows this marker.\n')
    except BaseException as exc:
        write_json(output / 'worker_failure.json', {'error': repr(exc)})
        raise
    finally:
        (output / 'TERMINAL').write_text('Finite ablation worker ended; inspect operations/failures. No resume.\n')


if __name__ == '__main__':
    main()
