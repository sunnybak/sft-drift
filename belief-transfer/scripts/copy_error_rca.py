"""Copy closed follow-up outputs only; running model directories stay on the GPU."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile
from preserve_ethical_pilot import install_terminal
from run_error_rca import MASTER,run_ids
RUNS=[run for _,_,run in run_ids()]
PROJECT=Path(__file__).resolve().parents[1]
REMOTE=r'''
from pathlib import Path
import hashlib,io,json,subprocess,tarfile
base=Path('/workspace/sft-drift/belief-transfer');master=__MASTER__;runs=__RUNS__
root=base/'data/results/ethical_pilot'/master
ops=[json.loads(l) for l in (root/'operations.jsonl').read_text().splitlines()] if (root/'operations.jsonl').exists() else []
status=subprocess.run(['supervisorctl','status',__SERVICE__],capture_output=True,text=True).stdout.strip()
terminal=any(w in status.split() for w in ['EXITED','STOPPED','FATAL','UNKNOWN'])
closed=[base/'data/results/ethical_pilot'/r['run_id'] for r in ops]
if terminal:
 log=Path(__LOG__)
 dst=root/'cuda_worker.log'
 raw=log.read_bytes()
 if dst.exists() and dst.read_bytes()!=raw:raise ValueError('Terminal log changed')
 if not dst.exists():dst.write_bytes(raw)
 closed.append(root)
manifest={};archive=Path(__ARCHIVE__)
with tarfile.open(archive,'w') as tar:
 for p in sorted({p for root in closed if root.exists() for p in root.rglob('*') if p.is_file()}):
  if p.is_symlink():raise ValueError('Symlink output')
  before=p.stat();raw=p.read_bytes();name=str(p.relative_to(base));tar.add(p,arcname=name,recursive=False)
  if p.stat().st_mtime_ns!=before.st_mtime_ns or p.read_bytes()!=raw:raise ValueError('Output still changing')
  manifest[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 raw=json.dumps(manifest).encode();info=tarfile.TarInfo('OFFBOX_MANIFEST.json');info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
print(json.dumps({'archive':str(archive),'status':status,'terminal':terminal,'operations':ops}))
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--suite',choices=['decoder','response','retention','scope','readout','interfaces','paired','target_free','modes','target_readout','target_readout_v2','scope_fact_clarity','fresh_retention','presence'],default='decoder');p.add_argument('--host',required=True);p.add_argument('--port',type=int,required=True);args=p.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9_.@:-]+',args.host) or not 1<=args.port<=65535:raise ValueError('Unsafe host/port')
 master=MASTER;runs=RUNS;name='error-rca-v1'
 if args.suite=='response':
  from run_response_interface_rca import MASTER as master,run_ids as response_ids
  runs=[r for _,_,r in response_ids()];name='response-interface-rca-v1'
 if args.suite=='retention':
  from run_retention_rca import MASTER as master,run_ids as retention_ids
  runs=[r for _,_,r in retention_ids()];name='retention-rca-v2'
 if args.suite=='scope':
  from run_scope_controls import MASTER as master,run_ids as scope_ids
  runs=[r for _,_,r in scope_ids()];name='scope-controls-v1'
 if args.suite=='interfaces':
  from run_interface_controls import MASTER as master,run_ids as interface_ids
  runs=[r for _,_,r in interface_ids()];name='interface-controls-v1'
 if args.suite=='target_free':
  from run_target_free_controls import MASTER as master,run_ids as target_ids
  runs=[r for _,_,r in target_ids()];name='target-free-controls-v1'
 if args.suite=='modes':
  from run_target_free_modes import MASTER as master,run_ids as mode_ids
  runs=[r for _,_,r in mode_ids()];name='target-free-modes-v1'
 if args.suite=='target_readout':
  from run_target_free_readout import MASTER as master,run_ids as target_readout_ids
  runs=[r for _,_,r in target_readout_ids()];name='target-free-readout-v1'
 if args.suite=='target_readout_v2':
  from run_target_free_readout_v2 import MASTER as master,run_ids as target_readout_v2_ids
  runs=[r for _,_,r in target_readout_v2_ids()];name='target-free-readout-v2'
 if args.suite=='scope_fact_clarity':
  from run_scope_fact_clarity import MASTER as master,run_ids as clarity_ids
  runs=[r for _,_,r in clarity_ids()];name='scope-fact-clarity-'+master.rsplit('_',1)[1]
 if args.suite=='fresh_retention':
  from run_fresh_retention import MASTER as master,ARMS,run_id
  runs=[run_id(a) for a in ARMS];name='fresh-retention-v1'
 if args.suite=='presence':
  from run_presence_controls import MASTER as master,run_ids as presence_ids
  runs=[r for _,_,r in presence_ids()];name='presence-controls-v1'
 if args.suite=='paired':
  from run_paired_readout import MASTER as master,run_ids as paired_ids
  runs=[r for _,_,r in paired_ids()];name='paired-readout-v1'
 if args.suite=='readout':
  from run_scoped_readout import MASTER as master,run_ids as readout_ids
  runs=[r for _,_,r in readout_ids()];name='scoped-readout-v1'
 script=REMOTE.replace('__MASTER__',repr(master)).replace('__RUNS__',repr(runs)).replace('__SERVICE__',repr('sft-drift-'+name)).replace('__LOG__',repr('/workspace/sft-drift-ops/'+name+'.log')).replace('__ARCHIVE__',repr('/workspace/sft-drift-ops/'+name+'-closed.tar'))
 r=subprocess.run(['ssh','-p',str(args.port),args.host,'python3','-'],input=script,text=True,capture_output=True,timeout=600);r.check_returncode();state=json.loads(r.stdout.strip().splitlines()[-1])
 registry=json.loads((PROJECT/'configs/handoff.json').read_text());allowed=['data/'+x for x in registry['include_paths'] if x.startswith('results/ethical_pilot/')]
 with tempfile.TemporaryDirectory(prefix='error-rca-copy-') as folder:
  archive=Path(folder)/'closed.tar';subprocess.run(['scp','-P',str(args.port),args.host+':'+state['archive'],str(archive)],check=True)
  manifest=install_terminal(archive,PROJECT,allowed)
 out=PROJECT/'data/results/ethical_pilot'/master;out.mkdir(parents=True,exist_ok=True)
 name=f"copy_receipt_{len(state['operations'])}_{'terminal' if state['terminal'] else 'partial'}.json"
 dest=out/name
 receipt={'copied_at':datetime.now(timezone.utc).isoformat(),'verified':True,'manifest':manifest,'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest.values()),**state}
 if not dest.exists():dest.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({k:receipt[k] for k in ['verified','files','bytes','terminal','status']}))
if __name__=='__main__':main()
