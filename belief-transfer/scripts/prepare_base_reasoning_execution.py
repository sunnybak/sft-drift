"""Freeze executable development and independent-confirmation contracts before SFT."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.config import load_job,config_sha
from prepare_base_reasoning_replay import MASTER,TRAIN,PARENT,PLAN
from prepare_base_reasoning_confirmation import MASTER as CONF,PARTS
from prepare_replay_interface_rca import CELLS as THREE_CELLS
from prepare_replay_weight_ablation import read,sha,write_json
from run_replay_weight_confirmation import check_bindings

POINTS=('midpoint','terminal','final')
CELLS=(*THREE_CELLS,'held_eval')
PART_NAMES=('retention',*[f'decisions_{c}' for c in CELLS])
GENERATED=Path('data/generated/ethical_stance_sft')/MASTER
RESULTS=Path('data/results/ethical_stance_sft')/MASTER
CONF_ROOT=Path('data/generated/ethical_pilot')/CONF
RCA_GENERATED=Path('data/generated/ethical_pilot/ethics_gpu_replay_interface_rca_v1')
RCA_RESULTS=Path('data/results/ethical_pilot/ethics_gpu_replay_interface_rca_v1')
REFERENCE=Path('data/results/ethical_stance_sft/ethics_sft_replay_coverage_probe_v4')
AMENDMENT=Path('../changelog/2026-10-22-base-reasoning-execution-plan.md')


def measure_id(point: str,part: str) -> str:
    if point not in POINTS or part not in PART_NAMES:raise ValueError('Unknown checkpoint/part')
    return f'ethics_gpu_base_reasoning_{point}_{part}_v1'


def eval_id(point: str,phase: str) -> str:
    if point not in POINTS or phase not in ('development','validation','reading','unqualified'):raise ValueError('Unknown checkpoint/phase')
    return f'ethics_gpu_base_reasoning_{point}_{phase}_s42_v1'


def required_paths() -> list[str]:
    names=[measure_id(p,k) for p in POINTS for k in PART_NAMES]
    names += [eval_id(p,f) for p in POINTS for f in ('development','validation','reading','unqualified')]
    return [f'{part}/ethical_pilot/{name}' for name in names for part in ('generated','results')]


def prepare() -> None:
    import yaml
    if not set(required_paths())<=set(read(Path('configs/handoff.json'))['include_paths']):raise ValueError('Register every output path first')
    protocol_path=GENERATED/'protocol.json';confirm_path=CONF_ROOT/'execution_protocol_v1.json'
    if protocol_path.exists() or confirm_path.exists() or RESULTS.exists():raise FileExistsError('No execution-contract overwrite/resume')
    prep=read(GENERATED/'preparation.json');freeze=read(GENERATED/'data_freeze_v1.json');conf=read(CONF_ROOT/'protocol.json')
    for d in (prep,freeze,conf):check_bindings(d['source_bindings'])
    qa=Path('data/results/ethical_stance_sft/ethics_sft_base_reasoning_replay_data_v1/target_review_summary_v1.json')
    review=read(qa)
    if not review['full_target_review_complete'] or review['target_review_sha256']!=sha(qa.parent/'target_agent_review_v1.jsonl'):
        raise ValueError('Complete target review missing/changed')
    if config_sha(load_job(['+run='+TRAIN]))!=prep['config_sha']:raise ValueError('Prepared training config changed')
    old=read(Path('data/generated/ethical_stance_sft/ethics_sft_replay_coverage_value_v5/protocol.json'))
    rca=read(RCA_GENERATED/'protocol.json');jobs={TRAIN:prep['config_sha']}
    checkpoint_paths={p:f'data/checkpoints/ethical_stance_sft/{TRAIN}/'+{'midpoint':'checkpoint-227','terminal':'checkpoint-454','final':'final'}[p] for p in POINTS}
    for point in POINTS:
        for phase in ('development','validation','reading','unqualified'):
            name=eval_id(point,phase);path=Path('configs/run',name+'.yaml')
            if path.exists():raise FileExistsError('Fresh checkpoint config IDs required')
            bench={'adapter_path':checkpoint_paths[point],'seed':42}
            if phase=='validation':bench['stance_study']={'selection_run_id':eval_id(point,'development')}
            if phase in ('reading','unqualified'):
                bench.update(measurement_control_failure_policy='collect_unqualified',
                    stance_validation_run_id=eval_id(point,'validation') if phase=='reading' else None)
            overlay={'defaults':[f'ethics_gpu_replay_coverage_{phase}_s42_v5'],'run_id':name,'pilot_bench':bench}
            path.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False));jobs[name]=config_sha(load_job(['+run='+name]))
    models={m:dict(rca['models'][m]) for m in ('base','control')}
    control=Path(models['control']['adapter_path'])
    models['control']['adapter_config_sha256']=sha(control/'adapter_config.json')
    refs={}
    for model in ('base','control','candidate'):
        label='parent' if model=='candidate' else model
        refs[label]={'rca_model':model,'adapter_sha256':rca['models'][model]['adapter_file_sha256'],'decisions':{}}
        for cell in CELLS:
            name=rca['models'][model]['reference_id'] if cell=='held_eval' else next(j['run_id'] for j in rca['jobs'] if j['model']==model and j['cell']==cell)
            refs[label]['decisions'][cell]=name
        refs[label]['retention']={'run_id':'ethics_gpu_replay_coverage_candidate_retention_v5' if model=='candidate' else f'ethics_gpu_replay_coverage_{model}_retention_v4',
            'parent':str(Path('data/results/ethical_stance_sft/ethics_sft_replay_coverage_value_v5') if model=='candidate' else REFERENCE),
            'inspection_role':model}
    source_paths=[PLAN,AMENDMENT,qa,qa.parent/'target_agent_review_v1.jsonl',GENERATED/'preparation.json',GENERATED/'data_freeze_v1.json',
        CONF_ROOT/'protocol.json',*[CONF_ROOT/(part+'.jsonl') for part in PARTS],RCA_GENERATED/'protocol.json',
        Path('data/generated/ethical_stance_sft/ethics_sft_replay_coverage_value_v5/protocol.json'),
        Path('data/results/ethical_stance_sft')/PARENT/'summary.json',
        control/'adapter_model.safetensors',control/'adapter_config.json']
    source_paths += [Path(p) for p in prep['source_bindings']]
    source_paths += list(REFERENCE.glob('*'))
    for spec in refs.values():
        r=spec['retention'];source_paths += list((Path('data/results/ethical_pilot')/r['run_id']).glob('*'))
        source_paths += [Path(r['parent'])/(r['inspection_role']+'_retention_dispatch.json')]
        for name in spec['decisions'].values():source_paths += list((Path('data/results/ethical_pilot')/name).glob('*'))
    source_paths += [RCA_GENERATED/(c+'.jsonl') for c in CELLS]
    source_paths += sorted(Path('src/belief_transfer').rglob('*.py'))+sorted(Path('configs').rglob('*.yaml'))
    source_paths += [Path('scripts',n) for n in ('prepare_base_reasoning_execution.py','run_base_reasoning_probe.py',
        'run_base_reasoning_confirmation.py','base_reasoning_runtime.py','base_reasoning_confirmation_checks.py',
        'run_replay_coverage_probe.py','run_replay_interface_rca.py','analyze_replay_value_probe.py','validate_registry_calibration.py')]
    sources={str(p):sha(p) for p in source_paths if p.is_file()}
    for n in ('run_base_reasoning_probe.py','run_base_reasoning_confirmation.py'):
        if str(Path('scripts',n)) not in sources:raise ValueError('Execution worker missing')
    write_json(confirm_path,{'prepared_protocol_sha256':sha(CONF_ROOT/'protocol.json'),'runtime_reference':old['runtime_reference'],
        'models':models,'source_bindings':sources,'condition':'Fully reviewed final development pass only. No historic v5confirmation resumed.'})
    write_json(protocol_path,{'run_id':MASTER,'train_id':TRAIN,'chunks':3625,'projection':prep['projection'],
        'expected_initial_adapter_sha256':freeze['expected_initial_adapter_sha256'],'runtime_reference':old['runtime_reference'],
        'bank_path':old['bank_path'],'checkpoint_paths':checkpoint_paths,'references':refs,'jobs':jobs,
        'source_bindings':sources|{str(confirm_path):sha(confirm_path)},
        'launch_allowed':True,'primary':'final','checkpoint_coverage':'midpoint and final full100;terminal aliases final only on exact adapter+config bytes, otherwise separately measured.',
        'no_resume':True,'no_automatic_confirmation':True})
    print({'worker_contract':'frozen','checkpoint_roles':list(POINTS),'primary':'final','source_bindings':len(sources),'confirmation_frozen':True})


if __name__=='__main__':prepare()
