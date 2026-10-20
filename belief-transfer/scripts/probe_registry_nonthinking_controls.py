"""New mode diagnostic on frozen control prompts; no changed instrument or rescue verdict."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import validate_registry_calibration as original

RUN = 'ethics_gpu_registry_nonthinking_controls_v1'
TRAINS = ['ethics_sft_registry_chat_low_calibration_v1', 'ethics_sft_registry_varied_requests_v1']


def roots() -> tuple[Path, Path]:
    generated, result = [Path('data') / p / 'ethical_pilot' / RUN for p in ['generated', 'results']]
    registry = json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in [generated, result]):
        raise ValueError('Register diagnostic paths before execution')
    return generated, result


def prepare(generated: Path) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    source = Path('data/generated/ethical_pilot/ethics_gpu_registry_varied_requests_validation_v1/control_bank.jsonl')
    generated.mkdir(parents=True, exist_ok=False)
    bank = generated / 'control_bank.jsonl'; bank.write_bytes(source.read_bytes()); write_md(bank)
    protocol = {'run_id': RUN, 'training_run_ids': TRAINS, 'script_sha256': original.sha(Path(__file__)),
                'helper_sha256': original.sha(Path(original.__file__)), 'control_bank_sha256': original.sha(bank),
                'source_path': str(source), 'source_sha256': original.sha(source),
                'decoder': {'thinking': False, 'temperature': .6, 'top_p': .95, 'top_k': 20, 'min_p': 0,
                            'max_new_tokens': 4096, 'seed': 42, 'submission_batch_size': 32},
                'interpretation': 'New unblinded diagnostic,96replies: BASE and2final adapters on unchanged32control prompts and per-item seeds. Only thinking mode and corresponding standard extraction mode change versus original vLLM controls. Frozen thinking measurements remain failed/unchanged. This does not qualify a new ethical instrument, select parameters on belief outcomes, or authorize training.'}
    (generated / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    (generated / 'PROTOCOL.md').write_text('# Nonthinking control diagnostic\n\n```json\n' + json.dumps(protocol, indent=2) + '\n```\n')


def child(generated: Path, result: Path, arm: str) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.inference.local import local_model
    from belief_transfer.validation.measurements import observation_from_reply
    binding = None if arm == 'base' else json.loads((result / 'bindings.json').read_text())[arm]
    if binding is not None:
        original.verify_binding(binding)
    path = result / (arm + '.jsonl')
    if path.exists():
        raise FileExistsError('No diagnostic phase overwrite')
    job = load_job(['+run=ethics_gpu_vllm_base_v1']); spec = job.pilot_bench
    model = local_model(spec.model, job.models, adapter_path=None if binding is None else Path(binding['adapter_path']),
        generation=spec.cuda_generation, max_new_tokens=4096, seed=42, enable_thinking=False, top_p=.95, top_k=20, min_p=0)
    rows = [json.loads(line) for line in (generated / 'control_bank.jsonl').read_text().splitlines()]
    try:
        replies = model.generate_batch_with_metadata([r['prompt'] for r in rows], temperature=.6,
            seeds=[r['seed'] for r in rows], batch_size=32)
        for row, (text, metadata) in zip(rows, replies):
            observed = observation_from_reply(row, text, metadata, thinking=False, seed=row['seed'])
            with path.open('a') as handle:
                handle.write(json.dumps({**observed, 'arm': arm}) + '\n')
        if len(replies) != len(rows):
            raise ValueError('Incomplete diagnostic batch')
        if binding is not None:
            original.verify_binding(binding)
    finally:
        if path.exists():
            write_md(path)


def run(generated: Path, result: Path) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    protocol = json.loads((generated / 'protocol.json').read_text())
    for path, key in [(Path(__file__), 'script_sha256'), (Path(original.__file__), 'helper_sha256'),
                      (generated / 'control_bank.jsonl', 'control_bank_sha256'), (Path(protocol['source_path']), 'source_sha256')]:
        if original.sha(path) != protocol[key]:
            raise ValueError('Changed diagnostic input: ' + str(path))
    bindings = {}
    for train in TRAINS:
        source = Path('data/generated/ethical_stance_sft') / train
        bindings[train] = original.training_binding(json.loads((source / 'plan.json').read_text()),
            Path('data/results/ethical_stance_sft') / train, Path('data/checkpoints/ethical_stance_sft') / train / 'final')
    result.mkdir(parents=True, exist_ok=False)
    (result / 'protocol.json').write_bytes((generated / 'protocol.json').read_bytes())
    (result / 'bindings.json').write_text(json.dumps(bindings, indent=2) + '\n')
    try:
        for arm in ['base', *TRAINS]:
            subprocess.run(['/workspace/sft-drift-vllm/.venv/bin/python', '-u', str(Path(__file__).absolute()), 'child', '--arm', arm], check=True)
        bank = [json.loads(line) for line in (generated / 'control_bank.jsonl').read_text().splitlines()]
        reports = {arm: original.control_report(bank, [json.loads(line) for line in (result / (arm + '.jsonl')).read_text().splitlines()], adapter=arm!='base') for arm in ['base', *TRAINS]}
        import torch
        summary = {'run_id': RUN, 'reports': reports, 'card': torch.cuda.get_device_name(), 'torch_version': torch.__version__, 'interpretation': protocol['interpretation'],
                   'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
        (result / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        (result / 'summary.md').write_text('# Separate mode diagnostic\n\n```json\n' + json.dumps(summary, indent=2) + '\n```\n')
        (result / 'COMPLETED').write_text('Mode diagnostic complete; original qualification unchanged.\n')
    except BaseException as exc:
        (result / 'failure.json').write_text(json.dumps({'error': str(exc), 'traceback': traceback.format_exc()}, indent=2) + '\n'); raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('operation', choices=['prepare', 'run', 'child']); parser.add_argument('--arm', choices=['base', *TRAINS])
    args = parser.parse_args(); generated, result = roots()
    if args.operation == 'prepare':
        prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        if args.operation == 'child':
            if args.arm is None:
                raise ValueError('Child requires an arm')
            child(generated, result, args.arm)
        else:
            import fcntl
            with open('/tmp/sft-drift-cuda-benchmark.lock', 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX); run(generated, result)


if __name__ == '__main__':
    main()
