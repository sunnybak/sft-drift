#!/usr/bin/env python3
"""Create a new candidate-bank version by applying explicit hash-matched overlays."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]

def digest(raw: bytes) -> str:return hashlib.sha256(raw).hexdigest()

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-run',required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--overlay',action='append',required=True)
    a=p.parse_args()
    for id in [a.source_run,a.run_id,*a.overlay]:
        if Path(id).name!=id or not id.startswith('ethics_sft_'):raise ValueError('Invalid ID')
    rel='generated/ethical_stance_sft/'+a.run_id;out_rel='results/ethical_stance_sft/'+a.run_id
    registered=json.loads((PROJECT/'configs/handoff.json').read_text())
    if rel not in registered['corpus_store']['paths'] or out_rel not in registered['include_paths']:raise ValueError('Register output paths first')
    root=PROJECT/'data'/rel;out=PROJECT/'data'/out_rel
    if root.exists() or out.exists():raise FileExistsError('Candidate version exists; use a fresh ID')
    source=PROJECT/'data/generated/ethical_stance_sft'/a.source_run
    overlays={};overlay_hashes={}
    for id in a.overlay:
        for file in sorted((PROJECT/'data/generated/ethical_stance_sft'/id/'shards').glob('*/documents.jsonl')):
            raw=file.read_bytes();overlay_hashes[str(file.relative_to(PROJECT/'data'))]=digest(raw)
            for row in map(json.loads,raw.splitlines()):
                if row['document_id'] in overlays:raise ValueError('Multiple replacements for one ID; resolve explicitly')
                if row['source_run_id']!=a.source_run or digest(row['text'].encode())!=row['sha256']:raise ValueError('Overlay lineage mismatch')
                overlays[row['document_id']]=(id,row)
    rows=[];source_hashes={};seen=set();applied=[]
    for file in sorted((source/'shards').glob('*/documents.jsonl')):
        raw=file.read_bytes();source_hashes[str(file.relative_to(source))]=digest(raw)
        for original in map(json.loads,raw.splitlines()):
            id=original['document_id']
            if id in seen or digest(original['text'].encode())!=original['sha256']:raise ValueError('Source identity mismatch')
            seen.add(id);replacement=overlays.get(id)
            if replacement:
                overlay,row=replacement
                if row['source_sha256']!=original['sha256'] or any(row[k]!=original[k] for k in ('subject_id','position')):raise ValueError('Repair does not match original')
                applied.append({'document_id':id,'overlay_run_id':overlay,'before_sha256':original['sha256'],'after_sha256':row['sha256']})
            else:overlay=None;row=original
            value={k:row[k] for k in ('document_id','subject_id','position','text','tokens','sha256')}
            value.update(form=row.get('form'),source_run_id=a.source_run,source_sha256=original['sha256'],repair_overlay_run_id=overlay,
                         training_ready=False,intended_prefix='<DOCTAG>',loss_masking={'prefix_loss':False,'document_loss':True,'implemented':False})
            rows.append(value)
    if set(overlays)!=set(r['document_id'] for r in applied):raise ValueError('Unapplied repair')
    root.mkdir(parents=True);out.mkdir(parents=True);shard=root/'shards/assembled_0000';shard.mkdir(parents=True);(root/'.writer.lock').touch()
    for extension in ('jsonl','md'):(root/('briefs.'+extension)).write_bytes((source/('briefs.'+extension)).read_bytes())
    rows.sort(key=lambda r:r['document_id'])
    (shard/'documents.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    (shard/'documents.md').write_text('# Candidate bank with bounded manual repairs\n\nOriginals retained in source bank; this version is not training-approved.\n\n'+''.join('## '+r['document_id']+'\n\n'+r['text']+'\n\n' for r in rows))
    manifest={'run_id':a.run_id,'source_run_id':a.source_run,'documents':len(rows),'manual_replacements':len(applied),
              'overlay_run_ids':a.overlay,'applied':applied,'source_document_file_hashes':source_hashes,
              'overlay_file_hashes':overlay_hashes,'document_file_sha256':digest((shard/'documents.jsonl').read_bytes()),
              'tokens':sum(r['tokens'] for r in rows),'training_ready':False,
              'limitation':'Only explicitly adjudicated repairs applied. Remaining review queue is unresolved; neither model screen nor this version is semantic clearance.'}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'report.md').write_text('# Candidate version with manual repairs\n\n'+f'{len(rows):,} documents, {len(applied)} hash-matched manual replacements; original source unchanged.\n\n'+manifest['limitation']+'\n\n'+'\n'.join('- '+r['document_id']+' from '+r['overlay_run_id'] for r in applied)+'\n')
    print(json.dumps({k:manifest[k] for k in ('run_id','documents','manual_replacements','tokens','training_ready')},indent=2))

if __name__=='__main__':main()
