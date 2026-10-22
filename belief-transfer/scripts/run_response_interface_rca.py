"""Finite response-interface diagnostic; explicit prepared bank, no training/resume."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_error_rca import sha,dump,write_rows
MASTER='ethics_gpu_response_interface_rca_v1'
ARMS=['base','offtopic']
MODES=['nonthinking','thinking']
def run_ids():return [(arm,mode,f'ethics_gpu_response_rca_{arm}_{mode}_v1') for mode in MODES for arm in ARMS]
def registered():
 registry=json.loads(Path('configs/handoff.json').read_text())['include_paths']
 paths=[f'{part}/ethical_pilot/{MASTER}' for part in ['generated','results']]+[f'results/ethical_pilot/{run}' for _,_,run in run_ids()]
 if any(p not in registry for p in paths):raise ValueError('Register all outputs before execution')
 return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def prepare():
 import yaml
 from belief_transfer.config import load_job
 from belief_transfer.evals.response_interface_rca import build_bank
 generated,result=registered()
 if generated.exists() or result.exists():raise FileExistsError('Diagnostic already prepared/started')
 for _,_,run in run_ids():
  if (Path('configs/run')/(run+'.yaml')).exists() or (Path('data/results/ethical_pilot')/run).exists():raise FileExistsError(run)
 generated.mkdir(parents=True);bank=generated/'bank.jsonl';write_rows(bank,build_bank())
 jobs=[];bindings={str(bank):sha(bank)}
 for arm,mode,run in run_ids():
  source=load_job(['+run=ethics_gpu_control_recheck_'+arm+'_v2'])
  thinking=mode=='thinking'
  overlay={'defaults':['ethics_gpu_control_recheck_'+arm+'_v2'],'stage':'response_interface_rca','run_id':run,
   'control_recheck':None,'response_interface_rca':{'model_label':arm,'bank_path':str(bank),'bank_sha256':sha(bank),'adapter_sha256':source.control_recheck.adapter_sha256},
   'pilot_bench':{'max_new_tokens':4096 if thinking else 256,'measurement_batch_size':64,
    'measurement_decoding':{'thinking':thinking,'temperature':.6 if thinking else .7,'top_p':.95 if thinking else .8,'top_k':20,'min_p':0.}}}
  config=Path('configs/run')/(run+'.yaml');config.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
  job=load_job(['+run='+run]);bindings[str(config)]=sha(config)
  jobs.append({'arm':arm,'mode':mode,'run_id':run,'expected':256,'adapter_sha256':job.response_interface_rca.adapter_sha256})
 for file in ['scripts/run_response_interface_rca.py','src/belief_transfer/evals/response_interface_rca.py','src/belief_transfer/stages/response_interface_rca.py','src/belief_transfer/validation/response_interface_rca.py','src/belief_transfer/metrics/response_interface_rca.py','src/belief_transfer/inference/vllm_model.py','../changelog/2026-10-21-response-interface-rca-plan.md']:
  bindings[file]=sha(file)
 protocol={'run_id':MASTER,'jobs':jobs,'source_bindings':bindings,'no_training':True,'no_resume':True,'expected_calls':1024,
  'plan':'../changelog/2026-10-21-response-interface-rca-plan.md','interpretation':'Development only; held-out all-model qualification needed before any adoption.'}
 dump(generated/'protocol.json',protocol)
 (generated/'protocol.md').write_text('# Prospective response-interface protocol\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
 print(json.dumps(protocol,indent=2))

def run():
 from belief_transfer.analysis.jsonl_md import write_md
 generated,result=registered();protocol=json.loads((generated/'protocol.json').read_text())
 if result.exists():raise FileExistsError('Worker started; no resume/restart')
 if any(sha(path)!=digest for path,digest in protocol['source_bindings'].items()):raise ValueError('Prepared source/input changed')
 for job in protocol['jobs']:
  if (Path('data/results/ethical_pilot')/job['run_id']).exists():raise FileExistsError('Child already started')
 result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
 (result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
 try:
  for job in protocol['jobs']:
   command=['flock','/tmp/sft-drift-cuda-benchmark.lock','/workspace/sft-drift-vllm/.venv/bin/python','-u','run.py','+run='+job['run_id']]
   print('RUN',job['run_id'],flush=True);operation=subprocess.run(command,check=False)
   path=result/'operations.jsonl'
   with path.open('a') as stream:stream.write(json.dumps({**job,'command':command,'returncode':operation.returncode})+'\n')
   write_md(path)
   if operation.returncode:raise RuntimeError('Child failed: '+job['run_id'])
  (result/'COMPLETED').write_text('All planned calls recorded; inspect outcomes.\n')
 except BaseException as exc:
  dump(result/'worker_failure.json',{'error':repr(exc)});raise
 finally:(result/'TERMINAL').write_text('Terminal worker; no resume.\n')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run']);args=parser.parse_args()
 prepare() if args.operation=='prepare' else run()
