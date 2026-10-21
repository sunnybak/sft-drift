"""CUDA-only prospective controls, independent of frozen ethical measurement wording."""
from __future__ import annotations
import asyncio
import hashlib
import json
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT, build_result, write_result, code_revision
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals.control_recheck import build_bank
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info, require_training_backend
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.control_recheck import summarize
from belief_transfer.validation.measurements import observation_from_reply


def start_directory(root:Path,job)->Path:
    directory=root/'data/results'/job.experiment.id/job.run_id
    directory.mkdir(parents=True,exist_ok=False)
    (directory/'STARTED').write_text(config_sha(job)+'\n')
    return directory

async def run(job):
    require_training_backend()
    spec=job.control_recheck
    if spec is None:raise ValueError('Explicit control_recheck configuration required')
    bench=job.pilot_bench
    if job.force or job.smoke:raise ValueError('Recheck requires fresh IDs and full predeclared bank')
    if bench.adapter_path:
        adapter=ROOT/bench.adapter_path/'adapter_model.safetensors'
        if hashlib.sha256(adapter.read_bytes()).hexdigest()!=spec.adapter_sha256:raise ValueError('Adapter differs from bound pilot')
    bank=build_bank(spec.seeds)
    directory=start_directory(ROOT,job)
    write_resolved_config(job,directory)
    artifacts=[]
    bank_path=directory/'control_bank.jsonl'
    bank_path.write_text(''.join(json.dumps(r)+'\n' for r in bank));write_md(bank_path)
    artifacts.extend([bank_path,bank_path.with_suffix('.md')])
    versions={}
    for package in ['torch','transformers','vllm']:
        try:versions[package]=version(package)
        except PackageNotFoundError:versions[package]=None
    manifest={'versions':versions,'model_config':job.models.models[bench.model].model_dump(),'version':spec.version,'model_label':spec.model_label,'bank_sha256':fingerprint(bank),
              'adapter_sha256':spec.adapter_sha256,'code_revision':code_revision(),
              'backend':backend_info(dtype=job.models.models[bench.model].dtype).model_dump(),
              'decoding':bench.measurement_decoding.model_dump(),'max_new_tokens':bench.max_new_tokens,
              'generation':bench.cuda_generation.model_dump() if bench.cuda_generation else None,
              'seeds':spec.seeds,'expected':len(bank),'qualification_policy':'Both expanded forms independently: accuracy>=.95, complete extraction/strict format, matched-note flip<=.05. Legacy checks and independent-repeat noise are reported separately; no ethical-score selection.'}
    path=directory/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n');artifacts.append(path)
    model=local_model(bench.model,job.models,adapter_path=bench.adapter_path,generation=bench.cuda_generation,
        max_new_tokens=bench.max_new_tokens,seed=bench.seed,enable_thinking=bench.measurement_decoding.thinking,
        **{k:getattr(bench.measurement_decoding,k) for k in ['top_p','top_k','min_p'] if getattr(bench.measurement_decoding,k) is not None})
    rows=[];raw=directory/'observations.jsonl'
    try:
        with raw.open('x') as stream:
            for offset in range(0,len(bank),bench.measurement_batch_size):
                batch=bank[offset:offset+bench.measurement_batch_size]
                try:
                    replies=await asyncio.to_thread(model.generate_batch_with_metadata,[r['prompt'] for r in batch],
                        temperature=bench.measurement_decoding.temperature,seeds=[r['sampling_seed'] for r in batch],batch_size=bench.measurement_batch_size)
                    if len(replies)!=len(batch):raise ValueError('Incorrect response count')
                    observed=[observation_from_reply(r,text,metadata,thinking=bench.measurement_decoding.thinking,seed=r['sampling_seed']) for r,(text,metadata) in zip(batch,replies)]
                except Exception as exc:
                    observed=[{**r,'response':None,'answer':None,'strict_format':False,'error':f'{type(exc).__name__}: {exc}'} for r in batch]
                rows.extend(observed)
                for row in observed:stream.write(json.dumps(row)+'\n')
                stream.flush()
                print(f'[control_recheck] {spec.model_label} {len(rows)}/{len(bank)}',flush=True)
    finally:
        if raw.exists():write_md(raw)
    artifacts.extend([raw,raw.with_suffix('.md')])
    summary=summarize(rows);summary.update(model_label=spec.model_label,expected=len(bank),observed=len(rows))
    path=directory/'summary.json';path.write_text(json.dumps(summary,indent=2)+'\n');artifacts.append(path)
    path=directory/'report.md';path.write_text('# Expanded control recheck\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n');artifacts.append(path)
    (directory/'COMPLETED').write_text('All planned calls recorded; not a qualification verdict.\n')
    result=build_result(RunContext(),stage=job.stage,experiment_id=job.experiment.id,run_id=job.run_id,
        datapoints=len(rows),artifacts=artifacts,metrics=summary,config_sha=config_sha(job),root=ROOT)
    write_result(result)
    return result
