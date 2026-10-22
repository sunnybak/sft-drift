"""Finite paired thinking-mode diagnostic; all five existing models, no training."""
from __future__ import annotations
import argparse
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_error_rca import sha, dump, write_rows
from run_scoped_readout import ARMS, MASTER as READOUT, PYTHON, validate_runtime
from run_target_free_controls import token_counts
MASTER = 'ethics_gpu_target_free_modes_v1'
MODES = ['thinking','nonthinking']
PLAN = '../changelog/2026-10-21-target-free-modes-plan.md'

def run_ids():
    return [(a,m,f'ethics_gpu_target_free_modes_{a}_{m}_v1') for a in ARMS for m in MODES]

def read(p): return json.loads(Path(p).read_text())
def rows(p): return [json.loads(l) for l in Path(p).read_text().splitlines()]

def registered():
    paths=[f'{part}/ethical_pilot/{MASTER}' for part in ['generated','results']]
    paths += [f'results/ethical_pilot/{r}' for _,_,r in run_ids()]
    if any(p not in read('configs/handoff.json')['include_paths'] for p in paths):
        raise ValueError('Register every mode diagnostic path first')
    return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def prepare():
    import yaml
    from belief_transfer.config import load_job, config_sha
    from belief_transfer.evals.target_free_controls import build_bank
    from belief_transfer.evals.target_free_modes import fresh_contexts
    generated,result=registered()
    if generated.exists() or result.exists(): raise FileExistsError('Mode comparison already prepared/started')
    for _,_,run in run_ids():
        if (Path('configs/run')/(run+'.yaml')).exists() or (Path('data/results/ethical_pilot')/run).exists():
            raise FileExistsError(run)
    reference=Path('data/generated/ethical_pilot')/READOUT/'scope_evidence.json'
    proofs=read(reference)
    old=Path('data/results/ethical_pilot/ethics_gpu_paired_readout_base_s42_v1/stance_controls.jsonl')
    bank=build_bank([r for r in rows(old) if r['answer']!=r['expected']],source_sha256=sha(old),cases=fresh_contexts())
    generated.mkdir(parents=True)
    bindings={str(reference):sha(reference),str(old):sha(old)}
    jobs=[];evidence={};audits={}
    for arm,mode,run in run_ids():
        source=f'ethics_gpu_scope_control_{arm}_v1';label=arm+'_'+mode;proof=proofs[arm]
        overlay={'defaults':[source],'run_id':run,
            'related_runs':{source:'Fixed weights/backend reference; new mode comparison does not requalify historical results'},
            'pilot_bench':{'measurement_decoding':{'thinking':mode=='thinking'}},
            'response_interface_rca':{'model_label':label,'bank_path':str(generated/f'bank_{mode}.jsonl'),
                'bank_sha256':'0'*64,'adapter_sha256':proof['adapter_sha256'],'expected_rows':388,
                'task_description':'Prospective target-free thinking-mode comparison; all five models regardless of performance; no training or own ethical outcomes.'}}
        path=Path('configs/run')/(run+'.yaml')
        path.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
        job=load_job(['+run='+run]);b=job.pilot_bench
        bank_path=generated/f'bank_{mode}.jsonl'
        if not bank_path.exists():
            lengths=token_counts(bank,job)
            if max(lengths)+b.max_new_tokens>b.cuda_generation.max_model_len: raise ValueError('Mode bank exceeds context')
            write_rows(bank_path,[{**r,'expected_input_tokens':n} for r,n in zip(bank,lengths,strict=True)])
            audits[mode]={'min':min(lengths),'max':max(lengths),'rows':len(lengths)}
        overlay['response_interface_rca']['bank_sha256']=sha(bank_path)
        path.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
        job=load_job(['+run='+run]);b=job.pilot_bench
        expected_decoder={**proof['decoder'],'thinking':mode=='thinking'}
        if (job.stage!='response_interface_rca' or job.force or job.smoke or b.seed!=42 or b.measurement_batch_size!=64
            or b.measurement_decoding.model_dump()!=expected_decoder or b.max_new_tokens!=proof['max_new_tokens']
            or b.cuda_generation.model_dump()!=proof['generation'] or job.models.models[b.model].model_dump()!=proof['model_config']):
            raise ValueError('Only thinking mode may differ from pinned runtime')
        if b.adapter_path:
            weight=Path(b.adapter_path)/'adapter_model.safetensors'
            if sha(weight)!=proof['adapter_sha256']: raise ValueError('Adapter identity changed')
            bindings[str(weight)]=sha(weight)
        evidence[label]={k:proof[k] for k in ['model_config','backend','generation','versions','max_new_tokens']}
        evidence[label]['decoder']=expected_decoder
        bindings[str(path)]=sha(path);bindings[str(bank_path)]=sha(bank_path)
        jobs.append({'arm':label,'model_arm':arm,'mode':mode,'run_id':run,'bank_filename':bank_path.name,
                     'adapter_sha256':proof['adapter_sha256'],'resolved_config_sha':config_sha(job),'expected':388})
    for name in ['scripts/run_target_free_modes.py','scripts/analyze_target_free_modes.py','scripts/run_target_free_controls.py',
                 'scripts/analyze_target_free_controls.py','scripts/analyze_interface_controls.py','scripts/run_error_rca.py',
                 'scripts/run_scoped_readout.py','src/belief_transfer/evals/target_free_controls.py','src/belief_transfer/evals/target_free_modes.py',
                 'src/belief_transfer/evals/measurements.py','src/belief_transfer/config.py','src/belief_transfer/schemas.py',
                 'src/belief_transfer/stages/response_interface_rca.py','src/belief_transfer/validation/response_interface_rca.py',
                 'src/belief_transfer/metrics/response_interface_rca.py','src/belief_transfer/inference/model.py',
                 'src/belief_transfer/inference/vllm_model.py','src/belief_transfer/analysis/jsonl_md.py',PLAN]:
        bindings[name]=sha(Path(name))
    protocol={'run_id':MASTER,'jobs':jobs,'source_bindings':bindings,'runtime_evidence':evidence,
              'expected_calls':3880,'token_audit':audits,'no_training':True,'no_resume':True,'plan':PLAN}
    dump(generated/'protocol.json',protocol)
    (generated/'protocol.md').write_text('# Paired mode protocol\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps({'jobs':len(jobs),'expected_calls':3880,'token_audit':audits},indent=2))

def check_runtime():
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.inference.backend import backend_info
    generated,_=registered();protocol=read(generated/'protocol.json')
    versions={p:version(p) for p in ['torch','transformers','vllm']}
    for item in protocol['jobs']:
        job=load_job(['+run='+item['run_id']]);b=job.pilot_bench
        if config_sha(job)!=item['resolved_config_sha']: raise ValueError('Resolved mode config changed')
        validate_runtime(protocol['runtime_evidence'][item['arm']],backend_info(dtype=job.models.models[b.model].dtype).model_dump(),versions)
        bank=rows(generated/item['bank_filename']);lengths=token_counts(bank,job)
        if lengths!=[r['expected_input_tokens'] for r in bank] or max(lengths)+b.max_new_tokens>b.cuda_generation.max_model_len:
            raise ValueError('Mode tokenizer/context changed')
    print('All ten mode configurations and tokenizer/runtime identities verified',flush=True)

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated,result=registered();protocol=read(generated/'protocol.json')
    if result.exists(): raise FileExistsError('Started mode worker cannot resume')
    if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()): raise ValueError('Prepared mode source changed')
    for item in protocol['jobs']:
        if (Path('data/results/ethical_pilot')/item['run_id']).exists(): raise FileExistsError('Mode child already started')
    result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    (result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
    try:
        subprocess.run([PYTHON,'-u',__file__,'check-runtime'],check=True)
        for item in protocol['jobs']:
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock',PYTHON,'-u','run.py','+run='+item['run_id']]
            print('RUN',item['run_id'],flush=True);op=subprocess.run(command,check=False)
            p=result/'operations.jsonl'
            with p.open('a') as out:out.write(json.dumps({**item,'command':command,'returncode':op.returncode})+'\n')
            write_md(p)
            if op.returncode: raise RuntimeError('Mode child execution failed: '+item['run_id'])
        (result/'COMPLETED').write_text('All ten mode jobs recorded; analyze performance separately.\n')
    except BaseException as exc: dump(result/'worker_failure.json',{'error':repr(exc)});raise
    finally: (result/'TERMINAL').write_text('Finite worker terminal; no resume.\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','check-runtime','run']);a=p.parse_args()
    {'prepare':prepare,'check-runtime':check_runtime,'run':run}[a.operation]()
