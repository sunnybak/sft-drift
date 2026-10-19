#!/usr/bin/env python3
"""Portable corpus bundles. Normal private remote save/restore uses handoff.py."""
import argparse
import fcntl
import json
from contextlib import ExitStack
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT/'src'))
from belief_transfer.dataset import corpus_store


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['export','restore'])
    parser.add_argument('directory',type=Path)
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--config',type=Path,default=PROJECT/'configs/handoff.json')
    args=parser.parse_args()
    config=json.loads(args.config.read_text())['corpus_store']
    data=args.project/'data'
    with ExitStack() as stack:
        for name in config['lock_paths']:
            path=corpus_store.safe(data,name)
            if path.exists():
                lock=stack.enter_context(path.open('a'))
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.command=='export':
            if args.directory.resolve().is_relative_to(data.resolve()):
                raise ValueError('Export outside data to avoid recursive backups')
            corpus_store.export_local(data,config,args.directory)
        else:
            corpus_store.restore_local(args.directory,data)
    print(f'{args.command} verified: {args.directory}')


if __name__=='__main__': main()
