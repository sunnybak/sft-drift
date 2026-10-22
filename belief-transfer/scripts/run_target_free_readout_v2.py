"""Prospective target-free relative-choice readout on fixed pilot weights; no training selection."""
from __future__ import annotations
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_error_rca import sha,dump,write_rows
from run_scoped_readout import ARMS,PYTHON,validate_runtime
from run_target_free_modes import MASTER as CONTROLS
from run_target_free_controls import token_counts
MASTER='ethics_gpu_target_free_readout_v2'
SEEDS=[42,7,1729]
POLICY='target_free_error_budget_v2'

def read(path):return json.loads(Path(path).read_text())
def rows(path):return list(map(json.loads,Path(path).read_text().splitlines()))
def run_ids():return [(arm,seed,f'ethics_gpu_target_free_readout_{arm}_s{seed}_v2') for seed in SEEDS for arm in ARMS]
def review_selection(groups,bank):
    pools={'target':[b for b,g in groups.items() if g['analysis_group']=='target'],
        'other_ethical':[b for b,g in groups.items() if g['analysis_group'] in ['related_untrained','other_untrained_ethical']],
        'offtopic':[b for b,g in groups.items() if g['analysis_group']=='offtopic_eval']}
    result=[]
    for group,ids in pools.items():
        chosen=sorted(ids,key=lambda b:hashlib.sha256(('42:'+b).encode()).hexdigest())[:2]
        if len(chosen)!=2:raise ValueError('Incomplete review group')
        for bid in chosen:
            wording=min(r['wording_id'] for r in bank if r['belief_id']==bid)
            selected=[r for r in bank if r['belief_id']==bid and r['wording_id']==wording]
            if len(selected)!=2:raise ValueError('Review requires both physical orders')
            for seed in [42,7]:
                for arm in (ARMS if seed==42 else ['base']):
                    for row in selected:result.append({'group':group,'belief_id':bid,'wording_id':wording,
                        'arm':arm,'seed':seed,'presentation_id':row['presentation_id'],
                        'selection_rule':'First2 SHA256(42:beliefID) per frozen group; first wording; both orders.'})
    return result
def registered():
    paths=[f'{part}/ethical_pilot/{MASTER}' for part in ['generated','results']]+[f'results/ethical_pilot/{run}' for _,_,run in run_ids()]
    if any(p not in read('configs/handoff.json')['include_paths'] for p in paths):raise ValueError('Register all target-free readout paths first')
    return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def diagnostic_evidence(data=Path('data')):
    from analyze_target_free_controls import inspect_model
    folder=data/'results/ethical_pilot'/CONTROLS;p=folder/'analysis.json';report=read(p)
    if not (folder/'COMPLETED').exists() or not report['complete'] or report['pending']:
        raise ValueError('Complete all ten mode diagnostic jobs before new diagnostic readout')
    protocol_path=data/'generated/ethical_pilot'/CONTROLS/'protocol.json';protocol=read(protocol_path)
    from run_target_free_modes import run_ids as mode_ids
    if ([(j['model_arm'],j['mode'],j['run_id']) for j in protocol['jobs']]!=mode_ids()
        or set(report['models'])!={a+'_'+m for a, m, _ in mode_ids()}):
        raise ValueError('Incomplete five-model/two-mode calibration identity')
    bindings={str(p):sha(p),str(protocol_path):sha(protocol_path)}
    for item in protocol['jobs']:
        rebuilt=inspect_model(data,item,protocol,master=CONTROLS)
        if rebuilt!=report['models'][item['arm']]:
            raise ValueError('Prior diagnostic does not reconstruct: '+item['arm'])
        for source in rebuilt['sources']:
            if sha(Path(source['path']))!=source['sha256']:raise ValueError('Published calibration source changed')
            bindings[source['path']]=source['sha256']
    return report,bindings

def overlay(arm,seed,adapter,control_bank):
    return {'defaults':['ethics_gpu_vllm_base_v1'],'run_id':f'ethics_gpu_target_free_readout_{arm}_s{seed}_v2',
        'related_runs':{f'ethics_gpu_target_free_modes_{arm}_thinking_v1':'Target-free thinking-mode known-reference validation; historical failures remain failed',
            f'ethics_gpu_scoped_readout_{arm}_s42_v1':'Separate independent-endorsement instrument, not interchangeable'},
        'pilot_bench':{'adapter_path':adapter,'seed':seed,'stance_interface':'target_free_positions','stance_profile_version':None,'measurement_batch_size':64,
            'stance_validation_run_id':None,'measurement_controls_source_run_id':None,
            'measurement_control_failure_policy':'collect_unqualified','measurement_control_bank':control_bank}}

def check_config(job,seed):
    b=job.pilot_bench
    if (job.stage!='pilot_measurements' or job.force or job.smoke or job.replicates!=1 or len(b.targets)!=100
        or b.bank_run_id!='ethics_100_bank_v3' or [(m.name,m.version) for m in b.measurements]!=[('stance','stance-v2')]
        or b.seed!=seed or seed not in SEEDS or b.stance_interface!='target_free_positions' or b.measurement_prompt_style!='concise'
        or b.stance_validation_run_id is not None or b.measurement_controls_source_run_id is not None
        or b.measurement_control_bank is None or b.measurement_control_bank.count!=488
        or b.cuda_generation.presence_penalty is not None or not b.measurement_decoding.thinking
        or b.measurement_control_failure_policy!='collect_unqualified' or b.measurement_batch_size!=64 or b.stance_profile_version is not None):
        raise ValueError('Target-free readout requires the full planned interface/grid/decoder layout')

def prepare():
    import yaml
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.stages.measurements import prepare as banks,measurement_bank_fingerprint
    generated,result=registered()
    if generated.exists() or result.exists():raise FileExistsError('Target-free master already prepared/started')
    for _,_,run in run_ids():
        if (Path('configs/run')/(run+'.yaml')).exists() or (Path('data/results/ethical_pilot')/run).exists():raise FileExistsError(run)
    from belief_transfer.evals.target_free_readout import fresh_control_bank,native_stress_controls
    from belief_transfer.metrics.measurements import operational_controls
    report,bindings=diagnostic_evidence()
    reference=read(Path('data/generated/ethical_pilot')/CONTROLS/'protocol.json')
    proofs={a:reference['runtime_evidence'][a+'_thinking'] for a in ARMS};jobs=[];generated.mkdir(parents=True);bank_sha=None
    stress_path=Path('data/generated/ethical_pilot/ethics_gpu_presence_controls_v1/bank.jsonl')
    stress_source=rows(stress_path);bindings[str(stress_path)]=sha(stress_path)
    native_controls=fresh_control_bank()+native_stress_controls(stress_source)
    operational_controls(native_controls,[])  # Validate the complete factorial, not model performance.
    control_path=generated/'control_bank.jsonl';write_rows(control_path,native_controls)
    control_spec={'path':str(control_path),'sha256':sha(control_path),'count':488}
    for arm,seed,run in run_ids():
        source=load_job(['+run=ethics_gpu_target_free_modes_'+arm+'_thinking_v1']);b=source.pilot_bench
        weight=Path(b.adapter_path)/'adapter_model.safetensors' if b.adapter_path else None
        expected=next(j['adapter_sha256'] for j in reference['jobs'] if j['model_arm']==arm and j['mode']=='thinking')
        if (sha(weight) if weight else None)!=expected:raise ValueError('Target-free adapter changed')
        if weight:bindings[str(weight)]=sha(weight)
        p=Path('configs/run')/(run+'.yaml');p.write_text('# @package _global_\n'+yaml.safe_dump(overlay(arm,seed,b.adapter_path,control_spec),sort_keys=False));bindings[str(p)]=sha(p)
        job=load_job(['+run='+run]);check_config(job,seed);b=job.pilot_bench;proof=proofs[arm]
        actual={'model_config':job.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens}
        if any(actual[k]!=proof[k] for k in actual):raise ValueError('Target-free model/decoder differs from validation')
        natural,controls,bundle=banks(job)
        if len(natural['stance'])!=1200 or len(controls['stance'])!=488 or any(r['polarity']!='positive' for r in natural['stance']):raise ValueError('Target-free full100 grid changed')
        actual_sha=measurement_bank_fingerprint(bundle)
        if bank_sha is not None and actual_sha!=bank_sha:raise ValueError('Model-specific bank changed')
        bank_sha=actual_sha
        if not jobs:
            lengths=token_counts(natural['stance']+controls['stance'],job)
            if max(lengths)+b.max_new_tokens>b.cuda_generation.max_model_len:raise ValueError('Target-free inputs exceed context')
            write_rows(generated/'stance_bank.jsonl',natural['stance']);write_rows(generated/'control_bank.jsonl',controls['stance'])
            dump(generated/'token_audit.json',{'lengths':lengths,'min':min(lengths),'max':max(lengths),'tokenizer_revision':b.cuda_generation.revision})
        elif natural['stance']!=rows(generated/'stance_bank.jsonl') or controls['stance']!=rows(generated/'control_bank.jsonl'):raise ValueError('Model/seed-specific prompt bank changed')
        jobs.append({'arm':arm,'seed':seed,'run_id':run,'adapter_sha256':expected,'adapter_path':b.adapter_path,'resolved_config_sha':config_sha(job),'expected_calls':1688})
    for name in ['analysis_groups.json','original_pilot_plan.json']:
        source=Path('data/generated/ethical_pilot/ethics_gpu_scoped_readout_v1')/name
        (generated/name).write_bytes(source.read_bytes());bindings[str(source)]=sha(source)
    write_rows(generated/'review_selection.jsonl',review_selection(read(generated/'analysis_groups.json')['beliefs'],rows(generated/'stance_bank.jsonl')))
    for name in ['protocol.json','bank_thinking.jsonl','bank_nonthinking.jsonl']:
        p=Path('data/generated/ethical_pilot')/CONTROLS/name;bindings[str(p)]=sha(p)
    sources=['scripts/run_target_free_readout_v2.py','scripts/analyze_target_free_readout_v2.py','scripts/analyze_paired_readout.py','scripts/run_target_free_readout.py','scripts/analyze_target_free_readout.py','scripts/run_target_free_controls.py','scripts/run_target_free_modes.py','scripts/analyze_target_free_controls.py','scripts/analyze_interface_controls.py','scripts/run_scoped_readout.py','scripts/run_error_rca.py',
        'src/belief_transfer/stages/measurements.py','src/belief_transfer/validation/measurements.py','src/belief_transfer/evals/measurements.py','src/belief_transfer/evals/target_free_readout.py','src/belief_transfer/evals/target_free_modes.py',
        'src/belief_transfer/metrics/measurements.py','src/belief_transfer/metrics/support_bounds.py','src/belief_transfer/analysis/measurement_report.py','src/belief_transfer/inference/vllm_model.py',
        'src/belief_transfer/inference/model.py','src/belief_transfer/config.py','src/belief_transfer/schemas.py','../changelog/2026-10-21-error-aware-readout-v2-plan.md']
    for name in sources:bindings[name]=sha(Path(name))
    dump(generated/'calibration_evidence.json',report)
    for p in generated.iterdir():
        if p.is_file():bindings[str(p)]=sha(p)
    protocol={'run_id':MASTER,'policy_id':POLICY,'jobs':jobs,'source_bindings':bindings,'runtime_evidence':proofs,
        'measurement_bank_sha':bank_sha,'evaluation_seeds':SEEDS,'expected_calls':25320,'no_training':True,'no_resume':True,
        'plan':'../changelog/2026-10-21-error-aware-readout-v2-plan.md'}
    dump(generated/'protocol.json',protocol);(generated/'protocol.md').write_text('# Prospective target-free readout\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps({'run_id':MASTER,'jobs':len(jobs),'expected_calls':25320,'bank_sha':bank_sha,'max_input_tokens':max(lengths)}))

def check_runtime():
    from belief_transfer.config import load_job,config_sha
    from belief_transfer.inference.backend import backend_info
    from belief_transfer.stages.measurements import prepare as banks,measurement_bank_fingerprint
    generated,_=registered();protocol=read(generated/'protocol.json');versions={p:version(p) for p in ['torch','transformers','vllm']}
    for item in protocol['jobs']:
        job=load_job(['+run='+item['run_id']]);check_config(job,item['seed'])
        if config_sha(job)!=item['resolved_config_sha'] or job.run_id!=item['run_id']:raise ValueError('Resolved target-free config changed')
        validate_runtime(protocol['runtime_evidence'][item['arm']],backend_info(dtype=job.models.models[job.pilot_bench.model].dtype).model_dump(),versions)
        natural,controls,bundle=banks(job)
        if measurement_bank_fingerprint(bundle)!=protocol['measurement_bank_sha'] or natural['stance']!=rows(generated/'stance_bank.jsonl') or controls['stance']!=rows(generated/'control_bank.jsonl'):raise ValueError('Runtime target-free bank changed')
    if token_counts(natural['stance']+controls['stance'],job)!=read(generated/'token_audit.json')['lengths']:raise ValueError('Target-free tokenizer changed')
    print('All15 target-free configs/runtime/banks/token counts verified',flush=True)

def run():
    from belief_transfer.analysis.jsonl_md import write_md
    generated,result=registered();protocol=read(generated/'protocol.json')
    if result.exists():raise FileExistsError('Started target-free worker cannot resume')
    diagnostic_evidence()
    if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()):raise ValueError('Prepared target-free sources changed')
    for item in protocol['jobs']:
        if (Path('data/results/ethical_pilot')/item['run_id']).exists():raise FileExistsError('Target-free child already started')
    result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes());(result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
    try:
        subprocess.run([PYTHON,'-u',__file__,'check-runtime'],check=True)
        for item in protocol['jobs']:
            if any(sha(Path(p))!=v for p,v in protocol['source_bindings'].items()):raise ValueError('Prepared target-free sources changed during execution')
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock',PYTHON,'-u','run.py','+run='+item['run_id']]
            print('RUN',item['run_id'],flush=True);op=subprocess.run(command,check=False);p=result/'operations.jsonl'
            with p.open('a') as out:out.write(json.dumps({**item,'command':command,'returncode':op.returncode})+'\n')
            write_md(p)
            if op.returncode:raise RuntimeError('Target-free child failed: '+item['run_id'])
            # Performance failures are retained. Identity/runtime failures stop subsequent calls.
            from analyze_target_free_readout_v2 import verify_child
            verify_child(Path('data'),item,protocol)
        (result/'COMPLETED').write_text('All planned measurement calls recorded; inspect coverage and model checks.\n')
    except BaseException as exc:dump(result/'worker_failure.json',{'error':repr(exc)});raise
    finally:(result/'TERMINAL').write_text('Finite worker terminal; no resume.\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','check-runtime','run']);a=p.parse_args();{'prepare':prepare,'check-runtime':check_runtime,'run':run}[a.operation]()
