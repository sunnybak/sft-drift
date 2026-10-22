"""Finite known-reference interface diagnostic; existing stage and existing weights."""
from __future__ import annotations
import argparse
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_error_rca import sha,dump,write_rows
from run_scoped_readout import ARMS,MASTER as READOUT,PYTHON,validate_runtime
MASTER='ethics_gpu_target_free_controls_v1'
DESCRIPTION='Target-free calibration:64fresh normative/provided-factual/arithmetic contexts with disjoint dev/validation objects, plus4separate reused regression probes. Fresh domain gates only, BASEfirst, no ethical outcomes or historical requalification.'
def run_ids():return [(a,'interface',f'ethics_gpu_target_free_control_{a}_v1') for a in ARMS]
def read(path):return json.loads(Path(path).read_text())
def registered():
    paths=[f'{part}/ethical_pilot/{MASTER}' for part in ['generated','results']]
    paths += [f'results/ethical_pilot/{r}' for _,_,r in run_ids()]
    registry=read('configs/handoff.json')['include_paths']
    if any(p not in registry for p in paths):raise ValueError('Register all interface-control paths first')
    return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def token_counts(bank,job):
    from transformers import AutoTokenizer
    from belief_transfer.inference.model import _apply_chat_template
    b=job.pilot_bench
    t=AutoTokenizer.from_pretrained(job.models.models[b.model].pretrained,revision=b.cuda_generation.revision,local_files_only=True)
    return [len(t.encode(_apply_chat_template(t,[{'role':'user','content':r['prompt']}],enable_thinking=True),add_special_tokens=False)) for r in bank]

def prepare():
    import yaml
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.evals.target_free_controls import build_bank
    generated,result=registered()
    if generated.exists() or result.exists():raise FileExistsError('Target-free diagnostic already prepared/started')
    for _,_,r in run_ids():
        if (Path('configs/run')/(r+'.yaml')).exists() or (Path('data/results/ethical_pilot')/r).exists():raise FileExistsError(r)
    proofs=read(Path('data/generated/ethical_pilot')/READOUT/'scope_evidence.json')
    source=load_job(['+run=ethics_gpu_scope_control_base_v1'])
    regression_source=Path('data/results/ethical_pilot/ethics_gpu_paired_readout_base_s42_v1/stance_controls.jsonl')
    original=[json.loads(l) for l in regression_source.read_text().splitlines()]
    regression=[r for r in original if r['answer']!=r['expected']]
    bank=build_bank(regression,source_sha256=sha(regression_source));lengths=token_counts(bank,source)
    if len(bank)!=388 or len({r['presentation_id'] for r in bank})!=388:raise ValueError('Incomplete interface factorial')
    if max(lengths)+source.pilot_bench.max_new_tokens>source.pilot_bench.cuda_generation.max_model_len:raise ValueError('Target-free bank exceeds pinned context')
    for row,n in zip(bank,lengths,strict=True):row['expected_input_tokens']=n
    generated.mkdir(parents=True);bank_path=generated/'bank.jsonl';write_rows(bank_path,bank)
    bindings={str(bank_path):sha(bank_path),str(regression_source):sha(regression_source)};jobs=[];evidence={}
    for arm,_,run in run_ids():
        scope=f'ethics_gpu_scope_control_{arm}_v1';source=load_job(['+run='+scope]);proof=proofs[arm]
        if source.pilot_bench.adapter_path:
            p=Path(source.pilot_bench.adapter_path)/'adapter_model.safetensors'
            if sha(p)!=proof['adapter_sha256']:raise ValueError('Adapter changed since scoped evidence')
            bindings[str(p)]=sha(p)
        overlay={'defaults':[scope],'run_id':run,'related_runs':{scope:'Exact weight/backend/decoder reference',f'ethics_gpu_scoped_readout_{arm}_s42_v1':'Original frozen all100 readout; no requalification'},
            'response_interface_rca':{'model_label':arm,'bank_path':str(bank_path),'bank_sha256':sha(bank_path),
                'adapter_sha256':proof['adapter_sha256'],'expected_rows':388,'task_description':DESCRIPTION}}
        path=Path('configs/run')/(run+'.yaml');path.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
        job=load_job(['+run='+run]);b=job.pilot_bench
        if job.stage!='response_interface_rca' or job.force or job.smoke or b.measurement_batch_size!=64 or b.seed!=42:raise ValueError('Incorrect diagnostic execution settings')
        evidence[arm]={k:proof[k] for k in ['model_config','backend','decoder','generation','versions','max_new_tokens']}
        if job.models.models[b.model].model_dump()!=proof['model_config'] or b.measurement_decoding.model_dump()!=proof['decoder'] or b.cuda_generation.model_dump()!=proof['generation'] or b.max_new_tokens!=proof['max_new_tokens']:raise ValueError('Diagnostic must retain scoped runtime/decoder')
        bindings[str(path)]=sha(path);jobs.append({'arm':arm,'run_id':run,'adapter_sha256':proof['adapter_sha256'],'resolved_config_sha':config_sha(job),'expected':388})
    for p in [Path('data/generated/ethical_pilot')/READOUT/'scope_evidence.json',
              Path('scripts/run_target_free_controls.py'),Path('scripts/analyze_target_free_controls.py'),
              Path('scripts/analyze_interface_controls.py'),Path('scripts/run_error_rca.py'),Path('scripts/run_scoped_readout.py'),
              Path('src/belief_transfer/config.py'),Path('src/belief_transfer/schemas.py'),Path('src/belief_transfer/analysis/jsonl_md.py'),
              Path('src/belief_transfer/evals/target_free_controls.py'),Path('src/belief_transfer/evals/measurements.py'),
              Path('src/belief_transfer/stages/response_interface_rca.py'),Path('src/belief_transfer/validation/response_interface_rca.py'),
              Path('src/belief_transfer/metrics/response_interface_rca.py'),Path('src/belief_transfer/inference/vllm_model.py'),
              Path('src/belief_transfer/inference/model.py'),Path('../changelog/2026-10-21-target-free-controls-plan.md')]:bindings[str(p)]=sha(p)
    protocol={'run_id':MASTER,'jobs':jobs,'source_bindings':bindings,'runtime_evidence':evidence,'expected_calls':1940,
        'bank_sha256':sha(bank_path),'token_audit':{'min':min(lengths),'max':max(lengths),'rows':len(bank),'tokenizer_revision':source.pilot_bench.cuda_generation.revision},
        'no_training':True,'no_resume':True,'preselected_candidate':'target_free','plan':'../changelog/2026-10-21-target-free-controls-plan.md'}
    dump(generated/'protocol.json',protocol);(generated/'protocol.md').write_text('# Interface-control protocol\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps({'run_id':MASTER,'jobs':jobs,'expected_calls':1940,'token_audit':protocol['token_audit']},indent=2))

def check_runtime():
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.inference.backend import backend_info
    generated,_=registered();protocol=read(generated/'protocol.json');bank=[json.loads(l) for l in (generated/'bank.jsonl').read_text().splitlines()]
    versions={p:version(p) for p in ['torch','transformers','vllm']}
    for item in protocol['jobs']:
        job=load_job(['+run='+item['run_id']]);b=job.pilot_bench
        if config_sha(job)!=item['resolved_config_sha']:raise ValueError('Resolved diagnostic config changed')
        validate_runtime(protocol['runtime_evidence'][item['arm']],backend_info(dtype=job.models.models[b.model].dtype).model_dump(),versions)
    lengths=token_counts(bank,job)
    if lengths!=[r['expected_input_tokens'] for r in bank] or max(lengths)+b.max_new_tokens>b.cuda_generation.max_model_len:raise ValueError('Runtime tokenizer/context changed')
    print('Target-free configs, runtime and tokenizer audit verified',flush=True)

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated,result=registered();protocol=read(generated/'protocol.json')
    if result.exists():raise FileExistsError('Started interface worker cannot resume')
    if not Path('data/results/ethical_pilot/ethics_gpu_paired_readout_v1/operator_stop.json').exists():raise ValueError('Preserve the stopped paired candidate first')
    if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()):raise ValueError('Prepared diagnostic source changed')
    for item in protocol['jobs']:
        if (Path('data/results/ethical_pilot')/item['run_id']).exists():raise FileExistsError('Interface child already started')
    result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes());(result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
    try:
        subprocess.run([PYTHON,'-u',__file__,'check-runtime'],check=True)
        for item in protocol['jobs']:
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock',PYTHON,'-u','run.py','+run='+item['run_id']]
            print('RUN',item['run_id'],flush=True);operation=subprocess.run(command,check=False)
            p=result/'operations.jsonl'
            with p.open('a') as out:out.write(json.dumps({**item,'command':command,'returncode':operation.returncode})+'\n')
            write_md(p)
            if operation.returncode:raise RuntimeError('Interface child failed: '+item['run_id'])
            if item['arm']=='base':
                from analyze_target_free_controls import inspect_model
                baseline=inspect_model(Path('data'),item,protocol)
                if not baseline['passed']:
                    dump(result/'BASE_GATE_FAILED.json',baseline)
                    (result/'BASE_GATE_FAILED.md').write_text('# BASEcalibration failed\n\n```json\n'+json.dumps(baseline,indent=2)+'\n```\n')
                    print('BASEfresh calibration failed; adapter calls not attempted under predeclared rule',flush=True)
                    return
        (result/'COMPLETED').write_text('All5target-free calibrations recorded; inspect every fresh domain/split; no automatic readout/training approval.\n')
    except BaseException as exc:dump(result/'worker_failure.json',{'error':repr(exc)});raise
    finally:(result/'TERMINAL').write_text('Finite diagnostic worker terminal; no resume.\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','check-runtime','run']);a=p.parse_args();{'prepare':prepare,'check-runtime':check_runtime,'run':run}[a.operation]()
