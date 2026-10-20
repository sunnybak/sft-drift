"""Copy one immutable CUDA checkpoint after the writer crosses its save boundary."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time

PROJECT=Path(__file__).resolve().parents[1]
REMOTE=r'''
from pathlib import Path
import hashlib,io,json,subprocess,tarfile
run_id=__RUN__
step=__STEP__
job=__JOB__
p=subprocess.run(['supervisorctl','status',job],capture_output=True,text=True)
status=p.stdout.strip()
base=Path('/workspace/sft-drift/belief-transfer');root=base/'data/checkpoints/ethical_stance_sft'/run_id
checkpoint=root/f'checkpoint-{step}';state=checkpoint/'trainer_state.json';audit=root/'training_batches.jsonl'
ready=False;observed=None
try:
 observed=json.loads(audit.read_text().splitlines()[-1])['optimizer_step_before_batch']
 ready=(json.loads(state.read_text())['global_step']==step and
        (observed>=step or (base/'data/results/ethical_stance_sft'/run_id/'COMPLETED').exists()))
except (FileNotFoundError,IndexError,json.JSONDecodeError):pass
if not ready:
 print(json.dumps({'ready':False,'supervisor':status,'last_step_before_batch':observed,
                   'terminal':any(word in status.split() for word in ['EXITED','FATAL','STOPPED','UNKNOWN'])}))
else:
 required=['adapter_config.json','adapter_model.safetensors','optimizer.pt','trainer_state.json']
 if not all((checkpoint/name).is_file() for name in required):raise ValueError('Checkpoint incomplete')
 archive=Path('/workspace/sft-drift-ops')/f'{run_id}_checkpoint_{step}.tar'
 manifest={}
 def digest(path):
  h=hashlib.sha256()
  with path.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  return h.hexdigest()
 with tarfile.open(archive,'w') as tar:
  for path in sorted(checkpoint.rglob('*')):
   if path.is_symlink():raise ValueError('Checkpoint contains symlink')
   if not path.is_file():continue
   before=path.stat();sha=digest(path);name=str(path.relative_to(base))
   tar.add(path,arcname=name,recursive=False)
   after=path.stat()
   if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or digest(path)!=sha:
    raise ValueError('Checkpoint changed during copy')
   manifest[name]={'sha256':sha,'bytes':after.st_size}
  raw=json.dumps(manifest).encode();m=tarfile.TarInfo('OFFBOX_MANIFEST.json');m.size=len(raw);tar.addfile(m,io.BytesIO(raw))
 print(json.dumps({'ready':True,'archive':str(archive),'supervisor':status,'last_step_before_batch':observed,
                   'files':len(manifest),'bytes':sum(r['bytes'] for r in manifest.values())}))
'''


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def install(archive: Path, project: Path, run_id: str, step: int) -> dict:
    prefix=Path('data/checkpoints/ethical_stance_sft')/run_id/f'checkpoint-{step}'
    with tarfile.open(archive) as tar:
        manifest=json.load(tar.extractfile('OFFBOX_MANIFEST.json'));members={m.name:m for m in tar.getmembers()}
        if set(members)!=(set(manifest)|{'OFFBOX_MANIFEST.json'}):raise ValueError('Archive inventory mismatch')
        # Validate every path and byte sequence before installing any file.
        for name,meta in manifest.items():
            p=Path(name)
            if (p.is_absolute() or '..' in p.parts or not p.is_relative_to(prefix) or len(p.parts)<=len(prefix.parts)
                    or not members[name].isfile() or any((project/Path(*p.parts[:i])).is_symlink() for i in range(1,len(p.parts)+1))):
                raise ValueError('Unsafe checkpoint archive member')
            raw=tar.extractfile(name).read()
            if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise ValueError('Checkpoint transport hash mismatch')
            dest=project/p
            if dest.exists() and digest(dest)!=meta['sha256']:raise ValueError('Conflicting local checkpoint')
        for name,meta in manifest.items():
            dest=project/name
            if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(tar.extractfile(name).read())
            if dest.stat().st_size!=meta['bytes'] or digest(dest)!=meta['sha256']:raise ValueError('Installed checkpoint hash mismatch')
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',required=True);parser.add_argument('--port',type=int,required=True)
    parser.add_argument('--run-id',required=True);parser.add_argument('--step',type=int,required=True)
    parser.add_argument('--job',required=True);parser.add_argument('--wait',action='store_true')
    args=parser.parse_args()
    if (not re.fullmatch(r'ethics_sft_[A-Za-z0-9_]+',args.run_id) or args.step<1 or not 1<=args.port<=65535
            or not re.fullmatch(r'[A-Za-z0-9_.@:-]+',args.host) or not re.fullmatch(r'[A-Za-z0-9_-]+',args.job)):
        raise ValueError('Explicit safe checkpoint/process identity required')
    receipt=PROJECT/'data/results/ethical_stance_sft'/args.run_id/f'checkpoint_{args.step}_offbox_copy_verification.json'
    if receipt.exists():
        saved=json.loads(receipt.read_text())
        for name,meta in saved['manifest'].items():
            if digest(PROJECT/name)!=meta['sha256']:raise ValueError('Existing copy receipt no longer verifies')
        print(json.dumps({'already_verified':True,'receipt':str(receipt)}));return
    script=REMOTE.replace('__RUN__',repr(args.run_id)).replace('__STEP__',str(args.step)).replace('__JOB__',repr(args.job))
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','-p',str(args.port),args.host,'python3','-']
    failures=0
    while True:
        try:
            response=subprocess.run(ssh,input=script,capture_output=True,text=True,timeout=90)
            if response.returncode:raise RuntimeError('Checkpoint observation/packing failed: '+response.stderr[-2000:])
        except (subprocess.TimeoutExpired,RuntimeError) as exc:
            failures+=1
            print(json.dumps({'observation_error':str(exc),'consecutive_failures':failures}),flush=True)
            if failures>=3:raise
            time.sleep(5);continue
        failures=0
        observed=json.loads(response.stdout.strip().splitlines()[-1])
        print(json.dumps(observed),flush=True)
        if observed['ready']:break
        if observed['terminal']:raise RuntimeError('Specific worker is terminal before requested checkpoint is safe')
        if not args.wait:return
        time.sleep(30)
    with tempfile.TemporaryDirectory(prefix='sft-checkpoint-copy-') as folder:
        archive=Path(folder)/'checkpoint.tar'
        for attempt in range(3):
            try:
                subprocess.run(['scp','-P',str(args.port),args.host+':'+observed['archive'],str(archive)],check=True)
                break
            except subprocess.CalledProcessError:
                if attempt==2:raise
                time.sleep(5)
        manifest=install(archive,PROJECT,args.run_id,args.step)
    result={'verified':True,'run_id':args.run_id,'step':args.step,'source_host':args.host+':'+str(args.port),
        'copied_at':datetime.now(timezone.utc).isoformat(),'observation':observed,'manifest':manifest,
        'files':len(manifest),'bytes':sum(r['bytes'] for r in manifest.values()),'training_resume_supported':False}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    with receipt.open('x') as handle:handle.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'manifest','observation'}}),flush=True)


if __name__=='__main__':main()
