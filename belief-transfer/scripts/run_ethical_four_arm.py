"""Execute the finite frozen pilot on CUDA; every successful fine-tune gets all100beliefs."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
import prepare_ethical_four_arm as pilot
import validate_registry_calibration as binding


def measurement_choice(development_ok:bool,validation_ok:bool)->str:
    return 'stance' if development_ok and validation_ok else 'unqualified'


def execute(command:list[str],out:Path,label:str,*,runner=subprocess.run)->bool:
    print('RUN',label,' '.join(command),flush=True)
    result=runner(command,check=False)
    event={'operation':label,'command':command,'returncode':result.returncode,'succeeded':result.returncode==0}
    p=out/'operations.jsonl'
    with p.open('a') as stream:stream.write(json.dumps(event)+'\n')
    write_md(p)
    return event['succeeded']


def main()->None:
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    master=Path('data/generated/ethical_stance_sft')/pilot.MASTER
    execution=pilot.read(master/'execution_manifest.json')
    for name,digest in execution['immutable_inputs'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or pilot.sha(path)!=digest:raise ValueError('Changed/nonportable frozen input: '+name)
    for name in execution['new_output_roots']:
        if Path(name).exists():raise FileExistsError('Started pilot cannot resume/overwrite: '+name)
    out=Path('data/results/ethical_stance_sft')/pilot.MASTER
    if (out/'STARTED').exists():raise FileExistsError('Pilot worker already started')
    (out/'STARTED').write_text(pilot.sha(master/'execution_manifest.json')+'\n')
    train_python='/workspace/sft-drift/belief-transfer/.venv/bin/python'
    eval_python='/workspace/sft-drift-vllm/.venv/bin/python'
    lock=['flock','/tmp/sft-drift-cuda-benchmark.lock']
    try:
        for arm in pilot.ARMS:
            run=pilot.run_id(arm)
            if not execute([*lock,train_python,'-u','run.py','+run='+run],out,'train/'+arm):continue
            plan=pilot.read(Path('data/generated/ethical_stance_sft')/run/'plan.json')
            bindings=binding.training_binding(plan,Path('data/results/ethical_stance_sft')/run,Path('data/checkpoints/ethical_stance_sft')/run/'final')
            pilot.dump(out/(arm+'_training_binding.json'),bindings)
            execute([train_python,'-u','scripts/probe_instruction_retention.py','run','--run-id',f'ethics_gpu_pilot_{arm}_retention_v1','--training-run-id',run],out,'retention/'+arm)
            for seed in pilot.SEEDS:
                binding.verify_binding(bindings)
                def run_phase(phase):return execute([*lock,eval_python,'-u','run.py','+run='+pilot.eval_id(arm,phase,seed)],out,f'{phase}/{arm}/{seed}')
                development_ok=run_phase('development')
                dev_summary=Path('data/results/ethical_pilot')/pilot.eval_id(arm,'development',seed)/'stance_study_summary.json'
                development_ok=development_ok and dev_summary.exists() and pilot.read(dev_summary).get('selected')=='named_endorse_reject'
                validation_ok=run_phase('validation') if development_ok else False
                val_summary=Path('data/results/ethical_pilot')/pilot.eval_id(arm,'validation',seed)/'stance_study_summary.json'
                validation_ok=validation_ok and val_summary.exists() and pilot.read(val_summary).get('validation_passed') is True
                phase=measurement_choice(development_ok,validation_ok)
                if phase=='unqualified':
                    directory=Path('data/results/ethical_pilot')/pilot.eval_id(arm,phase,seed);directory.mkdir(parents=True,exist_ok=False)
                    (directory/'UNQUALIFIED.md').write_text('Qualification failed; all100beliefs still measured under frozen instrument/settings. Results are exploratory observations, not qualified treatment evidence. No settings retuned.\n')
                run_phase(phase)
        execute([train_python,'scripts/analyze_ethical_four_arm.py'],out,'analysis')
        (out/'TERMINAL').write_text('Finite worker ended. Inspect operations/failures/coverage; this marker is not success.\n')
    except BaseException as exc:
        pilot.dump(out/'worker_failure.json',{'error':str(exc),'traceback':traceback.format_exc()});raise
if __name__=='__main__':main()
