"""Prepare/run the finite neutral comparison, preserving every completed phase; no resume."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

RUN='ethics_sft_registry_format_matrix_v1'
CANARY='ethics_sft_memorization_chat_canary_v1'
PAIRS=[(f'ethics_sft_registry_{v}_calibration_v1',f'ethics_gpu_registry_{v}_validation_v1')
       for v in ['chat_high','raw_low','chat_low']]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(generated):
    refs=[]
    for train,validation in PAIRS:
        for path in [Path('data/generated/ethical_stance_sft')/train/'plan.json',
                     Path('data/generated/ethical_pilot')/validation/'protocol.json',
                     Path('configs/run')/(train+'.yaml')]:
            refs.append({'path':str(path),'sha256':sha(path)})
    for path in [Path('data/generated/ethical_stance_sft')/CANARY/'protocol.json',
                 Path('configs/run')/(CANARY+'.yaml'), Path(__file__)]:
        relative=path.relative_to(Path.cwd()) if path.is_absolute() else path
        refs.append({'path':str(relative),'sha256':sha(path)})
    plan={'run_id':RUN,'canary':CANARY,'pairs':PAIRS,'inputs':refs,
        'selection':'All unchanged gates must pass. Prefer lower LR, then assistant format at that LR. Final checkpoints only. Three fresh variants, no ethical outcomes.',
        'halt':'Stop on any execution/training/canary failure; semantic validation failures remain completed results and the finite matrix continues. No automatic treatment training.',
        'source_reference':'ethics_sft_registry_mixed_calibration_v1',
        'limit':'Neutral technical calibration only. No resume, model rental, data regeneration or evaluator changes. Historical high-LR raw anchor is not a fresh replicate.'}
    generated.mkdir(parents=True,exist_ok=False);(generated/'.writer.lock').touch()
    (generated/'matrix.json').write_text(json.dumps(plan,indent=2)+'\n')
    (generated/'MATRIX.md').write_text('# Frozen neutral format/LR matrix\n\n```json\n'+json.dumps(plan,indent=2)+'\n```\n')
    print(json.dumps(plan,indent=2))


def run(generated,root):
    plan=json.loads((generated/'matrix.json').read_text())
    if plan['run_id']!=RUN or any(sha(x['path'])!=x['sha256'] for x in plan['inputs']):
        raise ValueError('Frozen matrix inputs changed')
    root.mkdir(parents=True,exist_ok=False)
    progress={'run_id':RUN,'matrix_sha256':sha(generated/'matrix.json'),
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'started_at':datetime.now(timezone.utc).isoformat(),'completed':[],'status':'RUNNING'}
    def phase(name,command):
        progress['phase']=name
        (root/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
        print('PHASE',name,datetime.now(timezone.utc).isoformat(),flush=True)
        subprocess.run(command,check=True)
        progress['completed'].append(name)
    python=str(Path('.venv/bin/python').absolute())
    def training(id):
        phase(id,['flock','/tmp/sft-drift-cuda-benchmark.lock',python,'-u','run.py','+run='+id])
    try:
        training(CANARY)
        canary=json.loads((Path('data/results/ethical_stance_sft')/CANARY/'summary.json').read_text())
        if not canary['memorization']['passed'] or not all(canary['training']['checks'].values()):
            raise ValueError('Direct chat canary failed; do not dispatch expensive matrix')
        judgments=[]
        for train,validation in PAIRS:
            training(train)
            phase(validation,[python,'-u','scripts/validate_registry_calibration.py','run',
                '--run-id',validation,'--training-run-id',train])
            result=json.loads((Path('data/results/ethical_pilot')/validation/'summary.json').read_text())
            judgments.append({'training_run_id':train,'validation_run_id':validation,
                'passed':result['technical_qualification_passed'],'arms':result['arms']})
        preference={PAIRS[2][0]:0,PAIRS[1][0]:1,PAIRS[0][0]:2}
        accepted=sorted([x for x in judgments if x['passed']],key=lambda x:preference[x['training_run_id']])
        summary={'run_id':RUN,'canary_passed':True,'judgments':judgments,
            'accepted_run_id':accepted[0]['training_run_id'] if accepted else None,
            'interpretation':'Technical qualification only; ethical training remains pending. Stop and diagnose if no variant passes.'}
        (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (root/'summary.md').write_text('# Neutral format/LR result\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
        progress.update(status='COMPLETED',phase='judged')
        (root/'COMPLETED').write_text('Finite matrix judged; inspect accepted_run_id, which may be null.\n')
    except BaseException as exc:
        progress['status']='FAILED'
        (root/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n')
        raise
    finally:
        (root/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run'])
    args=parser.parse_args()
    generated=Path('data/generated/ethical_stance_sft')/RUN;root=Path('data/results/ethical_stance_sft')/RUN
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in [generated,root]):
        raise ValueError('Register matrix paths first')
    if args.operation=='prepare':prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        run(generated,root)


if __name__=='__main__':main()
