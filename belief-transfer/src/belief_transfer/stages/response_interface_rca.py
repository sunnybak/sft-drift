"""CUDA response-interface development canary with immutable explicit inputs."""
from __future__ import annotations
import asyncio
import hashlib
import json
from importlib.metadata import version
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT,build_result,write_result,code_revision
from belief_transfer.config import config_sha,write_resolved_config
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import require_training_backend,backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.response_interface_rca import summarize
from belief_transfer.stages.control_recheck import start_directory
from belief_transfer.validation.response_interface_rca import assess

async def run(job):
    require_training_backend()
    spec=job.response_interface_rca;bench=job.pilot_bench
    if spec is None or job.force or job.smoke:raise ValueError('Explicit fresh full response RCA required')
    path=ROOT/spec.bank_path;raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=spec.bank_sha256:raise ValueError('Response bank changed')
    bank=[json.loads(line) for line in raw.decode().splitlines()]
    expected_rows=spec.expected_rows or 256
    if len(bank)!=expected_rows or len({r['presentation_id'] for r in bank})!=len(bank):raise ValueError(f'Require unique full{expected_rows}row diagnostic bank')
    for r in bank:
        if r['expected_word'] not in r['options'] or hashlib.sha256(r['prompt'].encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Changed prompt/key')
    if bench.adapter_path:
        weight=ROOT/bench.adapter_path/'adapter_model.safetensors'
        if hashlib.sha256(weight.read_bytes()).hexdigest()!=spec.adapter_sha256:raise ValueError('Adapter binding changed')
    elif spec.adapter_sha256 is not None:raise ValueError('BASE cannot carry adapter hash')
    directory=start_directory(ROOT,job);write_resolved_config(job,directory)
    saved=directory/'bank.jsonl';saved.write_bytes(raw);write_md(saved)
    manifest={'version':spec.version,'model_label':spec.model_label,'code_revision':code_revision(),
      'bank_sha256':spec.bank_sha256,'adapter_sha256':spec.adapter_sha256,
      'model_config':job.models.models[bench.model].model_dump(),'backend':backend_info(dtype=job.models.models[bench.model].dtype).model_dump(),
      'decoder':bench.measurement_decoding.model_dump(),'max_new_tokens':bench.max_new_tokens,'generation':bench.cuda_generation.model_dump(),
      'versions':{name:version(name) for name in ['torch','transformers','vllm']},
      'interpretation':spec.task_description or 'New development response-word diagnostic. No historical instrument/extractor/threshold changes.'}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    model=local_model(bench.model,job.models,adapter_path=bench.adapter_path,generation=bench.cuda_generation,
      max_new_tokens=bench.max_new_tokens,seed=bench.seed,enable_thinking=bench.measurement_decoding.thinking,
      **{k:getattr(bench.measurement_decoding,k) for k in ['top_p','top_k','min_p']})
    observed=[];out=directory/'observations.jsonl'
    try:
        with out.open('x') as stream:
            for offset in range(0,len(bank),bench.measurement_batch_size):
                batch=bank[offset:offset+bench.measurement_batch_size]
                try:
                    replies=await asyncio.to_thread(model.generate_batch_with_metadata,[r['prompt'] for r in batch],
                      temperature=bench.measurement_decoding.temperature,seeds=[r['sampling_seed'] for r in batch],batch_size=bench.measurement_batch_size)
                    if len(replies)!=len(batch):raise ValueError('Incorrect response count')
                    group=[{**r,'response':text,'generation_metadata':metadata,**assess(r,text,metadata,thinking=bench.measurement_decoding.thinking)} for r,(text,metadata) in zip(batch,replies,strict=True)]
                except Exception as exc:
                    group=[{**r,'response':None,'answer':None,'correct':False,'strict_format':False,'error':f'backend_batch_error: {type(exc).__name__}: {exc}'} for r in batch]
                for r in group:observed.append(r);stream.write(json.dumps(r)+'\n')
                stream.flush();print(f'[response_interface_rca] {spec.model_label} {len(observed)}/{len(bank)}',flush=True)
    finally:
        if out.exists():write_md(out)
    summary=summarize(observed);summary.update(model_label=spec.model_label)
    if spec.task_description:summary['interpretation']=spec.task_description
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (directory/'summary.md').write_text('# Response-interface development results\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
    (directory/'COMPLETED').write_text('Planned diagnostic calls recorded, not independent qualification.\n')
    artifacts=[p for p in directory.iterdir() if p.is_file() and p.name not in ['run.log','STARTED']]
    result=build_result(RunContext(),stage=job.stage,experiment_id=job.experiment.id,run_id=job.run_id,
      datapoints=len(observed),artifacts=artifacts,metrics=summary,config_sha=config_sha(job),root=ROOT)
    write_result(result);return result
