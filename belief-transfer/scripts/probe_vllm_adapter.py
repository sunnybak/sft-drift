"""Neutral technical adapter reload/generation probe, never a study fine-tune result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


def main():
    import fcntl

    gpu_lock = Path('/tmp/sft-drift-cuda-benchmark.lock').open('a')
    fcntl.flock(gpu_lock, fcntl.LOCK_EX)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--adapter', required=True)
    args = parser.parse_args()
    root = Path('data/results/ethical_pilot') / args.run_id
    if str(root.relative_to('data')) not in json.loads(Path('configs/handoff.json').read_text())['include_paths']:
        raise ValueError('Register probe before execution')
    root.mkdir(parents=True, exist_ok=False)
    try:
        from belief_transfer.config import load_job, write_resolved_config
        from belief_transfer.inference.local import local_model
        from belief_transfer.analysis.jsonl_md import write_md

        job = load_job(['+run=ethics_gpu_vllm_development_v1'])
        job.run_id, job.pilot_bench.adapter_path = args.run_id, args.adapter
        job.pilot_bench.max_new_tokens = 256
        write_resolved_config(job, root)
        prompts = ['Compute 17 plus 25. End with the number 42.',
                   'Write one sentence about organizing a bookshelf.',
                   'Return READY as your final answer.',
                   'Write a sentence containing the word blue.']
        seeds = [(42 ^ int(hashlib.sha256(p.encode()).hexdigest()[:8], 16)) & 0xffffffff for p in prompts]
        adapter_file = Path(args.adapter) / 'adapter_model.safetensors'
        (root / 'request.json').write_text(json.dumps({'prompts': prompts, 'seeds': seeds,
            'adapter_path': args.adapter, 'adapter_sha256': hashlib.sha256(adapter_file.read_bytes()).hexdigest(),
            'purpose': 'Technical two-step smoke adapter only; no stance outcomes'}, indent=2))
        p = job.pilot_bench
        model = local_model(p.model, job.models, adapter_path=p.adapter_path,
            generation=p.cuda_generation, max_new_tokens=p.max_new_tokens, seed=42,
            enable_thinking=True, top_k=20, top_p=.95, min_p=0)
        start = time.perf_counter()
        replies = model.generate_batch_with_metadata(prompts, temperature=.6, seeds=seeds, batch_size=4)
        elapsed = time.perf_counter() - start
        rows = [{'id': i, 'response': text, 'generation_metadata': meta}
                for i, (text, meta) in enumerate(replies)]
        path = root / 'responses.jsonl'
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        write_md(path)
        checks = {'all_requests_returned': len(rows) == len(prompts),
            'adapter_confirmed': all(r['generation_metadata'].get('adapter_lora_id') == 1 for r in rows),
            'no_backend_errors': all(not r['generation_metadata'].get('backend_error') for r in rows),
            'normal_stop': all(r['generation_metadata']['finish_reason'] == 'stop' for r in rows)}
        report = {'checks': checks, 'passed': all(checks.values()), 'elapsed_including_load_s': elapsed,
                  'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
        (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        (root / 'summary.md').write_text('# Technical vLLM adapter probe\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
        print(json.dumps(report, indent=2), flush=True)
        if not report['passed']:
            raise RuntimeError('Technical adapter probe failed; preserve results')
    except BaseException as error:
        (root / 'failure.json').write_text(json.dumps({'type': type(error).__name__, 'message': str(error),
                                                     'traceback': traceback.format_exc()}, indent=2))
        raise


if __name__ == '__main__':
    main()
