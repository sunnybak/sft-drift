"""Finite matched retention repeatability audit, no training or new known-item mask."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from run_error_rca import sha, dump
MASTER = 'ethics_gpu_retention_rca_v2'
ARMS = ['base', 'positive', 'negative', 'offtopic', 'c4_only']
def run_ids(): return [(arm, 'retention', f'ethics_gpu_retention_rca_{arm}_v2') for arm in ARMS]
def registered():
    paths = [f'{part}/ethical_pilot/{MASTER}' for part in ['generated', 'results']]
    paths += [f'results/ethical_pilot/{run}' for _, _, run in run_ids()]
    registry = json.loads(Path('configs/handoff.json').read_text())['include_paths']
    if any(p not in registry for p in paths): raise ValueError('Register all retention outputs before execution')
    return Path('data/generated/ethical_pilot') / MASTER, Path('data/results/ethical_pilot') / MASTER

def prepare():
    import yaml
    from belief_transfer.config import load_job
    from belief_transfer.analysis.jsonl_md import write_md
    generated, result = registered()
    if generated.exists() or result.exists(): raise FileExistsError('Prepared/started retention ID')
    for _, _, run in run_ids():
        if (Path('configs/run') / (run + '.yaml')).exists() or (Path('data/results/ethical_pilot') / run).exists(): raise FileExistsError(run)
    bank = Path('data/generated/ethical_pilot/ethics_gpu_instruction_retention_base_v1/bank.jsonl')
    known = Path('data/results/ethical_pilot/ethics_gpu_instruction_retention_base_v1/known_items.jsonl')
    if len(bank.read_text().splitlines()) != 128 or len(known.read_text().splitlines()) != 108: raise ValueError('Wrong frozen retention inputs')
    generated.mkdir(parents=True)
    for source in (bank, known):
        target = generated / source.name; target.write_bytes(source.read_bytes()); write_md(target)
    bindings = {str(bank): sha(bank), str(known): sha(known)}; jobs = []
    for arm, _, run in run_ids():
        source = load_job(['+run=ethics_gpu_control_recheck_' + arm + '_v2'])
        overlay = {'defaults': ['ethics_gpu_control_recheck_' + arm + '_v2'], 'stage': 'instruction_retention', 'run_id': run,
            'control_recheck': None, 'instruction_retention': {'model_label': arm, 'bank_path': str(generated / bank.name),
                'bank_sha256': sha(bank), 'known_path': str(generated / known.name), 'known_sha256': sha(known),
                'adapter_sha256': source.control_recheck.adapter_sha256, 'eval_seeds': [42, 7, 1729], 'nonthinking_temperature': 0},
            'pilot_bench': {'max_new_tokens': 4096, 'measurement_batch_size': 32,
                'measurement_decoding': {'thinking': True, 'temperature': .6, 'top_p': .95, 'top_k': 20, 'min_p': 0.}}}
        config = Path('configs/run') / (run + '.yaml'); config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        job = load_job(['+run=' + run]); bindings[str(config)] = sha(config)
        jobs.append({'arm': arm, 'run_id': run, 'expected': 384, 'adapter_sha256': job.instruction_retention.adapter_sha256})
    files = ['scripts/run_retention_rca.py', 'src/belief_transfer/stages/instruction_retention.py',
        'src/belief_transfer/metrics/instruction_retention.py', 'src/belief_transfer/evals/instruction_retention.py',
        'src/belief_transfer/inference/vllm_model.py', 'src/belief_transfer/dataset/document_sft.py',
        'scripts/build_instruction_replay.py', 'scripts/probe_instruction_retention.py', '../changelog/2026-10-21-retention-rca-plan.md']
    for f in files: bindings[f] = sha(Path(f))
    for name in [bank.name, known.name]: bindings[str(generated / name)] = sha(generated / name)
    protocol = {'run_id': MASTER, 'jobs': jobs, 'source_bindings': bindings, 'expected_calls': 1920,
        'no_training': True, 'no_resume': True, 'known_mask_reselected': False,
        'plan': '../changelog/2026-10-21-retention-rca-plan.md'}
    dump(generated / 'protocol.json', protocol)
    (generated / 'protocol.md').write_text('# Prospective retention audit\n\n```json\n' + json.dumps(protocol, indent=2) + '\n```\n')
    print(json.dumps(protocol, indent=2))

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated, result = registered(); protocol = json.loads((generated / 'protocol.json').read_text())
    if result.exists(): raise FileExistsError('Retention worker started; no restart/resume')
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
            if operation.returncode: raise RuntimeError('Retention child failed: ' + job['run_id'])
        (result / 'COMPLETED').write_text('All planned calls recorded; inspect outcomes.\n')
    except BaseException as exc:
        dump(result / 'worker_failure.json', {'error': repr(exc)}); raise
    finally: (result / 'TERMINAL').write_text('Terminal worker; no resume.\n')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('operation', choices=['prepare', 'run']); args = parser.parse_args()
    prepare() if args.operation == 'prepare' else run()
