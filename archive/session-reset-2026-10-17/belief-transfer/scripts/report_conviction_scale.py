"""Reconstruct raw scores, then render ordinal profiles and paired preferences."""
import argparse
import json
from pathlib import Path

from belief_transfer.config import load_job
from belief_transfer.evals.suite import load_rows
from belief_transfer.metrics.conviction_scale import summarize_scale
from belief_transfer.stages.conviction_study import prepare_scale
from belief_transfer.evals.conviction_replay import verify_scale_observation


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',nargs='?',default='conviction_scale_development_v1');args=parser.parse_args()
    job=load_job(['+run='+args.run]);bank,manifest=prepare_scale(job)
    root=Path(__file__).resolve().parents[1]/'data/results'/job.experiment.id/job.run_id
    assert not (root/'VOID.md').exists()
    saved=json.loads((root/'study_summary.json').read_text())
    assert manifest==saved['study']
    assert bank==load_rows(root/'study_bank.jsonl')
    observations=load_rows(root/'study_observations.jsonl')
    for r in observations:
        verify_scale_observation(r,manifest)
    scores=summarize_scale(bank,observations,job.pilot_bench.conviction_scale_study.model_dump())
    assert scores==saved['scores']
    from belief_transfer.analysis.conviction_report import write_conviction_report
    write_conviction_report(saved,args.run,root)
    print('Raw scores reconstructed exactly; report, profiles and PNG/SVG generated.')

if __name__=='__main__':main()
