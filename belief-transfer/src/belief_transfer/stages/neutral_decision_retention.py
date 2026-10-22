"""CUDA-only, hash-bound supplemental decision bank through JobConfig -> RunResult."""
from __future__ import annotations

import asyncio
import hashlib
from importlib.metadata import version
import json

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT, build_result, code_revision, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals.neutral_decision_retention import assess, summarize
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info, require_training_backend
from belief_transfer.inference.local import local_model
from belief_transfer.stages.control_recheck import start_directory


def observation(row: dict, reply: tuple[str, dict], tokenizer, *, revision: str, adapter: bool) -> dict:
    backend_text, meta = reply
    tokens = meta.get('output_token_ids', [])
    identity = (meta.get('model_revision') == revision
                and meta.get('adapter_lora_id') == (1 if adapter else None)
                and meta.get('input_token_ids') == row['expected_input_token_ids']
                and meta.get('sampling_seed') == row['seed']
                and meta.get('generation_tokens') == len(tokens))
    error = str(meta['backend_error']) if meta.get('backend_error') else None
    if not identity:
        error = 'DECISION_REQUEST_IDENTITY_MISMATCH'
    terminal = bool(tokens) and tokens[-1] == tokenizer.eos_token_id and meta.get('finish_reason') == 'stop'
    raw = tokenizer.decode(tokens[:-1] if terminal else tokens, skip_special_tokens=False)
    return {**row, 'response': raw, 'backend_text': backend_text, 'generation_metadata': meta,
            'response_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'error': error,
            'assessment': assess(raw, row, normal_stop=terminal and not error)}


async def run(job):
    require_training_backend()
    spec, bench = job.neutral_decision_retention, job.pilot_bench
    if spec is None or job.force or job.smoke or bench.seed != 42:
        raise ValueError('Explicit fresh seed42full decision job required')
    if bench.cuda_generation is None or bench.cuda_generation.engine != 'vllm':
        raise ValueError('Require pinned vLLM backend')
    source = ROOT / spec.bank_path
    raw_bank = source.read_bytes()
    if hashlib.sha256(raw_bank).hexdigest() != spec.bank_sha256:
        raise ValueError('Decision bank changed')
    bank = [json.loads(line) for line in raw_bank.decode().splitlines()]
    if (len(bank) != 64 or len({r['example_id'] for r in bank}) != 64
            or any(sum(r['thinking'] == mode for r in bank) != 32 for mode in (True, False))
            or any(r['expected'] not in {'endorse', 'reject'} for r in bank)):
        raise ValueError('Require unique balanced64-row supplemental bank')
    if bench.adapter_path:
        path = ROOT / bench.adapter_path / 'adapter_model.safetensors'
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec.adapter_sha256:
            raise ValueError('Decision adapter binding changed')
    elif spec.adapter_sha256 is not None:
        raise ValueError('BASE cannot carry adapter hash')
    directory = start_directory(ROOT, job)
    write_resolved_config(job, directory)
    saved = directory / 'bank.jsonl'
    saved.write_bytes(raw_bank)
    write_md(saved)
    manifest = {'version': spec.version, 'model_label': spec.model_label, 'code_revision': code_revision(),
        'bank_sha256': spec.bank_sha256, 'adapter_sha256': spec.adapter_sha256,
        'model': job.models.models[bench.model].model_dump(),
        'backend': backend_info(dtype=job.models.models[bench.model].dtype).model_dump(),
        'generation': bench.cuda_generation.model_dump(), 'decoding': bench.measurement_decoding.model_dump(),
        'nonthinking_temperature': 0.0, 'max_new_tokens': bench.max_new_tokens,
        'batch_size': bench.measurement_batch_size, 'versions': {p: version(p) for p in ('torch', 'transformers', 'vllm')}}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    model = local_model(bench.model, job.models, adapter_path=bench.adapter_path,
        generation=bench.cuda_generation, max_new_tokens=bench.max_new_tokens, seed=42,
        enable_thinking=True, **{k: getattr(bench.measurement_decoding, k) for k in ('top_p', 'top_k', 'min_p')})
    observed = []
    out = directory / 'responses.jsonl'
    try:
        with out.open('x') as stream:
            for mode in (True, False):
                model.enable_thinking = mode
                selected = [r for r in bank if r['thinking'] == mode]
                for offset in range(0, len(selected), bench.measurement_batch_size):
                    batch = selected[offset:offset + bench.measurement_batch_size]
                    try:
                        replies = await asyncio.to_thread(model.generate_batch_with_metadata,
                            [r['prompt'] for r in batch],
                            temperature=bench.measurement_decoding.temperature if mode else 0,
                            seeds=[r['seed'] for r in batch], batch_size=bench.measurement_batch_size)
                        if len(replies) != len(batch):
                            raise ValueError('Incomplete decision backend batch')
                        group = [observation(r, reply, model._tokenizer,
                            revision=bench.cuda_generation.revision, adapter=bool(bench.adapter_path))
                            for r, reply in zip(batch, replies, strict=True)]
                    except Exception as exc:
                        group = [{**r, 'response': None, 'generation_metadata': {'backend_error': str(exc)},
                                  'error': f'{type(exc).__name__}: {exc}',
                                  'assessment': assess(None, r, normal_stop=False)} for r in batch]
                    for row in group:
                        observed.append(row)
                        stream.write(json.dumps(row) + '\n')
                    stream.flush()
                    print(f'[neutral_decision_retention] {spec.model_label} {len(observed)}/64', flush=True)
    finally:
        if out.exists():
            write_md(out)
    summary = summarize(observed)
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    fence = chr(96) * 3
    (directory / 'summary.md').write_text('# Supplemental factual decisions\n\n' + fence + 'json\n' + json.dumps(summary, indent=2) + '\n' + fence + '\n')
    (directory / 'COMPLETED').write_text('All64planned records saved, not a qualification verdict.\n')
    result = build_result(RunContext(), stage=job.stage, experiment_id=job.experiment.id,
        run_id=job.run_id, datapoints=len(observed), metrics=summary, config_sha=config_sha(job),
        artifacts=[p for p in directory.iterdir() if p.is_file() and p.name not in ('STARTED', 'run.log')], root=ROOT)
    write_result(result)
    return result
