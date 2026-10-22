"""Finite scoped-comprehension audit; same stance template, fresh explicit facts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from run_error_rca import sha, dump, write_rows
MASTER = 'ethics_gpu_scope_controls_v1'
ARMS = ['base', 'positive', 'negative', 'offtopic', 'c4_only']
DESCRIPTION = ('Prospective explicit-premise scope/negation controls:32contexts,16development and16validation. '
 'Unchanged named stance template; arithmetic and retention remain separate. No historical requalification.')
def run_ids(): return [(arm, 'scope', f'ethics_gpu_scope_control_{arm}_v1') for arm in ARMS]
def registered():
    paths = [f'{part}/ethical_pilot/{MASTER}' for part in ['generated', 'results']]
    paths += [f'results/ethical_pilot/{run}' for _, _, run in run_ids()]
    registry = json.loads(Path('configs/handoff.json').read_text())['include_paths']
    if any(p not in registry for p in paths): raise ValueError('Register all scoped-control outputs before execution')
    return Path('data/generated/ethical_pilot') / MASTER, Path('data/results/ethical_pilot') / MASTER

def prepare():
    import yaml
    from belief_transfer.config import load_job
    from belief_transfer.evals.scope_controls import build_bank
    generated, result = registered()
    if generated.exists() or result.exists(): raise FileExistsError('Scoped audit already prepared/started')
    for _, _, run in run_ids():
        if (Path('configs/run') / (run + '.yaml')).exists() or (Path('data/results/ethical_pilot') / run).exists(): raise FileExistsError(run)
    bank = build_bank()
    if len(bank) != 768 or len({r['presentation_id'] for r in bank}) != 768: raise ValueError('Incomplete scoped factorial')
    generated.mkdir(parents=True); bank_path = generated / 'bank.jsonl'; write_rows(bank_path, bank)
    bindings = {str(bank_path): sha(bank_path)}; jobs = []
    for arm, _, run in run_ids():
        source = load_job(['+run=ethics_gpu_control_recheck_' + arm + '_v2'])
        overlay = {'defaults': ['ethics_gpu_control_recheck_' + arm + '_v2'], 'stage': 'response_interface_rca', 'run_id': run,
            'control_recheck': None, 'response_interface_rca': {'model_label': arm, 'bank_path': str(bank_path), 'bank_sha256': sha(bank_path),
                'adapter_sha256': source.control_recheck.adapter_sha256, 'expected_rows': 768, 'task_description': DESCRIPTION},
            'pilot_bench': {'max_new_tokens': 4096, 'measurement_batch_size': 64,
                'measurement_decoding': {'thinking': True, 'temperature': .6, 'top_p': .95, 'top_k': 20, 'min_p': 0.}}}
        config = Path('configs/run') / (run + '.yaml'); config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        job = load_job(['+run=' + run]); bindings[str(config)] = sha(config)
        jobs.append({'arm': arm, 'run_id': run, 'expected': 768, 'adapter_sha256': job.response_interface_rca.adapter_sha256})
    for f in ['scripts/run_scope_controls.py', 'src/belief_transfer/evals/scope_controls.py', 'src/belief_transfer/evals/measurements.py',
              'src/belief_transfer/stages/response_interface_rca.py', 'src/belief_transfer/validation/response_interface_rca.py',
              'src/belief_transfer/metrics/response_interface_rca.py', 'src/belief_transfer/inference/vllm_model.py',
              '../changelog/2026-10-21-scope-control-plan.md']:
        bindings[f] = sha(Path(f))
    protocol = {'run_id': MASTER, 'jobs': jobs, 'source_bindings': bindings, 'expected_calls': 3840, 'no_training': True,
                'no_resume': True, 'plan': '../changelog/2026-10-21-scope-control-plan.md', 'task_description': DESCRIPTION}
    dump(generated / 'protocol.json', protocol)
    (generated / 'protocol.md').write_text('# Prospective scope-comprehension controls\n\n```json\n' + json.dumps(protocol, indent=2) + '\n```\n')
    print(json.dumps(protocol, indent=2))

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated, result = registered(); protocol = json.loads((generated / 'protocol.json').read_text())
    if result.exists(): raise FileExistsError('Scoped worker started; no restart/resume')
    if any(sha(Path(p)) != digest for p, digest in protocol['source_bindings'].items()): raise ValueError('Prepared source/input changed')
    for job in protocol['jobs']:
        if (Path('data/results/ethical_pilot') / job['run_id']).exists(): raise FileExistsError('Child already started')
    result.mkdir(parents=True); (result / 'protocol.json').write_bytes((generated / 'protocol.json').read_bytes())
    (result / 'STARTED').write_text(subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True))
    try:
        for job in protocol['jobs']:
            command = ['flock', '/tmp/sft-drift-cuda-benchmark.lock', '/workspace/sft-drift-vllm/.venv/bin/python', '-u', 'run.py', '+run=' + job['run_id']]
            print('RUN', job['run_id'], flush=True); operation = subprocess.run(command, check=False)
            path = result / 'operations.jsonl'
            with path.open('a') as stream: stream.write(json.dumps({**job, 'command': command, 'returncode': operation.returncode}) + '\n')
            write_md(path)
            if operation.returncode: raise RuntimeError('Scoped child failed: ' + job['run_id'])
        (result / 'COMPLETED').write_text('All planned calls recorded; inspect both splits and all models.\n')
    except BaseException as exc:
        dump(result / 'worker_failure.json', {'error': repr(exc)}); raise
    finally: (result / 'TERMINAL').write_text('Terminal worker; no resume.\n')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('operation', choices=['prepare', 'run']); args = parser.parse_args()
    prepare() if args.operation == 'prepare' else run()
