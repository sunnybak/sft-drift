"""Finite, prospective error RCA using existing hash-bound pilot adapters; no training."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
MASTER='ethics_gpu_error_rca_v1'
ARMS=['base','positive','negative','offtopic','c4_only']
PROFILES=['nonthink_greedy','nonthink_sampled','hf_greedy']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run_ids():return [(arm,profile,f'ethics_gpu_rca_{arm}_{profile}_v1') for profile in PROFILES for arm in (['base','offtopic'] if profile=='hf_greedy' else ARMS)]
def dump(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def write_rows(p,rows):p.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(p)
def registered():
 registry=json.loads(Path('configs/handoff.json').read_text())['include_paths']
 paths=[f'{part}/ethical_pilot/{MASTER}' for part in ['generated','results']]+[f'results/ethical_pilot/{run}' for _,_,run in run_ids()]
 if any(p not in registry for p in paths):raise ValueError('Register every RCA output before execution')
 return Path('data/generated/ethical_pilot')/MASTER,Path('data/results/ethical_pilot')/MASTER

def prepare():
 import yaml
 from belief_transfer.config import load_job
 generated,result=registered()
 if generated.exists() or result.exists():raise FileExistsError('RCA ID already prepared/started')
 jobs=[];bindings={}
 for arm,profile,run in run_ids():
  config=Path('configs/run')/(run+'.yaml')
  if config.exists() or (Path('data/results/ethical_pilot')/run).exists():raise FileExistsError(run)
  sampled=profile=='nonthink_sampled'
  overlay={'defaults':[f'ethics_gpu_control_recheck_{arm}_v2'],'run_id':run,
   'control_recheck':{'seeds':[42,7,1729] if sampled else [42]},
   'pilot_bench':{'max_new_tokens':256,'measurement_batch_size':8 if profile=='hf_greedy' else 64,
     'measurement_decoding':{'thinking':False,'temperature':.7 if sampled else 0,'top_p':.8 if sampled else 1.,'top_k':20,'min_p':0.}}}
  if profile=='hf_greedy':overlay['pilot_bench']['cuda_generation']=None
  config.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
  job=load_job(['+run='+run])
  jobs.append({'arm':arm,'profile':profile,'run_id':run,'config_sha256':sha(config),'expected':672 if sampled else 224,
               'adapter_path':str(job.pilot_bench.adapter_path) if job.pilot_bench.adapter_path else None,'adapter_sha256':job.control_recheck.adapter_sha256})
  bindings[str(config)]=sha(config)
 # Audit only preserved failures; no reinterpretation of strict/semantic verdicts.
 audit=[]
 for arm in ARMS:
  path=Path(f'data/results/ethical_pilot/ethics_gpu_control_recheck_{arm}_v2/observations.jsonl');digest=sha(path)
  for r in map(json.loads,path.read_text().splitlines()):
   if r.get('error') or r.get('answer')!=r.get('expected') or not r.get('strict_format'):
    audit.append({'arm':arm,'kind':'known_control','source':str(path),'source_sha256':digest,
      **{k:r.get(k) for k in ['presentation_id','audit_form','fact_id','audit_seed','expected','answer','final_response','error','strict_format','response']},
      'generation':{k:r.get('generation_metadata',{}).get(k) for k in ['finish_reason','generation_tokens','backend_error']}})
  run='ethics_gpu_instruction_retention_base_v1' if arm=='base' else f'ethics_gpu_pilot_{arm}_retention_v1'
  root=Path('data/results/ethical_pilot')/run;path=root/'responses.jsonl';digest=sha(path)
  known={r['example_id'] for r in map(json.loads,(root/'known_items.jsonl').read_text().splitlines())}
  for r in map(json.loads,path.read_text().splitlines()):
   if r['example_id'] in known and not all(r['assessment'][k] for k in ['semantic_correct','strict_format','response_boundaries_valid','normal_stop']):
    audit.append({'arm':arm,'kind':'fixed_retention','source':str(path),'source_sha256':digest,**{k:r[k] for k in ['example_id','family','thinking','prompt','expected','response','assessment']}})
 generated.mkdir(parents=True)
 write_rows(generated/'historical_failures.jsonl',audit)
 dump(generated/'historical_audit_summary.json',{'n_failed_presentations':len(audit),'by_arm_kind':dict(Counter(r['arm']+'/'+r['kind'] for r in audit))})
 for f in ['scripts/run_error_rca.py','src/belief_transfer/stages/control_recheck.py','src/belief_transfer/evals/control_recheck.py','src/belief_transfer/inference/vllm_model.py','src/belief_transfer/validation/measurements.py','src/belief_transfer/metrics/control_recheck.py','../changelog/2026-10-21-error-rca-plan.md']:
  bindings[f]=sha(f)
 protocol={'run_id':MASTER,'jobs':jobs,'source_bindings':bindings,'no_training':True,'no_resume':True,
  'plan':'../changelog/2026-10-21-error-rca-plan.md','expected_calls':sum(j['expected'] for j in jobs),
  'criteria':'Original expanded control gates retained; report every failure; natural ethical consistency never a gate.'}
 dump(generated/'protocol.json',protocol)
 (generated/'protocol.md').write_text('# Prospective RCA protocol\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
 print(json.dumps(protocol,indent=2))

def run():
 generated,result=registered();protocol=json.loads((generated/'protocol.json').read_text())
 if result.exists():raise FileExistsError('RCA worker started; no restart/resume')
 if any(sha(path)!=digest for path,digest in protocol['source_bindings'].items()):raise ValueError('Prepared RCA source/config changed')
 for job in protocol['jobs']:
  if (Path('data/results/ethical_pilot')/job['run_id']).exists():raise FileExistsError('Child already started')
 result.mkdir(parents=True);(result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
 (result/'STARTED').write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
 try:
  for job in protocol['jobs']:
   python='.venv/bin/python' if job['profile']=='hf_greedy' else '/workspace/sft-drift-vllm/.venv/bin/python'
   command=['flock','/tmp/sft-drift-cuda-benchmark.lock',python,'-u','run.py','+run='+job['run_id']]
   print('RUN',job['run_id'],flush=True);operation=subprocess.run(command,check=False)
   path=result/'operations.jsonl'
   with path.open('a') as stream:stream.write(json.dumps({**job,'command':command,'returncode':operation.returncode})+'\n')
   write_md(path)
   if operation.returncode:raise RuntimeError(f"RCA child failed: {job['run_id']}")
  (result/'COMPLETED').write_text('All planned operations returned0; inspect control outcomes.\n')
 except BaseException as exc:
  dump(result/'worker_failure.json',{'error':repr(exc)});raise
 finally:(result/'TERMINAL').write_text('Worker terminal; no resume.\n')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run']);args=parser.parse_args()
 prepare() if args.operation=='prepare' else run()
