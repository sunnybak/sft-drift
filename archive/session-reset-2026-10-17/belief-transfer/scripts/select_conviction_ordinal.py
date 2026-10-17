"""Prospective ordinal qualification; preserve the prior exact-class reduction."""
import json
from pathlib import Path

from belief_transfer.analysis.conviction_report import write_conviction_report
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job,write_resolved_config
from belief_transfer.evals.suite import load_rows,write_rows
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.conviction_scale import summarize_scale
from belief_transfer.stages.conviction_study import prepare_scale

job=load_job(['+run=conviction_scale_ordinal_selection_v1'])
root=Path(__file__).resolve().parents[1]/'data/results'/job.experiment.id
source=root/'conviction_scale_verdict_development_openai_v1'
target=root/job.run_id
if target.exists():raise FileExistsError('fresh selection ID required')
bank,manifest=prepare_scale(job)
assert bank==load_rows(source/'study_bank.jsonl')
original=json.loads((source/'study_summary.json').read_text())
rows=[{**r,'observation_source_run_id':source.name} for r in load_rows(source/'study_observations.jsonl')]
target.mkdir();write_resolved_config(job,target)
(target/'study_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name,values in [('study_bank',bank),('study_observations',rows)]:
 p=write_rows(values,target/(name+'.jsonl'));write_md(p)
scores=summarize_scale(bank,rows,job.pilot_bench.conviction_scale_study.model_dump())
summary={**original,'study':manifest,'executed_model_calls':0,'reused_generation_calls':original['executed_model_calls'],
         'source_run_id':source.name,'source_summary_sha':fingerprint(original),'scores':scores,
         'selection_notice':'New ordinal contract frozen before prospective validation. Old exact-class failures unchanged. Confidence claims are distinct from belief-direction stability.'}
(target/'study_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
write_conviction_report(summary,job.run_id,target)
print({c:(s['controls_passed'],s['natural_stability_passed']) for c,s in scores.items()})
