"""Finite paired wording diagnostic; requires the parent sweep preserved first."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from importlib.metadata import version

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from build_scope_fact_clarity import MASTER,build_bank
from run_error_rca import sha,dump,write_rows
from run_scoped_readout import ARMS,PYTHON,validate_runtime
from run_target_free_controls import token_counts
from run_target_free_readout_v2 import MASTER as PARENT

PLAN='../changelog/2026-10-22-scope-fact-clarity-v2-plan.md'
DESCRIPTION='Paired original/explicit fact assertions on16reused scope cases;640calls across5fixed models. No independent qualification, ethical outcomes, training or retrospective gate repair.'
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(line) for line in Path(path).read_text().splitlines()]
def run_ids():return [(arm,'clarity',f'ethics_gpu_scope_fact_clarity_{arm}_v2') for arm in ARMS]

def registered():
    paths=[f'{kind}/ethical_pilot/{MASTER}' for kind in ['generated','results']]
    paths += [f'results/ethical_pilot/{run}' for _,_,run in run_ids()]
    if any(p not in read('configs/handoff.json')['include_paths'] for p in paths):
        raise ValueError('Register all clarity paths before preparation')
    return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def parent_preservation(data=Path('data')):
    """A closed GPU process is insufficient: require a verified off-box snapshot."""
    result=data/'results/ethical_pilot'/PARENT
    if not (result/'COMPLETED').exists() or not (result/'TERMINAL').exists() or not (result/'analysis.json').exists():
        raise ValueError('Complete, copy and independently analyze the parent sweep first')
    report=read(result/'analysis.json')
    if not report['complete'] or report['pending'] or set(report['models'])!=set(ARMS):
        raise ValueError('Parent analysis is incomplete')
    protocol=read(data/'generated/ethical_pilot'/PARENT/'protocol.json')
    from run_target_free_readout_v2 import run_ids as parent_ids
    if [(j['arm'],j['seed'],j['run_id']) for j in protocol['jobs']]!=parent_ids():
        raise ValueError('Parent fifteen-job schedule changed')
    receipt=read(data/'.handoff-receipt.json')
    if receipt['repo_id']!=read('configs/handoff.json')['repo_id']:
        raise ValueError('Parent receipt belongs to another artifact store')
    names=[f'results/ethical_pilot/{PARENT}/{name}' for name in ['COMPLETED','TERMINAL','analysis.json','operations.jsonl','cuda_worker.log']]
    names += [f'results/ethical_pilot/{item["run_id"]}/{name}' for item in protocol['jobs']
              for name in ['config.resolved.yaml','measurement_summary.json','measurement_manifest.json',
                           'stance_bank.jsonl','stance_control_bank.jsonl','external_control_bank.jsonl',
                           'stance_observations.jsonl','stance_controls.jsonl']]
    files=receipt['manifest']['files'];verified={}
    for name in names:
        if name not in files or not (data/name).is_file() or sha(data/name)!=files[name]['sha256']:
            raise ValueError('Parent output not preserved in the verified snapshot: '+name)
        verified[name]=files[name]['sha256']
    return {'revision':receipt['revision'],'repo_id':receipt['repo_id'],
        'code_commit':receipt['manifest']['code_commit'],'verified_parent_files':verified},protocol

def prepare():
    import yaml
    from belief_transfer.config import load_job,config_sha
    generated,result=registered()
    if generated.exists() or result.exists():raise FileExistsError('Clarity run already prepared/started')
    preservation,parent=parent_preservation()  # No file mutation before this check.
    for _,_,run in run_ids():
        if (Path('configs/run')/(run+'.yaml')).exists() or (Path('data/results/ethical_pilot')/run).exists():raise FileExistsError(run)
    launch_path=Path('data/generated/ethical_pilot')/PARENT/'launch_receipt.json'
    adapters=read(launch_path)['adapter_config_hashes']  # Validate required provenance before writing.
    source=Path('data/generated/ethical_pilot')/PARENT/'control_bank.jsonl'
    bank=build_bank(rows(source),source_sha256=sha(source))
    base=load_job(['+run=ethics_gpu_scope_control_base_v1']);lengths=token_counts(bank,base)
    if len(bank)!=128 or max(lengths)+base.pilot_bench.max_new_tokens>base.pilot_bench.cuda_generation.max_model_len:
        raise ValueError('Clarity factorial/context budget changed')
    for row,count in zip(bank,lengths,strict=True):row['expected_input_tokens']=count
    generated.mkdir(parents=True);bank_path=generated/'bank.jsonl';write_rows(bank_path,bank)
    dump(generated/'parent_preservation.json',preservation)
    bindings={str(source):sha(source),str(bank_path):sha(bank_path),str(generated/'parent_preservation.json'):sha(generated/'parent_preservation.json')}
    proofs=parent['runtime_evidence'];jobs=[]
    bindings[str(launch_path)]=sha(launch_path)
    for arm,_,run in run_ids():
        source_job=load_job(['+run=ethics_gpu_scope_control_'+arm+'_v1']);b=source_job.pilot_bench;proof=proofs[arm]
        digest=None
        if b.adapter_path:
            weight=Path(b.adapter_path)/'adapter_model.safetensors';digest=sha(weight);bindings[str(weight)]=digest
            config_path=Path(b.adapter_path)/'adapter_config.json'
            if sha(config_path)!=adapters[str(config_path)]:raise ValueError('Parent adapter configuration changed')
            bindings[str(config_path)]=sha(config_path)
        expected=next(j['adapter_sha256'] for j in parent['jobs'] if j['arm']==arm)
        if digest!=expected:raise ValueError('Parent weights changed')
        overlay={'defaults':['ethics_gpu_scope_control_'+arm+'_v1'],'run_id':run,
            'related_runs':{PARENT:'Completed source sweep; original failures remain unchanged'},
            'response_interface_rca':{'model_label':arm,'bank_path':str(bank_path),'bank_sha256':sha(bank_path),
                'adapter_sha256':digest,'expected_rows':128,'task_description':DESCRIPTION}}
        config_path=Path('configs/run')/(run+'.yaml');config_path.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
        job=load_job(['+run='+run]);check_config(job,proof)
        bindings[str(config_path)]=sha(config_path)
        jobs.append({'arm':arm,'run_id':run,'adapter_path':b.adapter_path,'adapter_sha256':digest,'resolved_config_sha':config_sha(job)})
    for name in ['scripts/build_scope_fact_clarity.py','scripts/run_scope_fact_clarity.py','scripts/analyze_scope_fact_clarity.py',
        'scripts/run_error_rca.py','scripts/run_scoped_readout.py','scripts/run_target_free_controls.py','scripts/run_target_free_readout_v2.py',
        'src/belief_transfer/stages/response_interface_rca.py','src/belief_transfer/validation/response_interface_rca.py',
        'src/belief_transfer/validation/measurements.py','src/belief_transfer/metrics/response_interface_rca.py',
        'src/belief_transfer/stages/measurements.py','src/belief_transfer/stages/control_recheck.py',
        'src/belief_transfer/analysis/report.py','src/belief_transfer/analysis/jsonl_md.py','src/belief_transfer/metrics/measurements.py',
        'src/belief_transfer/evals/measurements.py','src/belief_transfer/evals/target_free_readout.py',
        'src/belief_transfer/evals/target_free_modes.py','src/belief_transfer/evals/target_free_controls.py',
        'src/belief_transfer/inference/vllm_model.py','src/belief_transfer/inference/model.py',
        'src/belief_transfer/config.py','src/belief_transfer/schemas.py',PLAN]:bindings[name]=sha(Path(name))
    protocol={'run_id':MASTER,'jobs':jobs,'source_bindings':bindings,'runtime_evidence':proofs,
        'expected_calls':640,'bank_sha256':sha(bank_path),'token_lengths':lengths,'no_training':True,
        'no_resume':True,'parent':PARENT,'plan':PLAN,'parent_snapshot_revision':preservation['revision']}
    dump(generated/'protocol.json',protocol)
    (generated/'protocol.md').write_text('# Paired fact-clarity diagnostic\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps({'run_id':MASTER,'calls':640,'rows_per_model':128,'max_input_tokens':max(lengths)}))

def check_config(job,proof):
    b=job.pilot_bench
    if (job.stage!='response_interface_rca' or job.force or job.smoke or job.replicates!=1 or b.seed!=42 or b.measurement_batch_size!=64
        or job.response_interface_rca.expected_rows!=128 or b.cuda_generation.presence_penalty is not None
        or job.models.models[b.model].model_dump()!=proof['model_config']
        or b.measurement_decoding.model_dump()!=proof['decoder'] or b.cuda_generation.model_dump()!=proof['generation']
        or b.max_new_tokens!=proof['max_new_tokens']):raise ValueError('Clarity must preserve parent runtime/decoder')

def check_runtime():
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.inference.backend import backend_info
    generated,_=registered();protocol=read(generated/'protocol.json');bank=rows(generated/'bank.jsonl')
    versions={p:version(p) for p in ['torch','transformers','vllm']}
    for item in protocol['jobs']:
        job=load_job(['+run='+item['run_id']]);check_config(job,protocol['runtime_evidence'][item['arm']])
        if config_sha(job)!=item['resolved_config_sha'] or job.run_id!=item['run_id']:raise ValueError('Clarity config changed')
        validate_runtime(protocol['runtime_evidence'][item['arm']],backend_info(dtype=job.models.models[job.pilot_bench.model].dtype).model_dump(),versions)
    if token_counts(bank,job)!=protocol['token_lengths']:raise ValueError('Clarity tokenizer changed')
    print('All5clarity configs/runtime/tokenizer verified',flush=True)

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated,result=registered();protocol=read(generated/'protocol.json')
    if result.exists():raise FileExistsError('Started clarity run cannot resume')
    if not (Path('data/results/ethical_pilot')/PARENT/'COMPLETED').exists() or not (Path('data/results/ethical_pilot')/PARENT/'TERMINAL').exists():
        raise ValueError('Parent worker must finish first')
    for item in protocol['jobs']:
        if (Path('data/results/ethical_pilot')/item['run_id']).exists():raise FileExistsError('Clarity child already started')
    if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()):raise ValueError('Prepared clarity source changed')
    result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    (result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
    try:
        subprocess.run([PYTHON,'-u',__file__,'check-runtime'],check=True)
        for item in protocol['jobs']:
            if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()):raise ValueError('Clarity source changed during execution')
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock',PYTHON,'-u','run.py','+run='+item['run_id']]
            operation=subprocess.run(command,check=False);p=result/'operations.jsonl'
            with p.open('a') as out:out.write(json.dumps({**item,'command':command,'returncode':operation.returncode})+'\n')
            write_md(p)
            if operation.returncode:raise RuntimeError('Clarity child failed: '+item['run_id'])
            from analyze_scope_fact_clarity import inspect_model
            inspect_model(Path('data'),item,protocol)
        (result/'COMPLETED').write_text('All640diagnostic calls recorded; no qualification or training approval.\n')
    except BaseException as exc:dump(result/'worker_failure.json',{'error':repr(exc)});raise
    finally:(result/'TERMINAL').write_text('Finite paired diagnostic terminal; no resume.\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','check-runtime','run']);a=p.parse_args()
    {'prepare':prepare,'check-runtime':check_runtime,'run':run}[a.operation]()
