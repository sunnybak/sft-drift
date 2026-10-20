"""Prepare or train versioned standalone documents through JobConfig → RunResult."""
from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset.document_sft import load_manifest, tokenize_document, preprocessing_contract
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.model import require_model_cached
from belief_transfer.schemas import JobConfig, RunResult, file_sha

ROOT = Path(__file__).resolve().parents[3]


def verify_training_plan(job: JobConfig, manifest: Path) -> None:
    spec = job.document_sft
    assert spec is not None
    if spec.operation != 'train':
        return
    if not spec.plan_path or not spec.plan_sha256:
        raise ValueError('Treatment training requires a frozen, hashed experiment plan')
    path = ROOT / spec.plan_path
    if file_sha(path, length=64) != spec.plan_sha256:
        raise ValueError('Training plan hash mismatch')
    plan = json.loads(path.read_text())
    required = {'hypothesis', 'falsifier', 'contrasts', 'controls', 'analysis', 'seeds', 'checkpoint_policy'}
    if not required <= plan.keys() or any(not plan[k] for k in required):
        raise ValueError('Incomplete preregistered comparison')
    preprocessing = preprocessing_contract(spec)
    if (plan.get('run_id') != job.run_id or plan.get('dataset_sha256') != file_sha(manifest, length=64)
            or plan.get('training') != job.training.model_dump()
            or plan.get('schedule') != {'max_steps': spec.max_steps, 'save_steps': spec.save_steps}
            or plan.get('preprocessing') != preprocessing):
        raise ValueError('Plan does not match this run, dataset or training configuration')


async def run(job: JobConfig) -> RunResult:
    spec = job.document_sft
    if spec is None or not job.run_id.startswith('ethics_sft_'):
        raise ValueError('Use a dedicated ethics_sft_ document config')
    if job.force:
        raise ValueError('Document runs never overwrite; use a fresh ID')
    if spec.operation == 'smoke' and spec.max_steps > 8:
        raise ValueError('Technical smoke is bounded to eight optimizer steps')
    if spec.operation != 'prepare' and spec.max_length != job.training.sft.max_seq_len:
        raise ValueError('Document and training sequence lengths must agree')
    manifest = ROOT / spec.manifest_path
    verify_training_plan(job, manifest)
    rows = load_manifest(manifest)
    if spec.operation == 'memorize':
        from belief_transfer.benchmarks.document_memory import validate_memory_inputs

        validate_memory_inputs(job, rows)
    output = ROOT / 'data/results' / job.experiment.id / job.run_id
    checkpoint = ROOT / 'data/checkpoints' / job.experiment.id / job.run_id
    if (output.exists() and any(p.name not in {'.hydra', 'run.log'} for p in output.iterdir())) or checkpoint.exists():
        raise FileExistsError('Document stages do not resume/overwrite started runs')
    output.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, output)
    (output / 'STARTED').write_text(config_sha(job) + '\n')
    try:
        from transformers import AutoTokenizer

        require_model_cached(job.model_spec.pretrained)
        revision = {'revision': spec.model_revision} if spec.model_revision is not None else {}
        tokenizer = AutoTokenizer.from_pretrained(job.model_spec.pretrained, local_files_only=True, **revision)
        chunks = [chunk for row in rows for chunk in tokenize_document(
            row, tokenizer, max_length=spec.max_length, synthetic_prefix=spec.synthetic_prefix,
            serialization=spec.serialization)]
        path = output / 'tokenized.jsonl'
        path.write_text(''.join(json.dumps(c) + '\n' for c in chunks))
        write_md(path)
        metrics = {'manifest_sha256': file_sha(manifest, length=64), 'draws': len(rows),
                   'unique_sources': len({r['source_id'] for r in rows}), 'chunks': len(chunks),
                   'loss_tokens': sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks)}
        artifacts = [manifest, path, path.with_suffix('.md')]
        if spec.operation == 'memorize':
            from belief_transfer.benchmarks.document_memory import probe_memory

            metrics['memorization'] = {'base': probe_memory(job, rows, output, adapter=None),
                'protocol': 'Twenty arbitrary lookup codes; exact greedy answers, thinking disabled, 16-token cap',
                'max_base_accuracy': 0.1, 'min_reloaded_accuracy': 0.9}
            if metrics['memorization']['base']['accuracy'] > 0.1:
                (output / 'verification_failure.json').write_text(json.dumps(metrics, indent=2) + '\n')
                raise RuntimeError('Toy mappings are already known by BASE; do not train this check')
        if spec.operation != 'prepare':
            from belief_transfer.training.documents import train_documents

            checkpoint.mkdir(parents=True)
            metrics['training'] = train_documents(job, chunks, checkpoint)
            artifacts.append(checkpoint)
            if metrics['training']['status'] != 'COMPLETED':
                (output / 'verification_failure.json').write_text(json.dumps(metrics, indent=2) + '\n')
                raise RuntimeError('Document training verification failed; preserve this run')
            if spec.operation == 'memorize':
                metrics['memorization']['reloaded'] = probe_memory(job, rows, output, adapter=checkpoint / 'final')
                memory = metrics['memorization']
                losses = [r['loss'] for r in metrics['training']['log_history'] if 'loss' in r]
                memory['loss_decreased'] = len(losses) >= 2 and losses[-1] < losses[0]
                memory['passed'] = (memory['base']['accuracy'] <= 0.1
                    and memory['reloaded']['accuracy'] >= 0.9 and memory['loss_decreased'])
                for name in ('memory_base', 'memory_reloaded'):
                    artifacts.extend([output / f'{name}.jsonl', output / f'{name}.md'])
                if not memory['passed']:
                    (output / 'verification_failure.json').write_text(json.dumps(metrics, indent=2) + '\n')
                    raise RuntimeError('Semantic memorization failed; preserve this run')
        result = build_result(RunContext(), stage='document_sft', experiment_id=job.experiment.id,
                              run_id=job.run_id, datapoints=len(rows), artifacts=artifacts,
                              metrics=metrics, backend=backend_info(dtype=job.model_spec.dtype),
                              config_sha=config_sha(job))
        write_result(result)
        (output / 'summary.json').write_text(json.dumps(metrics, indent=2) + '\n')
        (output / 'summary.md').write_text('# Standalone document stage\n\n```json\n'
                                            + json.dumps(metrics, indent=2) + '\n```\n')
        (output / 'COMPLETED').write_text(config_sha(job) + '\n')
        return result
    except Exception as error:
        (output / 'failure.json').write_text(json.dumps({'type': type(error).__name__, 'message': str(error)}, indent=2) + '\n')
        raise
    finally:
        if checkpoint.exists():
            for path in checkpoint.glob('*.jsonl'):
                write_md(path)
