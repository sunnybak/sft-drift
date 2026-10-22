"""Forward scoped-validation readout; frozen instrument, all models and all beliefs."""
from __future__ import annotations
import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from run_error_rca import sha, dump
from analyze_scope_controls import split_summary
MASTER = 'ethics_gpu_scoped_readout_v1'
ARMS = ['base', 'positive', 'negative', 'offtopic', 'c4_only']
BANK_SHA = 'c119d2848e3947537145e67f5a401ecda04e530e91a49b85d198f438a77753a6'
POLICY = 'scoped_stance_readout_v1'
PYTHON = '/workspace/sft-drift-vllm/.venv/bin/python'
def run_ids(): return [(a, 'readout', f'ethics_gpu_scoped_readout_{a}_s42_v1') for a in ARMS]
def read(path): return json.loads(Path(path).read_text())
def rows(path): return list(map(json.loads, Path(path).read_text().splitlines()))
def registered():
    paths = [f'{part}/ethical_pilot/{MASTER}' for part in ['generated', 'results']]
    paths += [f'results/ethical_pilot/{run}' for _, _, run in run_ids()]
    declared = read('configs/handoff.json')['include_paths']
    if any(p not in declared for p in paths): raise ValueError('Register every forward readout output first')
    return Path('data/generated/ethical_pilot') / MASTER, Path('data/results/ethical_pilot') / MASTER

def evidence(job, folder: Path, arm: str) -> dict:
    """Identity errors stop execution; performance failures are explicit, not exclusions."""
    if not (folder / 'COMPLETED').exists(): raise ValueError('Scope source is incomplete')
    spec = job.pilot_bench; manifest = read(folder / 'manifest.json')
    if manifest['model_label'] != arm or manifest['model_config'] != job.models.models[spec.model].model_dump(): raise ValueError('Scoped model configuration mismatch')
    if manifest['decoder'] != spec.measurement_decoding.model_dump() or manifest['max_new_tokens'] != spec.max_new_tokens:
        raise ValueError('Scoped decoder mismatch')
    if manifest['generation'] != spec.cuda_generation.model_dump(): raise ValueError('Scoped generation backend mismatch')
    actual_adapter = sha(Path(spec.adapter_path) / 'adapter_model.safetensors') if spec.adapter_path else None
    if actual_adapter != manifest['adapter_sha256']: raise ValueError('Scoped adapter weight mismatch')
    bank = rows(folder / 'bank.jsonl'); observed = rows(folder / 'observations.jsonl')
    if sha(folder / 'bank.jsonl') != manifest['bank_sha256'] or len(bank) != 768: raise ValueError('Scoped bank mismatch')
    expected = {r['presentation_id']: r for r in bank}
    if len(expected) != 768 or Counter(r['presentation_id'] for r in observed) != Counter(expected.keys()): raise ValueError('Scoped response grid mismatch')
    if any(any(r.get(k) != v for k, v in expected[r['presentation_id']].items()) for r in observed): raise ValueError('Changed scoped input fields')
    for r in observed:
        if not r.get('error') and r['correct'] != (r['answer'] == r['expected_word']): raise ValueError('Inconsistent scoped answer score')
    splits = {s: split_summary([r for r in observed if r['split'] == s]) for s in ['development', 'validation']}
    return {'source_run_id': folder.name, 'model_label': arm, 'adapter_sha256': actual_adapter,
            'bank_sha256': manifest['bank_sha256'], 'model_config': manifest['model_config'],
            'backend': manifest['backend'], 'decoder': manifest['decoder'], 'generation': manifest['generation'],
            'max_new_tokens': manifest['max_new_tokens'], 'versions': manifest['versions'],
            'splits': splits, 'scoped_passed': all(s['passed'] for s in splits.values()),
            'sources': {str(folder / name): sha(folder / name) for name in ['manifest.json', 'bank.jsonl', 'observations.jsonl', 'summary.json']}}

def check_config(job):
    b = job.pilot_bench
    if (job.stage != 'pilot_measurements' or job.smoke or job.force or job.replicates != 1 or len(b.targets) != 100
        or b.bank_run_id != 'ethics_100_bank_v3' or [m.name for m in b.measurements] != ['stance']
        or b.seed != 42 or b.stance_validation_run_id is not None or b.measurement_controls_source_run_id is not None
        or b.measurement_control_failure_policy != 'collect_unqualified' or b.measurement_batch_size != 256):
        raise ValueError('Forward readout must collect the full frozen surface and fresh diagnostics')

def prepare():
    import yaml
    from belief_transfer.config import load_job, config_sha
    from belief_transfer.analysis.jsonl_md import write_md
    generated, result = registered()
    if generated.exists() or result.exists(): raise FileExistsError('Forward readout already prepared/started')
    for _, _, run in run_ids():
        if (Path('configs/run') / (run + '.yaml')).exists() or (Path('data/results/ethical_pilot') / run).exists(): raise FileExistsError(run)
    scope_root = Path('data/results/ethical_pilot/ethics_gpu_scope_controls_v1')
    scope_analysis = read(scope_root / 'analysis.json')
    if not scope_analysis['complete']: raise ValueError('Finish all scope audits first')
    for source in scope_analysis['sources']:
        if sha(Path(source['path'])) != source['sha256']: raise ValueError('Published scope evidence changed')
    generated.mkdir(parents=True); proofs = {}; jobs = []; bindings = {}
    for arm, _, run in run_ids():
        scope_run = f'ethics_gpu_scope_control_{arm}_v1'; source = load_job(['+run=' + scope_run])
        overlay = {'defaults': ['ethics_gpu_vllm_base_v1'], 'run_id': run,
            'related_runs': {scope_run: 'Prospective scoped-comprehension evidence for these weights/decoder',
                f'ethics_gpu_retention_rca_{arm}_v2': 'Separate fixed-retention diagnostic; old gates unchanged'},
            'pilot_bench': {'adapter_path': source.pilot_bench.adapter_path, 'seed': 42,
                'stance_validation_run_id': None, 'measurement_controls_source_run_id': None,
                'measurement_control_failure_policy': 'collect_unqualified'}}
        config = Path('configs/run') / (run + '.yaml'); config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        job = load_job(['+run=' + run]); check_config(job)
        proof = evidence(job, Path('data/results/ethical_pilot') / scope_run, arm)
        proofs[arm] = proof; bindings.update(proof['sources']); bindings[str(config)] = sha(config)
        if job.pilot_bench.adapter_path:
            p = Path(job.pilot_bench.adapter_path) / 'adapter_model.safetensors'; bindings[str(p)] = sha(p)
        jobs.append({'arm': arm, 'run_id': run, 'expected_calls': 2432, 'scope_run_id': scope_run, 'adapter_sha256': proof['adapter_sha256'], 'resolved_config_sha': config_sha(job)})
    for name in ['analysis_groups.json', 'plan.json']:
        source = Path('data/generated/ethical_stance_sft/ethics_sft_four_arm_pilot_v1') / name
        target = generated / ('original_pilot_plan.json' if name == 'plan.json' else name)
        target.write_bytes(source.read_bytes()); bindings[str(source)] = sha(source)
    dump(generated / 'scope_evidence.json', proofs)
    (generated / 'scope_evidence.md').write_text('# Scoped evidence\n\n```json\n' + json.dumps(proofs, indent=2) + '\n```\n')
    for f in ['scripts/run_scoped_readout.py', 'scripts/analyze_scoped_readout.py', 'scripts/analyze_scope_controls.py',
              'src/belief_transfer/stages/measurements.py', 'src/belief_transfer/validation/measurements.py',
              'src/belief_transfer/metrics/measurements.py', 'src/belief_transfer/metrics/support_bounds.py',
              'src/belief_transfer/inference/vllm_model.py', 'src/belief_transfer/inference/model.py',
              '../changelog/2026-10-21-scoped-readout-plan.md']:
        bindings[f] = sha(Path(f))
    for f in generated.iterdir():
        if f.is_file(): bindings[str(f)] = sha(f)
    protocol = {'run_id': MASTER, 'policy_id': POLICY, 'jobs': jobs, 'source_bindings': bindings,
        'expected_calls': 12160, 'expected_natural_per_model': 2400, 'measurement_bank_sha': BANK_SHA,
        'no_training': True, 'no_resume': True, 'evaluation_seeds': [42],
        'plan': '../changelog/2026-10-21-scoped-readout-plan.md'}
    dump(generated / 'protocol.json', protocol)
    (generated / 'protocol.md').write_text('# Forward scoped readout\n\n```json\n' + json.dumps(protocol, indent=2) + '\n```\n')
    print(json.dumps(protocol, indent=2))

def validate_runtime(proof, backend, versions):
    if backend != proof['backend']: raise ValueError('Runtime backend differs from scoped evidence')
    if versions != proof['versions']: raise ValueError('Runtime versions differ from scoped evidence')

def check_runtime():
    from belief_transfer.config import load_job, config_sha
    from belief_transfer.inference.backend import backend_info
    from belief_transfer.stages.measurements import prepare as prepare_banks, measurement_bank_fingerprint
    generated, _ = registered(); proofs = read(generated / 'scope_evidence.json')
    protocol = read(generated / 'protocol.json')
    versions = {p: version(p) for p in ['torch', 'transformers', 'vllm']}
    for item in protocol['jobs']:
        arm, run = item['arm'], item['run_id']
        job = load_job(['+run=' + run]); check_config(job)
        if config_sha(job) != item['resolved_config_sha']: raise ValueError('Resolved config changed across preparation/runtime')
        banks, controls, bundle = prepare_banks(job)
        if measurement_bank_fingerprint(bundle) != BANK_SHA or len(banks['stance']) != 2400 or len(controls['stance']) != 32:
            raise ValueError('Runtime frozen instrument identity or coverage changed')
        validate_runtime(proofs[arm], backend_info(dtype=job.models.models[job.pilot_bench.model].dtype).model_dump(), versions)
    print('Runtime model environment matches all scoped sources', flush=True)

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated, result = registered(); protocol = read(generated / 'protocol.json')
    if result.exists(): raise FileExistsError('Started forward worker cannot resume/restart')
    if any(sha(Path(p)) != digest for p, digest in protocol['source_bindings'].items()): raise ValueError('Prepared input/source changed')
    for job in protocol['jobs']:
        if (Path('data/results/ethical_pilot') / job['run_id']).exists(): raise FileExistsError('Readout child already started')
    result.mkdir(parents=True); (result / 'protocol.json').write_bytes((generated / 'protocol.json').read_bytes())
    (result / 'STARTED').write_text(subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True))
    try:
        # A separate process releases any CUDA metadata context before model inference.
        subprocess.run([PYTHON, '-u', __file__, 'check-runtime'], check=True)
        for job in protocol['jobs']:
            command = ['flock', '/tmp/sft-drift-cuda-benchmark.lock', PYTHON, '-u', 'run.py', '+run=' + job['run_id']]
            print('RUN', job['run_id'], flush=True); operation = subprocess.run(command, check=False)
            path = result / 'operations.jsonl'
            with path.open('a') as stream: stream.write(json.dumps({**job, 'command': command, 'returncode': operation.returncode}) + '\n')
            write_md(path)
            if operation.returncode: raise RuntimeError('Readout child failed: ' + job['run_id'])
        (result / 'COMPLETED').write_text('All measurement processes returned0; inspect identities, coverage and diagnostics.\n')
    except BaseException as exc:
        dump(result / 'worker_failure.json', {'error': repr(exc)}); raise
    finally: (result / 'TERMINAL').write_text('Finite worker terminal; no resume.\n')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('operation', choices=['prepare', 'check-runtime', 'run']); args = parser.parse_args()
    {'prepare': prepare, 'check-runtime': check_runtime, 'run': run}[args.operation]()
