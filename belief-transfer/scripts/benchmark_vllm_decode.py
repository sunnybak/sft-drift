"""Isolated vLLM throughput probe over the exact pinned-stack tokenized neutral inputs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
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
    parser.add_argument('--batch-size', type=int, required=True)
    parser.add_argument('--tokens', type=int, default=256)
    parser.add_argument('--trials', type=int, default=3, choices=range(1, 4))
    parser.add_argument('--lora-support', action='store_true')
    parser.add_argument('--input-tokens', type=int)
    args = parser.parse_args()
    root = Path('data/results/ethical_pilot') / args.run_id
    if str(root.relative_to('data')) not in json.loads(Path('configs/handoff.json').read_text())['include_paths']:
        raise ValueError('Register benchmark before execution')
    root.mkdir(parents=True, exist_ok=False)
    (root / 'STARTED').write_text(datetime.now(timezone.utc).isoformat())
    try:
        import torch
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer
        from vllm import LLM, SamplingParams

        source = Path('data/results/ethical_pilot/ethics_gpu_decode_dynamic_b8_v1/request.json')
        request = json.loads(source.read_text())
        # Remove left padding using saved attention masks, without retokenizing.
        panel = [[token for token, keep in zip(ids, mask) if keep]
                 for ids, mask in zip(request['input_ids'], request['attention_mask'])]
        revision = '1cfa9a7208912126459214e8b04321603b3df60c'
        weights = snapshot_download('Qwen/Qwen3-4B', revision=revision, local_files_only=True)
        if args.input_tokens is not None:
            tokenizer = AutoTokenizer.from_pretrained(weights, local_files_only=True)
            filler = tokenizer.encode(' Inventory.', add_special_tokens=False)
            if not filler or any(len(ids) > args.input_tokens for ids in panel):
                raise ValueError('Capacity extension never truncates source input')
            panel = [(ids + filler * ((args.input_tokens - len(ids) + len(filler) - 1) // len(filler)))[:args.input_tokens]
                     for ids in panel]
        inputs = [{'prompt_token_ids': panel[i % len(panel)]} for i in range(args.batch_size)]
        seeds = [request['seeds'][i % len(panel)] for i in range(args.batch_size)]
        params = [SamplingParams(temperature=.6, top_p=.95, top_k=20, min_p=0,
                  seed=seed, min_tokens=args.tokens, max_tokens=args.tokens) for seed in seeds]
        engine_options = dict(model=weights, tokenizer=weights, dtype='bfloat16',
            tensor_parallel_size=1, max_model_len=4352, max_num_seqs=args.batch_size,
            max_num_batched_tokens=8192, gpu_memory_utilization=.85,
            enable_prefix_caching=False, enable_chunked_prefill=True,
            enforce_eager=False, generation_config='vllm', seed=42)
        if args.lora_support:
            engine_options.update(enable_lora=True, max_lora_rank=64)
        (root / 'request.json').write_text(json.dumps({'args': vars(args),
            'source_request': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'inputs': inputs, 'seeds': seeds, 'engine': engine_options,
            'sampling': {'temperature': .6, 'top_p': .95, 'top_k': 20, 'min_p': 0,
                         'min_tokens': args.tokens, 'max_tokens': args.tokens},
            'sampler_backend': 'vllm-per-request-v1',
            'purpose': 'Neutral forced-length operational benchmark; not ethical eval responses'}, indent=2))
        loading = time.perf_counter()
        llm = LLM(**engine_options)
        load_seconds = time.perf_counter() - loading
        trials, responses = [], []
        for trial in range(args.trials):
            torch.cuda.synchronize()
            start = time.perf_counter()
            results = llm.generate(inputs, params, use_tqdm=False)
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - start
            outputs = [list(r.outputs[0].token_ids) for r in results]
            if len(outputs) != args.batch_size or any(len(x) != args.tokens for x in outputs):
                raise RuntimeError('Incomplete forced-length probe')
            count = sum(map(len, outputs))
            record = {'trial': trial, 'cold_generate': trial == 0, 'elapsed_s': elapsed,
                      'generated_tokens': count, 'aggregate_tokens_per_second': count / elapsed}
            trials.append(record)
            responses.extend({'trial': trial, 'index': i, 'output_token_ids': ids,
                              'text': results[i].outputs[0].text,
                              'finish_reason': results[i].outputs[0].finish_reason} for i, ids in enumerate(outputs))
            print(json.dumps(record), flush=True)
            (root / 'trials.json').write_text(json.dumps(trials, indent=2))
            (root / 'responses.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in responses))
            (root / 'responses.md').write_text('# vLLM throughput outputs\n\n' + '\n\n'.join(
                f'## Trial {r["trial"]}, row {r["index"]}\n\n```json\n{json.dumps(r)}\n```' for r in responses))
        report = {'args': vars(args), 'trials': trials, 'engine_load_seconds': load_seconds,
            'steady_aggregate_tokens_per_second': (sum(t['generated_tokens'] for t in trials[1:]) / sum(t['elapsed_s'] for t in trials[1:])) if len(trials) > 1 else None,
            'all_requested_tokens_generated': all(t['generated_tokens'] == args.batch_size * args.tokens for t in trials),
            'versions': {p: importlib.metadata.version(p) for p in ('vllm', 'torch', 'transformers')},
            'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0),
            'model_revision': revision, 'sampler_backend': 'vllm-per-request-v1',
            'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'limitations': ['Forced-length neutral text; full-bank runtime and long-tail scheduling not measured.',
                'Same probability settings, different RNG implementation from torch-per-row-v1.',
                'New backend requires capacity, adapter and control qualification before measurement.']}
        (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        (root / 'summary.md').write_text('# vLLM decode benchmark\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
        (root / 'COMPLETED').write_text(datetime.now(timezone.utc).isoformat())
        print(json.dumps(report), flush=True)
    except BaseException as error:
        (root / 'failure.json').write_text(json.dumps({'type': type(error).__name__, 'message': str(error),
                                                     'traceback': traceback.format_exc()}, indent=2))
        raise


if __name__ == '__main__':
    main()
