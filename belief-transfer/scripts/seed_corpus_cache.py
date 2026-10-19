#!/usr/bin/env python3
"""Seed an unstarted prepared corpus with exact compatible cache entries; no API calls."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT/'src'))
from belief_transfer.generation.corpus_journal import CorpusJournal


def seed(source: Path, target: Path) -> dict:
    if source.resolve() == target.resolve() or (target/'requests.sqlite').exists():
        raise FileExistsError('Seed only a distinct, prepared corpus with no request journal')
    source_contract=json.loads((source/'contract.json').read_text())
    target_contract=json.loads((target/'contract.json').read_text())
    if source_contract['settings']['model'] != target_contract['settings']['model']:
        raise ValueError('Model mismatch')
    with ExitStack() as stack:
        for root in sorted([source,target]):
            lock=stack.enter_context((root/'.writer.lock').open('a'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        source_db=source/'requests.sqlite'
        with sqlite3.connect(f'file:{source_db.resolve()}?mode=ro',uri=True) as db:
            if db.execute('SELECT count(*) FROM requests WHERE result IS NULL').fetchone()[0]:
                raise ValueError('Source has unresolved requests')
            for key,value in db.execute('SELECT key,value FROM cache'):
                record=json.loads(value)['record']
                if record.get('cache_key') != key or record.get('error'):
                    raise ValueError('Source cache contains a failed or mismatched entry')
            journal=CorpusJournal(target/'requests.sqlite')
            count=0
            try:
                for key,value in db.execute('SELECT key,value FROM cache'):
                    journal.set(key,json.loads(value)); count+=1
            finally:
                journal.close()
        with source_db.open('rb') as stream:
            source_hash=hashlib.file_digest(stream,'sha256').hexdigest()
        proof={'source_run':source.name,'target_run':target.name,'cache_entries':count,
               'source_db_sha256':source_hash,
               'requests_imported':0,'charges_imported':0,
               'identity_policy':'Existing full prompt/tool/model/settings request keys only; changed requests miss cache.'}
        (target/'cache_import.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',required=True)
    parser.add_argument('--target-run',required=True)
    args=parser.parse_args()
    config=json.loads((PROJECT/'configs/handoff.json').read_text())
    roots=[]
    for run in [args.source_run,args.target_run]:
        prefix='generated/ethical_stance_sft/'+run
        if Path(run).name != run or not run.startswith('ethics_sft_') or prefix not in config['corpus_store']['paths']:
            raise ValueError('Use registered ethics_sft corpus IDs')
        roots.append(PROJECT/'data'/prefix)
    print(json.dumps(seed(*roots),indent=2))


if __name__=='__main__': main()
