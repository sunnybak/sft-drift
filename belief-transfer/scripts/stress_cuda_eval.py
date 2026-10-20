#!/usr/bin/env python3
"""Bounded capacity check at the frozen evaluation output cap; not belief data."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--batch-size', type=int, default=4)
    args = parser.parse_args()
    if not args.run_id.startswith('ethics_gpu_') or not 1 <= args.batch_size <= 16:
        raise ValueError('Fresh ethics_gpu_ ID and bounded batch 1–16 required')
    from belief_transfer.config import load_job, write_resolved_config
    from belief_transfer.inference.model import HFModel
    import torch

    root = Path('data/results/ethical_pilot') / args.run_id
    if root.exists():
        raise FileExistsError(f'Capacity checks do not resume or overwrite: {root}')
    inventory = json.loads(Path('configs/handoff.json').read_text())
    if str(root.relative_to('data')) not in inventory['include_paths']:
        raise ValueError('Register output before execution')
    job = load_job(['+run=ethics_gpu_development_v1'])
    job.run_id = args.run_id
    root.mkdir(parents=True)
    write_resolved_config(job, root)
    (root / 'STARTED').write_text(datetime.now(timezone.utc).isoformat() + '\n')
    spec = job.pilot_bench
    decode = spec.measurement_decoding
    hf = HFModel(job.training.model, job.models, batch_size=args.batch_size)
    hf._ensure_loaded()
    model, tokenizer = hf._hf_model, hf._tokenizer
    assert all(p.device.type == 'cuda' for p in model.parameters())
    prompts = [
        f'Capacity test item {i}. Explain the following neutral inventory in prose. '
        + 'The shelf holds a blue notebook, a wooden ruler, and a plain folder. ' * 50
        for i in range(args.batch_size)
    ]
    rendered = [tokenizer.apply_chat_template(
        [{'role': 'user', 'content': p}], tokenize=False,
        add_generation_prompt=True, enable_thinking=decode.thinking,
    ) for p in prompts]
    encoded = tokenizer(rendered, return_tensors='pt', padding=True, add_special_tokens=False).to('cuda')
    request = dict(max_new_tokens=spec.max_new_tokens, min_new_tokens=spec.max_new_tokens,
                   do_sample=True, temperature=decode.temperature, top_p=decode.top_p,
                   top_k=decode.top_k, min_p=decode.min_p, use_cache=True,
                   pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
    (root / 'request.json').write_text(json.dumps({
        'prompts': prompts, 'rendered': rendered, 'input_ids': encoded['input_ids'].tolist(),
        'attention_mask': encoded['attention_mask'].tolist(), 'generation': request,
        'purpose': 'Forced-length capacity only; EOS suppressed, never score as belief replies',
    }, indent=2) + '\n')
    torch.manual_seed(42)
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    started = time.perf_counter()
    with torch.inference_mode():
        output = model.generate(**encoded, **request)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    rows = []
    for i, ids in enumerate(output[:, encoded['input_ids'].shape[1]:].tolist()):
        rows.append({'index': i, 'output_token_ids': ids,
                     'text': tokenizer.decode(ids, skip_special_tokens=False)})
    (root / 'responses.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    (root / 'responses.md').write_text('\n\n'.join(
        f'## Item {r["index"]}\n\n```json\n{json.dumps(r, indent=2)}\n```' for r in rows) + '\n')
    peak = torch.cuda.max_memory_allocated()
    total = torch.cuda.get_device_properties(0).total_memory
    info = dict(batch_size=args.batch_size, max_new_tokens=spec.max_new_tokens,
                generated_lengths=[len(r['output_token_ids']) for r in rows],
                input_width=encoded['input_ids'].shape[1], seed=42, elapsed_s=elapsed,
                peak_allocated_bytes=peak, total_vram_bytes=total,
                peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                model_revision=getattr(model.config, '_commit_hash', None),
                gpu=torch.cuda.get_device_name(0), torch_version=str(torch.__version__),
                cuda_runtime=torch.version.cuda,
                code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    info['passed'] = peak <= .85 * total and all(
        n == spec.max_new_tokens for n in info['generated_lengths'])
    (root / 'capacity.json').write_text(json.dumps(info, indent=2) + '\n')
    (root / 'capacity.md').write_text('# Frozen-cap CUDA capacity check\n\n```json\n'
                                        + json.dumps(info, indent=2) + '\n```\n')
    print(json.dumps(info, indent=2), flush=True)
    if not info['passed']:
        raise RuntimeError('Insufficient capacity/headroom; use a fresh ID for another setting')


if __name__ == '__main__':
    main()
