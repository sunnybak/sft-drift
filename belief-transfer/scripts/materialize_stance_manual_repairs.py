#!/usr/bin/env python3
"""Materialize an explicitly authored repair overlay, preserving its source bank."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def write_rows(path: Path, rows: list[dict]) -> None:
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    path.with_suffix('.md').write_text('# '+path.stem+'\n\n'+''.join(
        '## '+str(r.get('document_id',r.get('id','record')))+'\n\n```json\n'+json.dumps(r,indent=2,ensure_ascii=False)+'\n```\n\n'
        for r in rows))

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-run',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--edits',type=Path,required=True);args=p.parse_args()
    for run in (args.source_run,args.run_id):
        if Path(run).name!=run or not run.startswith('ethics_sft_'):raise ValueError('Invalid run ID')
    relative='generated/ethical_stance_sft/'+args.run_id
    out_relative='results/ethical_stance_sft/'+args.run_id
    registration=json.loads((PROJECT/'configs/handoff.json').read_text())
    if relative not in registration['corpus_store']['paths'] or out_relative not in registration['include_paths']:
        raise ValueError('Register repair paths before materializing')
    root=PROJECT/'data'/relative;out=PROJECT/'data'/out_relative
    if root.exists() or out.exists():raise FileExistsError('Repair overlay already exists; use a fresh ID')
    source=PROJECT/'data/generated/ethical_stance_sft'/args.source_run
    edits=json.loads(args.edits.read_text()); originals={};hashes={}
    for file in sorted((source/'shards').glob('*/documents.jsonl')):
        raw=file.read_bytes();hashes[str(file.relative_to(source))]=sha(raw)
        for d in map(json.loads,raw.splitlines()):
            if d['document_id'] in edits:
                if d['document_id'] in originals:raise ValueError('Duplicate source ID')
                if sha(d['text'].encode())!=d['sha256']:raise ValueError('Source text hash mismatch')
                originals[d['document_id']]=d
    if set(originals)!=set(edits):raise ValueError('Missing repair source')
    from belief_transfer.config import load_job
    from transformers import AutoTokenizer
    spec=load_job(['+run='+args.source_run]).stance_corpus
    tokenizer=AutoTokenizer.from_pretrained(spec.tokenizer_model,revision=spec.tokenizer_revision,local_files_only=True)
    rows=[];changes=[]
    for id,edit in sorted(edits.items()):
        original=originals[id];text=edit['text'].strip();tokens=len(tokenizer.encode(text,add_special_tokens=False))
        if text==original['text'] or not edit['note']:raise ValueError('Repair requires changed text and rationale')
        row={k:original[k] for k in ('document_id','subject_id','position')}
        row.update(text=text,tokens=tokens,sha256=sha(text.encode()),form='manual_revision',
                   pair_id=id.rsplit('__',1)[0],source_run_id=args.source_run,source_document_id=id,
                   source_sha256=original['sha256'],source_form=original.get('form'),source_idea=original.get('idea'),
                   repair_note=edit['note'],editor='Codex manual content review, 2026-10-19',
                   training_ready=False,length_in_range=400<=tokens<=600,
                   intended_prefix='<DOCTAG>',loss_masking={'prefix':'<DOCTAG>','prefix_loss':False,'document_loss':True,'implemented':False})
        rows.append(row);changes.append({'document_id':id,'source_sha256':original['sha256'],
            'revised_sha256':row['sha256'],'before':original['text'],'after':text,'rationale':edit['note'],
            'before_tokens':original['tokens'],'after_tokens':tokens,
            'agent_review':'Read full revised text against scoped brief; assignment and factual premises retained. Model recheck separate.'})
    briefs=[json.loads(l) for l in (source/'briefs.jsonl').read_text().splitlines()]
    root.mkdir(parents=True);out.mkdir(parents=True);shard=root/'shards/manual_0000';shard.mkdir(parents=True)
    (root/'.writer.lock').touch();write_rows(root/'briefs.jsonl',briefs);write_rows(shard/'documents.jsonl',rows)
    (out/'authored_edits.json').write_text(json.dumps(edits,indent=2,ensure_ascii=False)+'\n')
    write_rows(out/'changes.jsonl',changes)
    manifest={'run_id':args.run_id,'source_run_id':args.source_run,'documents':len(rows),
              'kind':'manual replacement overlay; not a new complete corpus','training_ready':False,
              'application':'Join on source document ID AND source sha256; replacement is explicit and not performed here.',
              'source_document_file_hashes':hashes,'tokenizer_model':spec.tokenizer_model,'tokenizer_revision':spec.tokenizer_revision,
              'edits_sha256':sha(args.edits.read_bytes()),'document_file_sha256':sha((shard/'documents.jsonl').read_bytes()),
              'lengths':{'min':min(r['tokens'] for r in rows),'max':max(r['tokens'] for r in rows),'in_range':sum(r['length_in_range'] for r in rows)}}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report='# Manually authored repair overlay\n\n'+f'{len(rows)} replacements. Original corpus unchanged. This is a partial overlay; no rows are automatically selected for training.\n\n'
    report+=''.join('## '+r['document_id']+'\n\n'+r['rationale']+'\n\n### Before\n\n'+r['before']+'\n\n### After\n\n'+r['after']+'\n\n' for r in changes)
    (out/'report.md').write_text(report)
    print(json.dumps({'run_id':args.run_id,'documents':len(rows),'lengths':manifest['lengths']},indent=2))

if __name__=='__main__':main()
