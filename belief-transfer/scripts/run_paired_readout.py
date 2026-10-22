"""Prospective paired-position readout on fixed pilot weights; no training selection."""
from __future__ import annotations
import argparse
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_error_rca import sha,dump,write_rows
from run_scoped_readout import ARMS,PYTHON,validate_runtime
from run_interface_controls import MASTER as CONTROLS,token_counts
MASTER='ethics_gpu_paired_readout_v1'
SEEDS=[42,7,1729]
BANK_SHA='0f7a9b1f5e50bab6955c51c3686d4cc74706c66a61563a52b1ad4217a1bc6e6a'
POLICY='paired_position_readout_v1'

def read(path):return json.loads(Path(path).read_text())
def rows(path):return list(map(json.loads,Path(path).read_text().splitlines()))
def run_ids():return [(arm,seed,f'ethics_gpu_paired_readout_{arm}_s{seed}_v1') for seed in SEEDS for arm in ARMS]
def registered():
    paths=[f'{part}/ethical_pilot/{MASTER}' for part in ['generated','results']]+[f'results/ethical_pilot/{run}' for _,_,run in run_ids()]
    if any(p not in read('configs/handoff.json')['include_paths'] for p in paths):raise ValueError('Register all paired readout paths first')
    return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def qualification(data=Path('data')):
    folder=data/'results/ethical_pilot'/CONTROLS;p=folder/'analysis.json';report=read(p)
    if not report['complete'] or report['pending'] or set(report['models'])!=set(ARMS) or not report['paired_eligible_for_prospective_readout']:
        raise ValueError('All five paired interface controls must be complete and passed')
    for arm,m in report['models'].items():
        if not m['passed']['paired'] or any(not s['passed'] or not all(s['checks'].values()) for s in m['forms']['paired'].values()) or set(m['forms']['paired'])!={'development','validation'}:
            raise ValueError('Paired domain/split qualification failed: '+arm)
    if len(report['sources'])!=20:raise ValueError('Incomplete paired evidence source manifest')
    for source in report['sources']:
        if sha(Path(source['path']))!=source['sha256']:raise ValueError('Published interface source changed')
    if not (folder/'COMPLETED').exists():raise ValueError('Interface worker is not complete')
    return report,{str(p):sha(p),**{s['path']:s['sha256'] for s in report['sources']}}

def overlay(arm,seed,adapter):
    return {'defaults':['ethics_gpu_vllm_base_v1'],'run_id':f'ethics_gpu_paired_readout_{arm}_s{seed}_v1',
        'related_runs':{f'ethics_gpu_interface_control_{arm}_v1':'Prospective paired known-reference validation for these weights',
            f'ethics_gpu_scoped_readout_{arm}_s42_v1':'Separate independent-endorsement instrument, not interchangeable'},
        'pilot_bench':{'adapter_path':adapter,'seed':seed,'stance_interface':'explicit_positions',
            'stance_validation_run_id':None,'measurement_controls_source_run_id':None,
            'measurement_control_failure_policy':'collect_unqualified'}}

def check_config(job,seed):
    b=job.pilot_bench
    if (job.stage!='pilot_measurements' or job.force or job.smoke or job.replicates!=1 or len(b.targets)!=100
        or b.bank_run_id!='ethics_100_bank_v3' or [(m.name,m.version) for m in b.measurements]!=[('stance','stance-v2')]
        or b.seed!=seed or seed not in SEEDS or b.stance_interface!='explicit_positions' or b.measurement_prompt_style!='concise'
        or b.stance_validation_run_id is not None or b.measurement_controls_source_run_id is not None
        or b.measurement_control_failure_policy!='collect_unqualified' or b.measurement_batch_size!=256):
        raise ValueError('Paired readout requires the full planned interface/grid/decoder layout')

def prepare():
    import yaml
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.stages.measurements import prepare as banks,measurement_bank_fingerprint
    generated,result=registered()
    if generated.exists() or result.exists():raise FileExistsError('Paired master already prepared/started')
    for _,_,run in run_ids():
        if (Path('configs/run')/(run+'.yaml')).exists() or (Path('data/results/ethical_pilot')/run).exists():raise FileExistsError(run)
    report,bindings=qualification()
    reference=read(Path('data/generated/ethical_pilot')/CONTROLS/'protocol.json')
    proofs=reference['runtime_evidence'];jobs=[];generated.mkdir(parents=True)
    for arm,seed,run in run_ids():
        source=load_job(['+run=ethics_gpu_interface_control_'+arm+'_v1']);b=source.pilot_bench
        weight=Path(b.adapter_path)/'adapter_model.safetensors' if b.adapter_path else None
        expected=next(j['adapter_sha256'] for j in reference['jobs'] if j['arm']==arm)
        if (sha(weight) if weight else None)!=expected:raise ValueError('Paired adapter changed')
        if weight:bindings[str(weight)]=sha(weight)
        p=Path('configs/run')/(run+'.yaml');p.write_text('# @package _global_\n'+yaml.safe_dump(overlay(arm,seed,b.adapter_path),sort_keys=False));bindings[str(p)]=sha(p)
        job=load_job(['+run='+run]);check_config(job,seed);b=job.pilot_bench;proof=proofs[arm]
        actual={'model_config':job.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens}
        if any(actual[k]!=proof[k] for k in actual):raise ValueError('Paired model/decoder differs from validation')
        natural,controls,bundle=banks(job)
        if measurement_bank_fingerprint(bundle)!=BANK_SHA or len(natural['stance'])!=2400 or len(controls['stance'])!=32:raise ValueError('Paired content/interface changed')
        if not jobs:
            lengths=token_counts(natural['stance']+controls['stance'],job)
            if max(lengths)+b.max_new_tokens>b.cuda_generation.max_model_len:raise ValueError('Paired inputs exceed context')
            write_rows(generated/'stance_bank.jsonl',natural['stance']);write_rows(generated/'control_bank.jsonl',controls['stance'])
            dump(generated/'token_audit.json',{'lengths':lengths,'min':min(lengths),'max':max(lengths),'tokenizer_revision':b.cuda_generation.revision})
        elif natural['stance']!=rows(generated/'stance_bank.jsonl') or controls['stance']!=rows(generated/'control_bank.jsonl'):raise ValueError('Model/seed-specific prompt bank changed')
        jobs.append({'arm':arm,'seed':seed,'run_id':run,'adapter_sha256':expected,'adapter_path':b.adapter_path,'resolved_config_sha':config_sha(job),'expected_calls':2432})
    for name in ['analysis_groups.json','original_pilot_plan.json']:
        source=Path('data/generated/ethical_pilot/ethics_gpu_scoped_readout_v1')/name
        (generated/name).write_bytes(source.read_bytes());bindings[str(source)]=sha(source)
    for name in ['protocol.json','bank.jsonl']:
        p=Path('data/generated/ethical_pilot')/CONTROLS/name;bindings[str(p)]=sha(p)
    sources=['scripts/run_paired_readout.py','scripts/analyze_paired_readout.py','scripts/run_interface_controls.py','scripts/run_scoped_readout.py','scripts/run_error_rca.py',
        'src/belief_transfer/stages/measurements.py','src/belief_transfer/validation/measurements.py','src/belief_transfer/evals/measurements.py',
        'src/belief_transfer/metrics/measurements.py','src/belief_transfer/metrics/support_bounds.py','src/belief_transfer/inference/vllm_model.py',
        'src/belief_transfer/inference/model.py','src/belief_transfer/config.py','src/belief_transfer/schemas.py','../changelog/2026-10-21-paired-readout-plan.md']
    for name in sources:bindings[name]=sha(Path(name))
    dump(generated/'interface_evidence.json',report)
    for p in generated.iterdir():
        if p.is_file():bindings[str(p)]=sha(p)
    protocol={'run_id':MASTER,'policy_id':POLICY,'jobs':jobs,'source_bindings':bindings,'runtime_evidence':proofs,
        'measurement_bank_sha':BANK_SHA,'evaluation_seeds':SEEDS,'expected_calls':36480,'no_training':True,'no_resume':True,
        'plan':'../changelog/2026-10-21-paired-readout-plan.md'}
    dump(generated/'protocol.json',protocol);(generated/'protocol.md').write_text('# Prospective paired readout\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps({'run_id':MASTER,'jobs':len(jobs),'expected_calls':36480,'bank_sha':BANK_SHA,'max_input_tokens':max(lengths)}))

def check_runtime():
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.inference.backend import backend_info
    from belief_transfer.stages.measurements import prepare as banks,measurement_bank_fingerprint
    generated,_=registered();protocol=read(generated/'protocol.json');versions={p:version(p) for p in ['torch','transformers','vllm']}
    for item in protocol['jobs']:
        job=load_job(['+run='+item['run_id']]);check_config(job,item['seed'])
        if config_sha(job)!=item['resolved_config_sha']:raise ValueError('Resolved paired config changed')
        validate_runtime(protocol['runtime_evidence'][item['arm']],backend_info(dtype=job.models.models[job.pilot_bench.model].dtype).model_dump(),versions)
        natural,controls,bundle=banks(job)
        if measurement_bank_fingerprint(bundle)!=BANK_SHA or natural['stance']!=rows(generated/'stance_bank.jsonl') or controls['stance']!=rows(generated/'control_bank.jsonl'):raise ValueError('Runtime paired bank changed')
    if token_counts(natural['stance']+controls['stance'],job)!=read(generated/'token_audit.json')['lengths']:raise ValueError('Paired tokenizer changed')
    print('All15 paired configs/runtime/banks/token counts verified',flush=True)

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated,result=registered();protocol=read(generated/'protocol.json')
    if result.exists():raise FileExistsError('Started paired worker cannot resume')
    qualification()
    if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()):raise ValueError('Prepared paired sources changed')
    for item in protocol['jobs']:
        if (Path('data/results/ethical_pilot')/item['run_id']).exists():raise FileExistsError('Paired child already started')
    result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes());(result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
    try:
        subprocess.run([PYTHON,'-u',__file__,'check-runtime'],check=True)
        for item in protocol['jobs']:
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock',PYTHON,'-u','run.py','+run='+item['run_id']]
            print('RUN',item['run_id'],flush=True);op=subprocess.run(command,check=False);p=result/'operations.jsonl'
            with p.open('a') as out:out.write(json.dumps({**item,'command':command,'returncode':op.returncode})+'\n')
            write_md(p)
            if op.returncode:raise RuntimeError('Paired child failed: '+item['run_id'])
        (result/'COMPLETED').write_text('All planned measurement calls recorded; inspect coverage and model checks.\n')
    except BaseException as exc:dump(result/'worker_failure.json',{'error':repr(exc)});raise
    finally:(result/'TERMINAL').write_text('Finite worker terminal; no resume.\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','check-runtime','run']);a=p.parse_args();{'prepare':prepare,'check-runtime':check_runtime,'run':run}[a.operation]()
