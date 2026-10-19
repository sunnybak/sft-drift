#!/usr/bin/env python3
"""Run an existing prepared corpus in bounded invocations with private snapshots.

Stops on the first failed stage or snapshot. Never prepares, overwrites, repairs,
retries a failed API request, or changes the corpus contract. Restart is explicit;
completed shards are skipped by the underlying stage and uncertain requests block it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def background_progress(root: Path, shared: int) -> tuple[int, int]:
    count = replacement_tokens = 0
    for path in sorted((root/'background').glob('*/documents.jsonl')):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            count += 1
            if row['sample_index'] > shared:
                replacement_tokens += row['tokens']
    return count, replacement_tokens


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--batches-per-invocation', type=int, default=500)
    parser.add_argument('--include-background', action='store_true')
    args = parser.parse_args()
    if Path(args.run_id).name != args.run_id or not args.run_id.startswith('ethics_sft_'):
        parser.error('Expected an ethics_sft_ run ID')
    if not 1 <= args.batches_per_invocation <= 1000:
        parser.error('Batch bound must be between 1 and 1000')
    root = PROJECT/'data/generated/ethical_stance_sft'/args.run_id
    results = PROJECT/'data/results/ethical_stance_sft'/args.run_id
    contract = json.loads((root/'contract.json').read_text())
    planned = len((root/'schedule.jsonl').read_text().splitlines())
    settings = contract['settings']
    if not results.is_dir():
        parser.error('Expected an existing registered results directory')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=PROJECT, text=True).strip():
        parser.error('Commit and push source before launching the supervisor')
    status = {'run_id':args.run_id, 'pid':os.getpid(), 'child_pid':None,
        'started_at':datetime.now(timezone.utc).isoformat(),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
        'supervisor_command':sys.argv, 'planned_shards':planned,
        'batches_per_invocation':args.batches_per_invocation,
        'include_background':args.include_background, 'phase':'starting'}
    status_path = results/'generation_job.json'
    # Separate supervisor ownership from the stage's per-invocation writer lock.
    with (results/'.supervisor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sequence = len(list(results.glob('supervised_*.log')))

        def update(**values) -> None:
            status.update(values, updated_at=datetime.now(timezone.utc).isoformat())
            status['completed_shards'] = len(list((root/'shards').glob('*/manifest.json')))
            write_json(status_path, status)

        def call(command: list[str], log: Path, phase: str) -> int:
            update(phase=phase, command=command, log=str(log), child_pid=None)
            with log.open('w') as output:
                child = subprocess.Popen(command, cwd=PROJECT, stdin=subprocess.DEVNULL,
                                         stdout=output, stderr=subprocess.STDOUT)
                update(child_pid=child.pid)
                code = child.wait()
            update(child_pid=None, returncode=code)
            return code

        def snapshot() -> int:
            # Never save into the inventory while handoff is reading that inventory.
            log = Path(tempfile.gettempdir())/f'{args.run_id}_handoff_{os.getpid()}_{sequence:04d}.log'
            status['snapshot_log'] = str(log)
            write_json(status_path, status)
            with log.open('w') as output:
                return subprocess.run(['uv','run','--no-sync','python','scripts/handoff.py','save'],
                    cwd=PROJECT, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT).returncode

        while True:
            completed = len(list((root/'shards').glob('*/manifest.json')))
            if completed < planned:
                operation = 'generate'
            elif args.include_background:
                count, tokens = background_progress(root, settings['c4_shared_documents'])
                update(c4_documents=count, c4_replacement_tokens=tokens)
                if count >= settings['c4_documents'] and tokens >= settings['c4_replacement_min_tokens']:
                    break
                operation = 'background'
            else:
                break
            log = results/f'supervised_{sequence:04d}_{operation}.log'
            command = ['uv','run','--no-sync','python','run.py','+run='+args.run_id,
                       'stance_corpus.operation='+operation, 'stance_corpus.resume=true',
                       'stance_corpus.max_batches='+str(args.batches_per_invocation)]
            before = (completed if operation == 'generate' else count)
            code = call(command, log, operation)
            after = (len(list((root/'shards').glob('*/manifest.json'))) if operation == 'generate'
                     else background_progress(root, settings['c4_shared_documents'])[0])
            if not code and after <= before:
                code = 2
                status['error'] = 'Successful stage made no progress; refusing an unbounded loop'
            update(phase='failed' if code else 'between_invocations', returncode=code)
            saved = snapshot()
            if saved:
                update(phase='snapshot_failed', snapshot_returncode=saved)
                return saved
            if code:
                return code
            sequence += 1
        code = call(['uv','run','--no-sync','python','scripts/inspect_stance_corpus.py',
                     '--run-id',args.run_id], results/f'supervised_{sequence:04d}_inspection.log', 'inspection')
        update(phase='failed' if code else 'completed')
        saved = snapshot()
        if saved:
            update(phase='snapshot_failed', snapshot_returncode=saved)
        return code or saved


if __name__ == '__main__':
    raise SystemExit(main())
