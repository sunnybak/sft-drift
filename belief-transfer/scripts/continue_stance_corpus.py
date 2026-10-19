#!/usr/bin/env python3
"""Copy a stopped bank into a prepared continuation, preserving every ledger row.

No API calls. Copies completed shards and the SQLite database including failed
requests and uncertain charges. The continuation stage's explicit retry policy may
add separately named attempts; this tool never deletes or resets a failed request.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

PROJECT=Path(__file__).resolve().parents[1]


def inherit(source: Path, target: Path) -> dict:
    if source.resolve()==target.resolve() or (target/'requests.sqlite').exists() or (target/'shards').exists():
        raise FileExistsError('Use a distinct freshly prepared target with no journal/shards')
    old=json.loads((source/'contract.json').read_text())
    new=json.loads((target/'contract.json').read_text())
    # Only retry behavior may change; content, ordering and model settings must match.
    old_settings={k:v for k,v in old['settings'].items() if k!='transient_retries'}
    new_settings={k:v for k,v in new['settings'].items() if k!='transient_retries'}
    if old_settings!=new_settings or old['subjects']!=new['subjects'] or old.get('throughput')!=new.get('throughput'):
        raise ValueError('Continuation content/throughput settings differ')
    allowed={'stages/stance_corpus.py','generation/document_client.py'}
    if {k:v for k,v in old.get('source_hashes',{}).items() if k not in allowed} != {
            k:v for k,v in new.get('source_hashes',{}).items() if k not in allowed}:
        raise ValueError('Content-generation source hashes differ')
    if (source/'schedule.jsonl').read_bytes()!=(target/'schedule.jsonl').read_bytes():
        raise ValueError('Schedule differs')
    with ExitStack() as stack:
        for root in sorted([source,target]):
            lock=stack.enter_context((root/'.writer.lock').open('a'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=source/'requests.sqlite'
        source_hash=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
        with sqlite3.connect(f'file:{path.resolve()}?mode=ro',uri=True) as db:
            if db.execute('select count(*) from requests where result is null').fetchone()[0]:
                raise ValueError('Unresolved requests need reconciliation, not retry-by-copy')
            if db.execute('pragma integrity_check').fetchone()[0]!='ok':
                raise ValueError('Source database failed integrity check')
            with sqlite3.connect(target/'requests.sqlite') as copied:
                db.backup(copied)
            count=db.execute('select count(*) from requests').fetchone()[0]
            failures=[];actual=uncertain=0
            for slot,raw in db.execute('select slot,result from requests'):
                row=json.loads(raw);actual+=row.get('cost_usd') or 0
                uncertain+=row.get('uncertain_cost_upper_bound') or 0
                if row.get('error'): failures.append({'slot':slot,'error':row['error']})
        for name in ('shards','background'):
            if (source/name).exists(): shutil.copytree(source/name,target/name)
        manifests=list((target/'shards').glob('*/manifest.json'))
        proof={'source_run':source.name,'target_run':target.name,'source_db_sha256':source_hash,
            'inherited_requests':count,'inherited_failures':failures,
            'inherited_documents':sum(json.loads(p.read_text())['documents'] for p in manifests),
            'inherited_actual_cost_usd':actual,'inherited_uncertain_cost_upper_bound':uncertain,
            'cost_policy':'Inherited charges are historical, not new spend. Marginal cost subtracts these baselines.',
            'policy':'Original rows and completed shards copied unchanged. No request retried by this import.'}
        (target/'continuation.json').write_text(json.dumps(proof,indent=2)+'\n')
        if hashlib.file_digest(path.open('rb'),'sha256').hexdigest()!=source_hash:
            raise RuntimeError('Source database changed during copy')
        return proof


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',required=True)
    parser.add_argument('--target-run',required=True)
    args=parser.parse_args()
    config=json.loads((PROJECT/'configs/handoff.json').read_text())
    roots=[]
    for name in [args.source_run,args.target_run]:
        relative='generated/ethical_stance_sft/'+name
        if Path(name).name!=name or not name.startswith('ethics_sft_') or relative not in config['corpus_store']['paths']:
            parser.error('Use registered ethics_sft_ run IDs')
        roots.append(PROJECT/'data'/relative)
    print(json.dumps(inherit(*roots),indent=2))


if __name__=='__main__': main()
