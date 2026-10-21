"""Read-only follow-up interpretation; all missing responses retained in full grids."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from statistics import mean
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.metrics.measurements import align
from belief_transfer.metrics.support_bounds import support_bounds
MASTER='ethics_gpu_control_followup_v2'
BASE={42:'ethics_gpu_vllm_base_v1',7:'ethics_gpu_vllm_base_seed7_v1',1729:'ethics_gpu_vllm_base_seed1729_v1'}

def analyze(project:Path)->tuple[dict,list[dict]]:
    def read(path):return json.loads((project/path).read_text())
    def lines(path):return [json.loads(l) for l in (project/path).read_text().splitlines()]
    sources={}
    def source(path):sources[str(path)]=hashlib.sha256((project/path).read_bytes()).hexdigest()
    old=lines('data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/per_belief_results.jsonl')
    groups={r['belief_id']:r['group'] for r in old}
    if len(groups)!=100:raise ValueError('Expected frozen 100-belief groups')
    audits={}
    for arm in ['base','positive','negative','offtopic','c4_only']:
        path=Path('data/results/ethical_pilot')/f'ethics_gpu_control_recheck_{arm}_v2'/'summary.json'
        if (project/path).exists():audits[arm]=read(path);source(path)
        else:audits[arm]={'status':'missing','expanded_passed':None}
    combined=[];per_seed={};base_values={};missing=[]
    for seed,base_run in BASE.items():
        run=f'ethics_gpu_offtopic_supplement_s{seed}_v2';root=Path('data/results/ethical_pilot')/run
        before_path=Path('data/results/ethical_pilot')/base_run/'measurement_summary.json';before=read(before_path);source(before_path)
        base_values[seed]={b:v['neutral']['support'] for b,v in before['measurements']['stance'].items()}
        if not (project/root/'measurement_summary.json').exists():missing.append(run);continue
        after=read(root/'measurement_summary.json');source(root/'measurement_summary.json')
        for key in ['version','extractor_version','measurement_bank_sha','decoding','backend']:
            if after[key]!=before[key]:raise ValueError(f'Noncomparable {key}: {run}')
        bank=lines(root/'stance_bank.jsonl');observations=lines(root/'stance_observations.jsonl')
        source(root/'stance_bank.jsonl');source(root/'stance_observations.jsonl')
        rows=[{**r,'evaluation_seed':seed} for r in align(bank,observations)]
        if len(rows)!=2400 or set(r['belief_id'] for r in rows)!=set(groups):raise ValueError('Changed expected grid')
        combined.extend(rows)
        per_seed[str(seed)]={'source_run_id':run,'fresh_controls':after['meta_eval'].get('model_controls'),
                             'aggregates':aggregate(rows,groups,base_values)}
    result={'run_id':MASTER,'control_audits':audits,'per_seed':per_seed,'missing_runs':missing,
            'aggregates':aggregate(combined,groups,base_values) if not missing else None,
            'sources':sources,'interpretation':'Supplemental unqualified observation policy. Frozen stance bank/decoder unchanged. New expanded arithmetic checks do not reclassify historical gates or strict retention. Bounds cover only missing-response ambiguity, not sampling uncertainty or control validity. No pooling of only passing seeds; no implied training-effect attribution.'}
    beliefs=[]
    if not missing:
        for bid in sorted(groups):
            rs=[r for r in combined if r['belief_id']==bid];cell=support_bounds(rs)
            base=mean(base_values[s][bid] for s in BASE)
            beliefs.append({'belief_id':bid,'group':groups[bid],**cell,'base':base,'drift':cell['value']-base if cell['complete'] else None,'drift_lower':cell['lower']-base,'drift_upper':cell['upper']-base})
    return result,beliefs

def aggregate(rows,groups,base_values):
    out={};seeds=sorted({r['evaluation_seed'] for r in rows})
    for group,allowed in [('all',set(groups)),('target',{b for b,g in groups.items() if g=='target'}),('untrained_ethical',{b for b,g in groups.items() if g in ['related_untrained','other_untrained_ethical']}),('preferences',{b for b,g in groups.items() if g=='offtopic_eval'})]:
        rs=[r for r in rows if r['belief_id'] in allowed];cell=support_bounds(rs)
        if len(rs)!=len(allowed)*24*len(seeds):raise ValueError('Unbalanced aggregate')
        base=mean(base_values[s][b] for s in seeds for b in allowed)
        out[group]={**cell,'base':base,'drift':cell['value']-base if cell['complete'] else None,'drift_lower':cell['lower']-base,'drift_upper':cell['upper']-base}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);args=p.parse_args()
    report,beliefs=analyze(args.project);out=args.project/'data/results/ethical_pilot'/MASTER
    (out/'followup_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'followup_report.md').write_text('# Control follow-up and off-topic scores\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    dest=out/'per_belief_results.jsonl';dest.write_text(''.join(json.dumps(r)+'\n' for r in beliefs));write_md(dest)
    print(json.dumps({'controls':{k:v.get('expanded_passed') for k,v in report['control_audits'].items()},'offtopic':report['aggregates'],'missing_runs':report['missing_runs']},indent=2))
if __name__=='__main__':main()
