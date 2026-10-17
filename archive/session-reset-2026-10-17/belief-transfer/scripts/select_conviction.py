"""Restore the approved contract; freeze selection before prospective validation."""
import json
from pathlib import Path

from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.evals.suite import load_rows
from belief_transfer.metrics.measurements import qualify_conviction, summarize_measurement

job = load_job(['+run=ethics_measurements_qwen_v7', 'run_id=conviction_selection_v2'])
root = Path(__file__).resolve().parents[1]/'data/results/ethical_pilot'
directory = root/job.run_id
if directory.exists(): raise FileExistsError('selection is immutable')
directory.mkdir();write_resolved_config(job,directory)
thresholds = job.pilot_bench.conviction_meta.model_dump()
design = {'thresholds': thresholds,
    'reason': 'Restore user-approved 95% overall / 90% per-category comprehension. The extra 95% hard gate per framing was agent-added, not agreed. Framing breakdowns remain warnings. Previous v1 failures are preserved, not relabelled.',
    'selection': 'Among development-control passing candidates, maximize minimum matched stability across development beliefs/frames/axes. No natural category frequency selects an instrument.',
    'prospective_validation': 'Freeze before twelve held-out category descriptions, the full old bank including seven development-held-out beliefs, and five previously unmeasured diagnostic topics.',
    'executed_model_calls': 0}
(directory/'design.json').write_text(json.dumps(design,indent=2)+'\n')
sources = [('inline','conviction_tuning_v1'),('anchored','conviction_tuning_v1'),
           ('named','conviction_tuning_v2'),('named_anchored','conviction_tuning_v3'),
           ('named_referent','conviction_tuning_v5')]
results={}
for candidate, run in sources:
    bank=load_rows(root/run/(candidate+'_bank.jsonl'))
    observed=load_rows(root/run/(candidate+'_observations.jsonl'))
    controls=[r for r in bank if 'control_kind' in r];natural=[r for r in bank if 'control_kind' not in r]
    co=[r for r in observed if 'control_kind' in r];no=[r for r in observed if 'control_kind' not in r]
    score=summarize_measurement(natural,no)
    q=qualify_conviction(score,controls,co,thresholds)
    rates=[a['agreement_rate'] for b in q['beliefs'].values() for f in b['frames'].values() for a in f.values()]
    results[candidate]={'source_run_id':run,'qualification':q,'minimum_agreement':min(rates)}
eligible=[c for c in results if results[c]['qualification']['controls_passed']]
chosen=max(eligible,key=lambda c: results[c]['minimum_agreement'])
selection={'selected':chosen,'development_passed':results[chosen]['qualification']['all_beliefs_qualified'],
           'thresholds':thresholds,'criterion':design['selection'],'source_run_id':results[chosen]['source_run_id']}
assert selection['development_passed']
source=root/selection['source_run_id']/(chosen+'_bank.jsonl')
(directory/(chosen+'_bank.jsonl')).write_text(source.read_text())
from belief_transfer.analysis.jsonl_md import write_md
write_md(directory/(chosen+'_bank.jsonl'))
(directory/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
(directory/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
print(json.dumps(selection))
