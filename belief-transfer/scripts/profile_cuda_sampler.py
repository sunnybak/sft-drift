"""Bounded sampler-only timing while an existing measurement is paused in memory.

Does not load weights, edit the measurement, or change its sampler. A separate
watchdog resumes the original process within 60 seconds even if this probe dies.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pause-pid', type=int, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    command = Path(f'/proc/{args.pause_pid}/cmdline').read_bytes().replace(b'\0', b' ').decode()
    if 'run.py' not in command or '+run=ethics_gpu_base_v1' not in command:
        raise ValueError('Expected the currently running BASE Python process')
    root = Path('data/results/ethical_pilot') / args.run_id
    root.mkdir(parents=True, exist_ok=False)
    (root / 'request.json').write_text(json.dumps(vars(args) | {'paused_command': command,
        'iterations': 32, 'batch': 8, 'vocab': 151936, 'synthetic_logits_only': True}, indent=2))
    (root / 'STARTED').write_text(str(time.time()))
    watchdog = subprocess.Popen([sys.executable, '-c',
        f'import os,signal,time; time.sleep(60); os.kill({args.pause_pid},signal.SIGCONT)'],
        start_new_session=True)
    started = time.monotonic()
    paused = False
    report = {}
    try:
        os.kill(args.pause_pid, signal.SIGSTOP)
        paused = True
        # Leave already submitted GPU kernels time to finish before timing this process.
        time.sleep(1)
        import torch
        from transformers import TopKLogitsWarper, TopPLogitsWarper
        from belief_transfer.inference.model import seeded_token_processor

        if not torch.cuda.is_available():
            raise RuntimeError('CUDA required')
        torch.cuda.set_device(0)
        seeds = list(range(42, 50))
        ids = torch.zeros((8, 160), device='cuda', dtype=torch.long)
        generator = torch.Generator(device='cuda').manual_seed(42)
        scores = torch.randn((8, 151936), generator=generator, device='cuda')
        topk, topp = TopKLogitsWarper(20), TopPLogitsWarper(.95)
        scaled = scores / .6
        filtered_k = topk(ids, scaled)
        filtered_p = topp(ids, filtered_k)
        probs = torch.softmax(filtered_p, dim=-1)
        generators = [torch.Generator(device='cuda') for _ in seeds]

        def draws(probabilities, reuse=False):
            choices = []
            for i, seed in enumerate(seeds):
                g = generators[i] if reuse else torch.Generator(device='cuda')
                g.manual_seed(seed)
                choices.append(torch.multinomial(probabilities[i], 1, generator=g))
            return torch.stack(choices)

        reference = seeded_token_processor(seeds, 160, .6, {'top_k': 20, 'top_p': .95})

        def reused_reference():
            p = torch.softmax(topp(ids, topk(ids, scores / .6)), dim=-1)
            return torch.full_like(scores, -float('inf')).scatter(1, draws(p, reuse=True), 0.)

        values, indices = torch.topk(scaled, 20, sorted=True)
        compact_ids = torch.zeros((8, 1), device='cuda', dtype=torch.long)
        compact_probs = torch.softmax(topp(compact_ids, values), dim=-1)

        def compact_pipeline():
            v, ix = torch.topk(scores / .6, 20, sorted=True)
            p = torch.softmax(topp(compact_ids, v), dim=-1)
            return ix.gather(1, draws(p, reuse=True))

        def timing(fn):
            for _ in range(4):
                fn()
            torch.cuda.synchronize()
            begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            t = time.perf_counter()
            begin.record()
            for _ in range(32):
                fn()
            end.record()
            torch.cuda.synchronize()
            return {'wall_ms_per_call': 1000 * (time.perf_counter() - t) / 32,
                    'cuda_elapsed_ms_per_call': begin.elapsed_time(end) / 32}

        with torch.inference_mode():
            matched = bool(torch.equal(reference(ids, scores), reused_reference()))
            phases = {
                'reference_full_processor': lambda: reference(ids, scores),
                'temperature': lambda: scores / .6,
                'top_k': lambda: topk(ids, scaled),
                'top_p_after_top_k_full_vocab': lambda: topp(ids, filtered_k),
                'full_vocab_softmax': lambda: torch.softmax(filtered_p, dim=-1),
                'per_row_multinomial_new_generators': lambda: draws(probs),
                'per_row_multinomial_reused_generators': lambda: draws(probs, reuse=True),
                'full_processor_reused_generators': reused_reference,
                'compact_top20_pipeline_changed_rng_mapping': compact_pipeline,
                'compact_per_row_multinomial': lambda: draws(compact_probs, reuse=True),
            }
            timings = {name: timing(fn) for name, fn in phases.items()}
        report = {'timings': timings, 'reused_generators_match_on_fixture': matched,
                  'compact_is_drop_in_compatible': False,
                  'limitations': ['Synthetic logits; not an end-to-end model benchmark.',
                      'Compaction changes RNG-to-vocabulary mapping, tie handling and reduction order.',
                      'A single matched fixture does not prove full-run equivalence.'],
                  'torch': torch.__version__, 'cuda': torch.version.cuda,
                  'gpu': torch.cuda.get_device_name(0),
                  'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
    except BaseException as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        if paused:
            os.kill(args.pause_pid, signal.SIGCONT)
        watchdog.terminate()
        watchdog.wait()
        report['pause_seconds'] = time.monotonic() - started
        report['original_process_resumed'] = paused
        (root / 'profile.json').write_text(json.dumps(report, indent=2) + '\n')
        (root / 'profile.md').write_text('# Sampler timing probe\n\n```json\n'
                                        + json.dumps(report, indent=2) + '\n```\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
