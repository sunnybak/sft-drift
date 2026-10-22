"""CUDA fixed-bank retention repeats with frozen assessment and known-item mask."""
from __future__ import annotations

import asyncio
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT, build_result, code_revision, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info, require_training_backend
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.instruction_retention import report
from belief_transfer.stages.control_recheck import start_directory
from belief_transfer.evals.instruction_retention import assess


def read_bound(path: Path, digest: str) -> list[dict]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f'Changed retention input: {path.name}')
    return [json.loads(line) for line in raw.decode().splitlines()]


def request_seed(original: int, evaluation: int) -> int:
    """Seed42 reproduces the reference; other seeds change only the request RNG."""
    return (original ^ 42 ^ evaluation) & 0xffffffff


def observation(row: dict, reply: tuple[str, dict], tokenizer, *, evaluation: int,
                revision: str, adapter: bool) -> dict:
    text, metadata = reply
    error = None
    expected_seed = request_seed(row['seed'], evaluation)
    if metadata.get('backend_error'):
        error = 'backend_error: ' + str(metadata['backend_error'])
    elif (metadata.get('model_revision') != revision
          or metadata.get('adapter_lora_id') != (1 if adapter else None)
          or metadata.get('input_token_ids') != row['expected_input_token_ids']
          or metadata.get('sampling_seed') != expected_seed):
        error = 'retention_input_model_adapter_or_seed_identity_mismatch'
    tokens = metadata.get('output_token_ids', [])
    terminal = bool(tokens) and tokens[-1] == tokenizer.eos_token_id and metadata.get('finish_reason') == 'stop'
    raw = tokenizer.decode(tokens[:-1] if terminal else tokens, skip_special_tokens=False)
    score = assess(raw, row, normal_stop=terminal and not error)
    if error:
        # A reply to an unverified request cannot count as a correct known-item answer.
        score.update(semantic_correct=False, exact_answer=False, admissible=False)
    return {**row, 'eval_seed': evaluation, 'request_seed': expected_seed,
            'response': raw, 'backend_text': text, 'generation_metadata': metadata,
            'assessment': score, 'error': error,
            'response_sha256': hashlib.sha256(raw.encode()).hexdigest()}


def failed_observation(row: dict, evaluation: int, exc: Exception) -> dict:
    score = assess('', row, normal_stop=False)
    return {**row, 'eval_seed': evaluation, 'request_seed': request_seed(row['seed'], evaluation),
            'response': None, 'generation_metadata': {'backend_error': str(exc)},
            'assessment': score, 'error': f'backend_batch_error: {type(exc).__name__}: {exc}'}


async def run(job):
    require_training_backend()
    spec, bench = job.instruction_retention, job.pilot_bench
    if spec is None or job.force or job.smoke:
        raise ValueError('A fresh explicit full retention job is required')
    if bench.cuda_generation is None or bench.cuda_generation.engine != 'vllm':
        raise ValueError('Retention RCA requires the pinned vLLM backend')
    if len(set(spec.eval_seeds)) != len(spec.eval_seeds):
        raise ValueError('Repeated evaluation seed')
    bank = read_bound(ROOT / spec.bank_path, spec.bank_sha256)
    if spec.fresh_base_reference and bench.adapter_path:
        raise ValueError('Only BASE may construct a fresh reference')
    known = None if spec.fresh_base_reference else read_bound(ROOT / spec.known_path, spec.known_sha256)
    if len(bank) != 128 or len({r['example_id'] for r in bank}) != 128:
        raise ValueError('Require the unique full128-item frozen retention bank')
    if any(sum(r['thinking'] == mode for r in bank) != 64 for mode in (True, False)):
        raise ValueError('Both fixed retention modes are required')
    # Validate frozen mask identity and coverage before loading weights.
    dummy = [{**r, 'assessment': {k: False for k in ('semantic_correct', 'strict_format',
              'response_boundaries_valid', 'normal_stop')}} for r in bank]
    if known is not None:
        report(dummy, bank, known)
    if bench.adapter_path:
        path = ROOT / bench.adapter_path / 'adapter_model.safetensors'
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec.adapter_sha256:
            raise ValueError('Adapter binding changed')
    elif spec.adapter_sha256 is not None:
        raise ValueError('BASE cannot carry an adapter binding')
    directory = start_directory(ROOT, job)
    write_resolved_config(job, directory)
    inputs = [(spec.bank_path, 'bank.jsonl')]
    if spec.known_path is not None:
        inputs.append((spec.known_path, 'known_items.jsonl'))
    for source, name in inputs:
        target = directory / name
        target.write_bytes((ROOT / source).read_bytes())
        write_md(target)
    manifest = {'model_label': spec.model_label, 'bank_sha256': spec.bank_sha256,
                'known_sha256': spec.known_sha256, 'adapter_sha256': spec.adapter_sha256,
                'code_revision': code_revision(), 'evaluation': spec.model_dump(),
                'model': job.models.models[bench.model].model_dump(),
                'backend': backend_info(dtype=job.models.models[bench.model].dtype).model_dump(),
                'generation': bench.cuda_generation.model_dump(),
                'decoding': bench.measurement_decoding.model_dump(),
                'max_new_tokens': bench.max_new_tokens, 'batch_size': bench.measurement_batch_size,
                'versions': {p: version(p) for p in ('torch', 'transformers', 'vllm')},
                'interpretation': ('Fresh bank: BASE reference selected once from seed42 only; original scoring/gates retained.'
                    if spec.fresh_base_reference else
                    'Fixed historical mask; no re-selection of BASE-known items. Original scoring and gates retained.')}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    model = local_model(bench.model, job.models, adapter_path=bench.adapter_path,
                        generation=bench.cuda_generation, max_new_tokens=bench.max_new_tokens,
                        seed=bench.seed, enable_thinking=True,
                        **{k: getattr(bench.measurement_decoding, k) for k in ('top_p', 'top_k', 'min_p')})
    observed = []
    out = directory / 'responses.jsonl'
    try:
        with out.open('x') as stream:
            for evaluation in spec.eval_seeds:
                for thinking in (True, False):
                    # VLLMModel renders the template per request; token identity below
                    # verifies the exact historical template after every mode switch.
                    model.enable_thinking = thinking
                    selected = [r for r in bank if r['thinking'] == thinking]
                    temperature = bench.measurement_decoding.temperature if thinking else spec.nonthinking_temperature
                    for offset in range(0, len(selected), bench.measurement_batch_size):
                        batch = selected[offset:offset + bench.measurement_batch_size]
                        try:
                            replies = await asyncio.to_thread(model.generate_batch_with_metadata,
                                [r['prompt'] for r in batch], temperature=temperature,
                                seeds=[request_seed(r['seed'], evaluation) for r in batch],
                                batch_size=bench.measurement_batch_size)
                            if len(replies) != len(batch):
                                raise ValueError('Incorrect backend response count')
                        except Exception as exc:
                            group = [failed_observation(r, evaluation, exc) for r in batch]
                        else:
                            group = []
                            for row, reply in zip(batch, replies, strict=True):
                                try:
                                    result = observation(row, reply, model._tokenizer, evaluation=evaluation,
                                        revision=bench.cuda_generation.revision, adapter=bool(bench.adapter_path))
                                except Exception as exc:
                                    result = failed_observation(row, evaluation, exc)
                                    result.update(backend_text=reply[0], generation_metadata=reply[1])
                                group.append(result)
                        for row in group:
                            observed.append(row)
                            stream.write(json.dumps(row) + '\n')
                        stream.flush()
                        print(f'[instruction_retention] {spec.model_label} {len(observed)}/{128 * len(spec.eval_seeds)}', flush=True)
    finally:
        if out.exists():
            write_md(out)
    if spec.fresh_base_reference:
        _, known = report([r for r in observed if r['eval_seed'] == 42], bank, None)
        mask = directory / 'known_items.jsonl'
        mask.write_text(''.join(json.dumps(r) + '\n' for r in known))
        write_md(mask)
    summary = {'model_label': spec.model_label, 'by_seed': {str(seed): report(
        [r for r in observed if r['eval_seed'] == seed], bank, known)[0] for seed in spec.eval_seeds},
        'known_mask_reselected': False, 'expected': 128 * len(spec.eval_seeds),
        'interpretation': manifest['interpretation']}
    if spec.fresh_base_reference:
        summary.update(known_mask_created_from_base_seed=42, known_sha256=hashlib.sha256(
            (directory / 'known_items.jsonl').read_bytes()).hexdigest())
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (directory / 'summary.md').write_text('# Fixed retention repeats\n\n```json\n' + json.dumps(summary, indent=2) + '\n```\n')
    (directory / 'COMPLETED').write_text('All planned responses recorded; inspect failures, not a passing verdict.\n')
    artifacts = [p for p in directory.iterdir() if p.is_file() and p.name not in ('run.log', 'STARTED')]
    result = build_result(RunContext(), stage=job.stage, experiment_id=job.experiment.id,
        run_id=job.run_id, datapoints=len(observed), artifacts=artifacts,
        metrics=summary, config_sha=config_sha(job), root=ROOT)
    write_result(result)
    return result
