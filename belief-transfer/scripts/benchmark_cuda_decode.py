"""Pinned-stack decode throughput probe. Neutral text, forced length, never eval scores."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback


def main():
    import fcntl

    gpu_lock = Path('/tmp/sft-drift-cuda-benchmark.lock').open('a')
    fcntl.flock(gpu_lock, fcntl.LOCK_EX)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--engine', choices=['dynamic', 'static', 'compiled'], required=True)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--tokens', type=int, default=256)
    args = parser.parse_args()
    root = Path('data/results/ethical_pilot') / args.run_id
    inventory = json.loads(Path('configs/handoff.json').read_text())
    if str(root.relative_to('data')) not in inventory['include_paths']:
        raise ValueError('Register benchmark before execution')
    root.mkdir(parents=True, exist_ok=False)
    (root / 'STARTED').write_text(datetime.now(timezone.utc).isoformat())
    try:
        from belief_transfer.config import load_job, write_resolved_config
        from belief_transfer.inference.model import HFModel, seeded_token_processor
        from transformers import CompileConfig, LogitsProcessorList
        import torch

        job = load_job(['+run=ethics_gpu_development_v1'])
        job.run_id = args.run_id
        write_resolved_config(job, root)
        hf = HFModel(job.pilot_bench.model, job.models, enable_thinking=True)
        hf._ensure_loaded()
        model, tokenizer = hf._hf_model, hf._tokenizer
        assert all(p.device.type == 'cuda' for p in model.parameters())
        prompts = [f'Inventory item {i}. Describe how to organize this collection in a clear, detailed explanation. '
                   + 'The shelf contains a blue notebook, a wooden ruler, a plain folder, and a glass paperweight. '
                   * (3 + i % 4) for i in range(args.batch_size)]
        rendered = [tokenizer.apply_chat_template([{'role': 'user', 'content': p}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=True) for p in prompts]
        encoded = tokenizer(rendered, return_tensors='pt', padding=True, add_special_tokens=False).to('cuda')
        width = encoded['input_ids'].shape[1]
        seeds = [(42 ^ int(hashlib.sha256(p.encode()).hexdigest()[:8], 16)) & 0xffffffff for p in prompts]
        options = {'top_k': 20, 'top_p': .95, 'min_p': 0}
        settings = dict(max_new_tokens=args.tokens, min_new_tokens=args.tokens,
            do_sample=False, temperature=1., top_p=1., top_k=0, use_cache=True,
            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
        # Static without compilation isolates cache allocation effects. Compiled
        # uses the same static cache with HF's compiled model-forward path.
        if args.engine != 'dynamic':
            settings['cache_implementation'] = 'static'
            settings['disable_compile'] = args.engine == 'static'
        if args.engine == 'compiled':
            settings['compile_config'] = CompileConfig(mode='reduce-overhead', fullgraph=True)
        (root / 'request.json').write_text(json.dumps({'args': vars(args), 'prompts': prompts,
            'rendered': rendered, 'input_ids': encoded['input_ids'].tolist(),
            'attention_mask': encoded['attention_mask'].tolist(), 'seeds': seeds,
            'decoder': options | {'temperature': .6, 'thinking': True},
            'force_length': True, 'purpose': 'Operational throughput; never belief observations'}, indent=2))
        trials, responses = [], []
        for trial in range(3):
            processor = seeded_token_processor(seeds, width, .6, options)
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            begin = time.perf_counter()
            with torch.inference_mode():
                output = model.generate(**encoded, **settings,
                    logits_processor=LogitsProcessorList([processor]))
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - begin
            generated = output[:, width:].tolist()
            count = sum(map(len, generated))
            rows = [{'trial': trial, 'index': i, 'output_token_ids': ids,
                     'text': tokenizer.decode(ids, skip_special_tokens=False)} for i, ids in enumerate(generated)]
            responses.extend(rows)
            record = {'trial': trial, 'cold': trial == 0, 'elapsed_s': elapsed,
                'generated_tokens': count, 'aggregate_tokens_per_second': count / elapsed,
                'batch_decode_steps_per_second': args.tokens / elapsed,
                'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
                'compiled_call_present': getattr(model, '_compiled_call', None) is not None}
            trials.append(record)
            print(json.dumps(record), flush=True)
            (root / 'trials.json').write_text(json.dumps(trials, indent=2))
            (root / 'responses.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in responses))
            (root / 'responses.md').write_text('# Throughput probe outputs\n\n' + '\n\n'.join(
                f'## Trial {r["trial"]}, row {r["index"]}\n\n```json\n{json.dumps(r)}\n```' for r in responses))
        report = {'args': vars(args), 'trials': trials,
            'steady_aggregate_tokens_per_second': sum(t['generated_tokens'] for t in trials[1:]) / sum(t['elapsed_s'] for t in trials[1:]),
            'torch': torch.__version__, 'cuda': torch.version.cuda,
            'gpu': torch.cuda.get_device_name(0), 'model_revision': getattr(model.config, '_commit_hash', None),
            'attention_implementation': model.config._attn_implementation,
            'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'limitations': ['Forced-length neutral output is not a full-bank runtime estimate.',
                'Compilation/cache changes may change floating-point results; fresh qualification required.']}
        (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        (root / 'summary.md').write_text('# CUDA decode benchmark\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
        (root / 'COMPLETED').write_text(datetime.now(timezone.utc).isoformat())
    except BaseException as error:
        (root / 'failure.json').write_text(json.dumps({'type': type(error).__name__, 'message': str(error),
                                                     'traceback': traceback.format_exc()}, indent=2))
        raise


if __name__ == '__main__':
    main()
