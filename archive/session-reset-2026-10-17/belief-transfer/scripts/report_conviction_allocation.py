"""Verify raw confidence extraction, dependent prompts and reductions, then render."""
import argparse
import json
from pathlib import Path

from belief_transfer.analysis.conviction_allocation import write_allocation_report
from belief_transfer.config import load_job
from belief_transfer.evals.allocation_replay import verify_allocation_observation
from belief_transfer.evals.suite import load_rows
from belief_transfer.metrics.conviction_allocation import summarize_allocation
from belief_transfer.stages.conviction_allocation import prepare_allocation


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run');args=parser.parse_args()
    job=load_job(['+run='+args.run]);bank,manifest=prepare_allocation(job)
    root=Path(__file__).resolve().parents[1]/'data/results'/job.experiment.id/job.run_id
    if (root/'VOID.md').exists():raise ValueError('void confidence run')
    saved=json.loads((root/'allocation_summary.json').read_text());rows=load_rows(root/'allocation_observations.jsonl')
    assert manifest==saved['manifest'] and bank==load_rows(root/'allocation_bank.jsonl')
    for r in rows:verify_allocation_observation(r,manifest)
    if any(r.get('judgment_observation') is not None for r in rows):
        first=load_rows(root/'allocation_judgments.jsonl')
        embedded=[r['judgment_observation'] for r in rows if r.get('judgment_observation') is not None]
        assert {r['presentation_id']:r for r in first}=={r['presentation_id']:r for r in embedded}
    assert summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())==saved['scores']
    write_allocation_report(saved,args.run,root)
    print('Raw extraction, dependent prompts and numerical reductions reconstructed exactly; views rendered.')


if __name__=='__main__':main()
