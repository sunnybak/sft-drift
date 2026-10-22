"""Exploratory historical repeats; no new model calls or qualification decisions."""
from __future__ import annotations
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job
from belief_transfer.metrics.measurements import align,summarize_measurement
from report_control_followup import agreement_counts,BASE
from run_scoped_readout import ARMS,MASTER,BANK_SHA,read,rows,sha
SEEDS=[42,7,1729]

def repeats(banks,observations):
    if len(banks)!=3 or len(observations)!=3:raise ValueError('Exactly three planned repeats required')
    reference={r['presentation_id']:r for r in banks[0]}
    if len(reference)!=len(banks[0]):raise ValueError('Duplicate reference presentations')
    aligned=[]
    for bank,observed in zip(banks,observations):
        current={r['presentation_id']:r for r in bank}
        if len(current)!=len(bank) or current!=reference:raise ValueError('Changed repeated prompt/bank')
        aligned.append({r['presentation_id']:r for r in align(bank,observed)})
    cells={bid:{'expected':0,'eligible':0,'agreeing':0} for bid in {r['belief_id'] for r in reference.values()}}
    for a,b in combinations(aligned,2):
        for key,r in reference.items():
            c=cells[r['belief_id']];c['expected']+=1
            x,y=a[key],b[key]
            if all(not z.get('error') and z.get('answer') in z['options'] for z in [x,y]):
                c['eligible']+=1;c['agreeing']+=x['answer']==y['answer']
    return cells

def rate(c):
    return {**c,'rate_over_eligible':c['agreeing']/c['eligible'] if c['eligible'] else None}

def combine(cells):
    return rate({k:sum(c[k] for c in cells) for k in ['expected','eligible','agreeing']})

def analyze(project=Path('.')):
    output=project/'data/results/ethical_pilot'/MASTER/'natural_stability'
    if output.exists():raise FileExistsError('Historical stability analysis already started')
    generated=project/'data/generated/ethical_pilot'/MASTER
    groups=read(generated/'analysis_groups.json')['beliefs']
    old_path=project/'data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/per_belief_results.jsonl'
    old=rows(old_path);sources={str(old_path):sha(old_path)};models={};per_belief=[]
    group_ids={'all':set(groups),'ethical':{b for b,g in groups.items() if g['role']=='ethical'},
        'target':{b for b,g in groups.items() if g['analysis_group']=='target'},
        'untrained_ethical':{b for b,g in groups.items() if g['analysis_group'] in ['related_untrained','other_untrained_ethical']},
        'preferences':{b for b,g in groups.items() if g['analysis_group']=='offtopic_eval'}}
    if [len(group_ids[k]) for k in group_ids]!=[100,90,10,80,10]:raise ValueError('Unexpected predeclared groups')
    for arm in ARMS:
        summary_paths=[]
        for seed in SEEDS:
            if arm=='base':p=project/'data/results/ethical_pilot'/BASE[seed]/'measurement_summary.json'
            elif arm=='offtopic':p=project/f'data/results/ethical_pilot/ethics_gpu_offtopic_supplement_s{seed}_v2/measurement_summary.json'
            else:
                paths={r['source_path'] for r in old if r['arm']==arm and r['seed']==seed}
                if len(paths)!=1:raise ValueError('No unique historical source')
                p=project/next(iter(paths))
                if any(sha(p)!=r['source_sha256'] for r in old if r['arm']==arm and r['seed']==seed):raise ValueError('Historical summary source changed')
            summary_paths.append(p)
        summaries=[];banks=[];observations=[];identity=None
        expected_adapter=load_job(['+run='+f'ethics_gpu_scoped_readout_{arm}_s42_v1']).pilot_bench.adapter_path
        for seed,p in zip(SEEDS,summary_paths):
            summary=read(p);bank=rows(p.parent/'stance_bank.jsonl');raw=rows(p.parent/'stance_observations.jsonl')
            if summary['measurement_bank_sha']!=BANK_SHA or summary['adapter']!=expected_adapter or summary['decoding']['seed']!=seed:raise ValueError('Historical model/bank/seed mismatch')
            current={k:summary[k] for k in ['version','extractor_version','model','adapter','model_config_sha','backend','measurement_bank_sha']}
            current['decoding']={k:v for k,v in summary['decoding'].items() if k!='seed'}
            if identity is not None and current!=identity:raise ValueError('Historical runtime/decoder changed')
            identity=current
            if len(bank)!=2400 or Counter(r['belief_id'] for r in bank)!=Counter({b:24 for b in groups}):raise ValueError('Missing full100 repeated grid')
            if summarize_measurement(bank,raw)!=summary['measurements']['stance']:raise ValueError('Frozen historical scores do not reconstruct')
            for path in [p,p.parent/'stance_bank.jsonl',p.parent/'stance_observations.jsonl']:sources[str(path)]=sha(path)
            summaries.append(summary);banks.append(bank);observations.append(raw)
        repeat=repeats(banks,observations);within={}
        for bid in groups:
            measures=[agreement_counts({'measurements':{'stance':{bid:s['measurements']['stance'][bid]}}}) for s in summaries]
            within[bid]={metric:combine([m[metric] for m in measures]) for metric in ['order','wording','negation']}
            per_belief.append({'model':arm,'belief_id':bid,**groups[bid],'same_prompt':rate(repeat[bid]),'within_prompt':within[bid]})
        aggregate={}
        for name,ids in group_ids.items():
            repeat_rate=combine([repeat[b] for b in ids]);checks={m:combine([within[b][m] for b in ids]) for m in ['order','wording','negation']}
            aggregate[name]={'same_prompt':repeat_rate,'within_prompt':checks,
                'within_minus_repeat_agreement':{m:c['rate_over_eligible']-repeat_rate['rate_over_eligible'] if c['rate_over_eligible'] is not None and repeat_rate['rate_over_eligible'] is not None else None for m,c in checks.items()}}
        models[arm]={'runs':[p.parent.name for p in summary_paths],'identity':identity,'groups':aggregate,
            'cohort':'Later off-topic three-seed supplement' if arm=='offtopic' else 'Original pilot three-seed evaluations'}
    interpretation='Exploratory historical response stability, not forward qualification or a new training replicate. Same-prompt repeats and within-prompt variants are distinct correlated comparisons, not noise-corrected scores, confidence or a causal decomposition. Historical failed controls remain failed; invalid pairs retain expected counts. Later off-topic cohort is separate. No fresh readout pooled here.'
    report={'models':models,'seeds':SEEDS,'sources':sources,'interpretation':interpretation}
    output.mkdir(parents=True)
    (output/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Historical natural-response stability','',interpretation,'','| Model | Same prompt | Order | Wording | Negation |','|---|---:|---:|---:|---:|']
    for arm,m in models.items():
        g=m['groups']['all'];values=[g['same_prompt'],*[g['within_prompt'][k] for k in ['order','wording','negation']]]
        lines.append('| '+arm+' | '+' | '.join(f"{v['rate_over_eligible']:.3%} ({v['agreeing']}/{v['eligible']}; expected{v['expected']})" if v['rate_over_eligible'] is not None else f"Not estimable; expected{v['expected']}" for v in values)+' |')
    (output/'analysis.md').write_text('\n'.join(lines)+'\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    p=output/'per_belief.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in per_belief));write_md(p)
    print('\n'.join(lines[:12]));return report
if __name__=='__main__':analyze()
