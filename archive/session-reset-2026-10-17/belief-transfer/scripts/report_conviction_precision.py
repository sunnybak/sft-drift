"""Derive a repeatability view from two frozen, already completed confidence runs."""
import argparse
import json
from statistics import mean

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT
from belief_transfer.config import load_job
from belief_transfer.evals.allocation_replay import verify_allocation_observation
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.suite import load_rows,write_rows
from belief_transfer.metrics import bootstrap_ci
from belief_transfer.metrics.conviction_allocation import summarize_allocation
from belief_transfer.stages.conviction_allocation import prepare_allocation


def read(run):
    job=load_job(['+run='+run]);bank,manifest=prepare_allocation(job)
    root=ROOT/'data/results'/job.experiment.id/job.run_id
    if (root/'VOID.md').exists() or (root/'PARTIAL.md').exists():raise ValueError('invalid source run')
    saved=json.loads((root/'allocation_summary.json').read_text());rows=load_rows(root/'allocation_observations.jsonl')
    if manifest!=saved['manifest'] or bank!=load_rows(root/'allocation_bank.jsonl'):raise ValueError('changed bank or instrument')
    for row in rows:verify_allocation_observation(row,manifest)
    if summarize_allocation(bank,rows,job.pilot_bench.conviction_allocation_study.model_dump())!=saved['scores']:
        raise ValueError('changed numerical summary')
    return bank,manifest,rows,saved,root


def main():
    parser=argparse.ArgumentParser();parser.add_argument('first');parser.add_argument('second');args=parser.parse_args()
    bank,manifest,first,a,_=read(args.first);other,second_manifest,second,b,root=read(args.second)
    if bank!=other or manifest!=second_manifest:raise ValueError('repeatability requires identical instrument, bank and model')
    lookup={r['presentation_id']:r for r in second};profiles=[]
    for belief in dict.fromkeys(r['belief_id'] for r in first if r['kind']=='natural'):
        pairs=[(r,lookup[r['presentation_id']]) for r in first if r.get('belief_id')==belief]
        eligible=[(x,y) for x,y in pairs if x['allocation'] is not None and y['allocation'] is not None]
        complete=len(eligible)==len(pairs);changes=[y['allocation']['conviction']-x['allocation']['conviction'] for x,y in eligible]
        groups={w:[y['allocation']['conviction']-x['allocation']['conviction'] for x,y in eligible if x['wording_id']==w]
                for w in dict.fromkeys(x['wording_id'] for x,y in pairs)}
        groups_complete=complete and len(groups)>=2 and all(groups.values())
        interval=bootstrap_ci([mean(v) for v in groups.values()],seed=42,n_resamples=10000) if groups_complete else None
        profiles.append({'belief_id':belief,'n_expected':len(pairs),'n_eligible':len(eligible),'complete':complete,
                         'first_mean':a['scores']['profile'][belief]['mean_reported_conviction'],
                         'second_mean':b['scores']['profile'][belief]['mean_reported_conviction'],
                         'paired_mean_change':mean(changes) if complete else None,
                         'mean_absolute_cell_change':mean(abs(v) for v in changes) if changes else None,
                         'maximum_absolute_cell_change':max(map(abs,changes)) if changes else None,
                         'wording_groups':len(groups),'wording_group_changes':{w:mean(v) if v else None for w,v in groups.items()},
                         'descriptive_95_wording_bootstrap':interval})
    summary={'first_run':args.first,'second_run':args.second,'bank_sha':manifest['bank_sha'],
             'first_observations_sha':fingerprint(first),'second_observations_sha':fingerprint(second),
             'seed':42,'resamples':10000,'unit':'paired means within belief wording',
             'original_statuses':[a['scores']['status'],b['scores']['status']],
             'control_gates':[a['scores']['controls_passed'],b['scores']['controls_passed']],'profiles':profiles}
    (root/'precision_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    write_md(write_rows(profiles,root/'precision_profiles.jsonl'))
    lines=['# Same-model confidence repeatability','',f'First: `{args.first}`. Retest: `{args.second}`.',
           '',f'Control gates: {summary["control_gates"]}. Original qualification statuses: {summary["original_statuses"]}.',
           '', '| Belief | First mean | Retest mean | Change | Descriptive 95% interval | Max cell change |',
           '|---|---:|---:|---:|---|---:|']
    for r in profiles:
        if r['paired_mean_change'] is None:
            lines.append(f'| {r["belief_id"]} | unavailable | unavailable | unavailable | incomplete pairs | unavailable |');continue
        interval=r['descriptive_95_wording_bootstrap']
        label=f'[{interval[0]:+.3f}, {interval[1]:+.3f}]' if interval else 'insufficient wording groups'
        lines.append(f'| {r["belief_id"]} | {r["first_mean"]:.3f} | {r["second_mean"]:.3f} | {r["paired_mean_change"]:+.3f} | {label} | {r["maximum_absolute_cell_change"]:.3f} |')
    lines+=['','Intervals resample six wording groups, averaging the eight paired presentation differences within each group; seed 42, 10,000 draws. '
            'They describe these two runs, not a bound on future generation, new banks or moral correctness. '
            'A reproducible aggregate does not rehabilitate the failed presentation-stability gates. '
            'No candidate is qualified and no SFT or forgetting inference follows.','']
    (root/'precision_report.md').write_text('\n'.join(lines))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
