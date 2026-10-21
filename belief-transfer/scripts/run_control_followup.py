"""Finite prospective controls and full off-topic observation; no training or retries."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
MASTER='ethics_gpu_control_followup_v1'
ARMS=['base','positive','negative','offtopic','c4_only']
RUNS=[f'ethics_gpu_control_recheck_{a}_v1' for a in ARMS]+[f'ethics_gpu_offtopic_supplement_s{s}_v1' for s in [42,7,1729]]

def main():
    registry=json.loads(Path('configs/handoff.json').read_text())
    for run in [MASTER,*RUNS]:
        if 'results/ethical_pilot/'+run not in registry['include_paths']:raise ValueError('Unregistered output')
        if (Path('data/results/ethical_pilot')/run).exists():raise FileExistsError('Use fresh IDs: '+run)
    out=Path('data/results/ethical_pilot')/MASTER;out.mkdir(parents=True)
    (out/'STARTED').write_text('Prospective follow-up; do not resume or overwrite.\n')
    try:
        for run in RUNS:
            command=['flock','/tmp/sft-drift-cuda-benchmark.lock','/workspace/sft-drift-vllm/.venv/bin/python','-u','run.py','+run='+run]
            print('RUN',run,flush=True)
            r=subprocess.run(command,check=False)
            with (out/'operations.jsonl').open('a') as f:f.write(json.dumps({'run_id':run,'command':command,'returncode':r.returncode})+'\n')
            write_md(out/'operations.jsonl')
    except BaseException as exc:
        (out/'worker_failure.json').write_text(json.dumps({'error':repr(exc)})+'\n');raise
    finally:(out/'TERMINAL').write_text('Finite worker terminated; inspect operation results, not a pass verdict.\n')
if __name__=='__main__':main()
