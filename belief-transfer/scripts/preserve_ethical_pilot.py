"""Mac-side finite pilot preservation: serialize checkpoint copies and private snapshots."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time

PROJECT=Path(__file__).resolve().parents[1]
REMOTE=r'''
from pathlib import Path
import json,subprocess,tarfile,hashlib,io
base=Path('/workspace/sft-drift/belief-transfer');master=__MASTER__;job=__JOB__
plan=json.loads((base/'data/generated/ethical_stance_sft'/master/'plan.json').read_text());step=plan['steps']
p=subprocess.run(['supervisorctl','status',job],capture_output=True,text=True)
terminal=any(x in p.stdout.split() for x in ['EXITED','FATAL','STOPPED','UNKNOWN'])
ready=[]
for arm,value in plan['arms'].items():
 run=value['run_id'];root=base/'data/checkpoints/ethical_stance_sft'/run
 try:last=json.loads((root/'training_batches.jsonl').read_text().splitlines()[-1])['optimizer_step_before_batch']
 except (FileNotFoundError,IndexError,json.JSONDecodeError):last=-1
 for n in [step//2,step]:
  try:saved=json.loads((root/f'checkpoint-{n}'/'trainer_state.json').read_text())['global_step']
  except (FileNotFoundError,json.JSONDecodeError):continue
  if saved==n and (last>=n or (base/'data/results/ethical_stance_sft'/run/'COMPLETED').exists()):ready.append([run,n])
result={'terminal':terminal,'supervisor':p.stdout.strip(),'ready':ready}
if terminal and __PACK__:
 log=Path('/workspace/sft-drift-ops/ethical_four_arm_v1.log')
 copied_log=base/'data/results/ethical_stance_sft'/master/'cuda_worker.log'
 if log.exists():
  content=log.read_bytes()
  if copied_log.exists() and copied_log.read_bytes()!=content:raise ValueError('Terminal log changed')
  if not copied_log.exists():copied_log.write_bytes(content)
 roots=[base/'data/results/ethical_stance_sft'/master]
 for arm,value in plan['arms'].items():
  run=value['run_id'];roots += [base/'data/results/ethical_stance_sft'/run,base/'data/checkpoints/ethical_stance_sft'/run/'final']
  roots += [base/'data/results/ethical_pilot'/id for id in value['evaluation_ids']]
  roots += [base/'data/results/ethical_pilot'/f'ethics_gpu_pilot_{arm}_retention_v1']
 files=set(p for root in roots if root.exists() for p in root.rglob('*') if p.is_file())
 for value in plan['arms'].values():
  root=base/'data/checkpoints/ethical_stance_sft'/value['run_id']
  if root.exists():files.update(p for p in root.iterdir() if p.is_file())
 archive=Path('/workspace/sft-drift-ops')/(master+'_terminal.tar');manifest={}
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 with tarfile.open(archive,'w') as tar:
  for path in sorted(files):
   if path.is_symlink():raise ValueError('Symlink in terminal outputs')
   before=path.stat();digest=sha(path);name=str(path.relative_to(base));tar.add(path,arcname=name,recursive=False)
   after=path.stat()
   if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or sha(path)!=digest:raise ValueError('Live terminal file')
   manifest[name]={'sha256':digest,'bytes':after.st_size}
  raw=json.dumps(manifest).encode();info=tarfile.TarInfo('OFFBOX_MANIFEST.json');info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
 result['archive']=str(archive)
print(json.dumps(result))
'''

def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()

def install_terminal(archive:Path,project:Path,allowed:list[str])->dict:
    with tarfile.open(archive) as tar:
        manifest=json.load(tar.extractfile('OFFBOX_MANIFEST.json'))
        # Verify all archive bytes and all existing destinations before any installation.
        for name,meta in manifest.items():
            if 'local_path' in meta:raise ValueError('Archive cannot choose local destination')
            path=Path(name)
            if path.is_absolute() or '..' in path.parts or not any(name.startswith(prefix+'/') for prefix in allowed):raise ValueError('Unregistered terminal path')
            member=tar.getmember(name)
            if not member.isfile() or member.issym() or member.islnk():raise ValueError('Nonregular terminal artifact')
            stream=tar.extractfile(member);h=hashlib.sha256();size=0
            for block in iter(lambda:stream.read(1048576),b''):h.update(block);size+=len(block)
            if h.hexdigest()!=meta['sha256'] or size!=meta['bytes']:raise ValueError('Terminal archive integrity failure')
            dest=project/name
            if dest.exists() and digest(dest)!=meta['sha256']:
                # Derived views may differ only in the displayed JSONL path. Keep
                # both exact views; the immutable JSONL must already match.
                raw_name=str(path.with_suffix('.jsonl'))
                raw_meta=manifest.get(raw_name)
                incoming=tar.extractfile(member).read()
                old=dest.read_bytes()
                short=('`'+Path(raw_name).name+'` — ').encode()
                full=('`'+raw_name+'` — ').encode()
                prefix=b'# '+Path(raw_name).name.encode()+b'\n\n'
                same_view=(old.startswith(prefix) and incoming.startswith(prefix)
                           and old.replace(full,short,1)==incoming.replace(full,short,1))
                if (path.suffix!='.md' or not raw_meta or not (project/raw_name).exists()
                        or digest(project/raw_name)!=raw_meta['sha256'] or not same_view):
                    raise FileExistsError('Refuse changed historical artifact: '+name)
                local_path=str(path.with_name(path.stem+'.gpu-view.md'))
                dest=project/local_path
                if dest.exists() and digest(dest)!=meta['sha256']:
                    raise FileExistsError('Refuse changed GPU view: '+local_path)
                meta['local_path']=local_path
        for name,meta in manifest.items():
            dest=project/meta.get('local_path',name)
            if not dest.exists():
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as out,tar.extractfile(name) as source:
                    for block in iter(lambda:source.read(1048576),b''):out.write(block)
            if digest(dest)!=meta['sha256']:raise ValueError('Installed terminal hash mismatch')
    return manifest

def main()->None:
    if sys.platform!='darwin':raise ValueError('Run private preservation on the Mac, not the GPU box')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--host',required=True);parser.add_argument('--port',type=int,required=True);parser.add_argument('--job',required=True);parser.add_argument('--master-run',required=True);args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.@:-]+',args.host) or not re.fullmatch(r'[A-Za-z0-9_-]+',args.job) or not re.fullmatch(r'ethics_sft_[A-Za-z0-9_]+',args.master_run) or not 1<=args.port<=65535:raise ValueError('Unsafe explicit identity')
    master=PROJECT/'data/generated/ethical_stance_sft'/args.master_run;plan=json.loads((master/'plan.json').read_text());out=PROJECT/'data/results/ethical_stance_sft'/args.master_run
    registry=json.loads((PROJECT/'configs/handoff.json').read_text())
    allowed=['data/'+p for p in registry['include_paths'] if p.startswith(('results/','checkpoints/'))]
    status=out/'preservation_status.json';events=out/'preservation_events.jsonl'
    sys.path.insert(0,str(PROJECT/'src'))
    from belief_transfer.analysis.jsonl_md import write_md
    def event(state,**extra):
        value={'state':state,'updated_at':datetime.now(timezone.utc).isoformat(),**extra};status.write_text(json.dumps(value,indent=2)+'\n')
        with events.open('a') as stream:stream.write(json.dumps(value)+'\n')
        write_md(events);print(json.dumps(value),flush=True)
    def call(command):subprocess.run(command,check=True,cwd=PROJECT)
    def snapshot():
        event('snapshot_running')
        save=subprocess.run([sys.executable,'scripts/handoff.py','save'],cwd=PROJECT)
        if save.returncode:event('snapshot_failed',returncode=save.returncode);return
        verify=subprocess.run([sys.executable,'scripts/handoff.py','verify'],cwd=PROJECT)
        event('snapshot_verified' if verify.returncode==0 else 'snapshot_verify_failed',returncode=verify.returncode)
    script=REMOTE.replace('__MASTER__',repr(args.master_run)).replace('__JOB__',repr(args.job))
    complete=False;failures=0;verified_receipts=set()
    try:
        event('waiting_for_checkpoint',job=args.job)
        while not complete:
            try:
                result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','-p',str(args.port),args.host,'python3','-'],input=script.replace('__PACK__','False'),capture_output=True,text=True,timeout=90)
                if result.returncode:raise RuntimeError(result.stderr[-1000:])
                observation=json.loads(result.stdout.strip().splitlines()[-1]);failures=0
            except (subprocess.TimeoutExpired,RuntimeError,json.JSONDecodeError) as exc:
                failures+=1;event('observation_error',error=str(exc),consecutive=failures)
                if failures>=3:raise
                time.sleep(10);continue
            for run,step in observation['ready']:
                receipt=PROJECT/'data/results/ethical_stance_sft'/run/f'checkpoint_{step}_offbox_copy_verification.json'
                if receipt.exists():
                    if str(receipt) not in verified_receipts:
                        saved=json.loads(receipt.read_text())
                        if any(digest(PROJECT/name)!=meta['sha256'] for name,meta in saved['manifest'].items()):raise ValueError('Existing checkpoint receipt no longer verifies')
                        verified_receipts.add(str(receipt))
                    continue
                event('copying_checkpoint',run_id=run,step=step)
                call([sys.executable,'scripts/preserve_cuda_checkpoint.py','--host',args.host,'--port',str(args.port),'--run-id',run,'--step',str(step),'--job',args.job])
                if not receipt.exists():raise RuntimeError('Copy did not produce verified receipt')
                verified_receipts.add(str(receipt))
                event('checkpoint_verified',run_id=run,step=step);snapshot()
            if observation['terminal']:
                event('copying_terminal_results')
                packed=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','-p',str(args.port),args.host,'python3','-'],input=script.replace('__PACK__','True'),capture_output=True,text=True,timeout=600)
                packed.check_returncode();value=json.loads(packed.stdout.strip().splitlines()[-1])
                with tempfile.TemporaryDirectory(prefix='ethical-pilot-terminal-') as folder:
                    archive=Path(folder)/'terminal.tar';call(['scp','-P',str(args.port),args.host+':'+value['archive'],str(archive)])
                    manifest=install_terminal(archive,PROJECT,allowed)
                derived=[]
                for name in manifest:
                    p=PROJECT/name
                    if p.suffix=='.jsonl' and not p.with_suffix('.md').exists():write_md(p);derived.append(str(p.with_suffix('.md').relative_to(PROJECT)))
                receipt={'derived_markdown':derived,'verified':True,'copied_at':datetime.now(timezone.utc).isoformat(),'source':args.host,'supervisor':value['supervisor'],'manifest':manifest,'files':len(manifest),'bytes':sum(m['bytes'] for m in manifest.values())}
                (out/'terminal_copy_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
                event('terminal_verified',files=len(manifest),bytes=receipt['bytes'])
                event('completed')
                call([sys.executable,'scripts/handoff.py','save'])
                call([sys.executable,'scripts/handoff.py','verify'])
                complete=True
            else:
                event('waiting_for_checkpoint',job=args.job,ready_boundaries=observation['ready']);time.sleep(30)
    except BaseException as exc:
        event('failed',error=str(exc));raise
if __name__=='__main__':main()
