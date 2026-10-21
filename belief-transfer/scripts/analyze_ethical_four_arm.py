"""Read frozen pilot outputs; no model calls, filtering, parameter or checkpoint selection."""
from __future__ import annotations
import json
from pathlib import Path
import random
from statistics import mean
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
import prepare_ethical_four_arm as pilot

BASE={42:'ethics_gpu_vllm_base_v1',7:'ethics_gpu_vllm_base_seed7_v1',1729:'ethics_gpu_vllm_base_seed1729_v1'}

def cluster_interval(values:list[float],*,seed:int=42,draws:int=2000)->tuple[float,float]:
    if not values:raise ValueError('No clusters')
    rng=random.Random(seed);samples=sorted(mean(rng.choices(values,k=len(values))) for _ in range(draws))
    return samples[int((draws-1)*.025)],samples[int((draws-1)*.975)]

def main()->None:
    master=Path('data/generated/ethical_stance_sft')/pilot.MASTER
    plan=pilot.read(master/'plan.json');root=Path('data/results/ethical_pilot');rows=[];missing=[];qualifications={};retention={}
    ethical=set(plan['subjects']);groups=pilot.read(master/'analysis_groups.json')['beliefs']
    for arm in pilot.ARMS:
        ret=root/f'ethics_gpu_pilot_{arm}_retention_v1'/'summary.json'
        retention[arm]=pilot.read(ret) if ret.exists() else None
        for seed in pilot.SEEDS:
            paths=[root/pilot.eval_id(arm,phase,seed)/'measurement_summary.json' for phase in ('stance','unqualified')]
            existing=[p for p in paths if p.exists()]
            if len(existing)!=1:missing.append({'arm':arm,'seed':seed,'reason':'No unique completed measurement summary'});continue
            p=existing[0];summary=pilot.read(p);base_path=root/BASE[seed]/'measurement_summary.json';base=pilot.read(base_path)
            # Adapter identity differs; content bank, decoder and backend must match same-seed BASE.
            if any(summary[k]!=base[k] for k in ('version','extractor_version','measurement_bank_sha','decoding','backend')):raise ValueError('Unmatched measurement identity')
            qualifications[f'{arm}/{seed}']={'validated_chain':p.parent.name==pilot.eval_id(arm,'stance',seed),'fresh_controls':summary['meta_eval']['model_controls']}
            if len(summary['measurements']['stance'])!=100:raise ValueError('Full100belief surface missing')
            for id,profiles in summary['measurements']['stance'].items():
                score=profiles['neutral'];before=base['measurements']['stance'][id]['neutral'];complete=score['diagnostics']['complete'] and before['diagnostics']['complete']
                rows.append({'arm':arm,'seed':seed,'belief_id':id,'group':groups[id]['analysis_group'],'category':groups[id]['category'],'related_group':groups[id]['related_group'],
                    'stance_score':score['support'],'base_stance_score':before['support'],
                    'drift':score['support']-before['support'] if complete and score['support'] is not None and before['support'] is not None else None,
                    'complete':complete,'diagnostics':score['diagnostics'],'base_diagnostics':before['diagnostics'],
                    'order_agreement':score['order_consistency'],'wording_agreement':score['paraphrase_consistency'],
                    'negation':{k:score[k] for k in ('n_expected_negation_pairs','n_eligible_negation_pairs','n_contradictions')},
                    'polarity_profile':score['polarity_profile'],'source_path':str(p),'source_sha256':pilot.sha(p),
                    'base_source_path':str(base_path),'base_source_sha256':pilot.sha(base_path)})
    lookup={(r['arm'],r['seed'],r['belief_id']):r for r in rows};contrasts=[];by_seed={seed:[] for seed in pilot.SEEDS}
    for id in plan['subjects']:
        values=[]
        for seed in pilot.SEEDS:
            p=lookup.get(('positive',seed,id));n=lookup.get(('negative',seed,id))
            if p and n and p['drift'] is not None and n['drift'] is not None:
                value=p['drift']-n['drift'];values.append(value);by_seed[seed].append(value)
        if len(values)==len(pilot.SEEDS):contrasts.append(mean(values))
    estimable=len(contrasts)==10
    primary=mean(contrasts) if estimable else None
    interval=cluster_interval(contrasts) if estimable else None
    report={'run_id':pilot.MASTER,'hypothesis':'Positive-minus-negative mean target drift >0',
      'primary_contrast':primary,'belief_cluster_95_interval':interval,'bootstrap_draws':2000,'bootstrap_seed':42,
      'primary_verdict':'not_estimable' if not estimable else 'directional_hypothesis_failed' if primary<=0 else 'inconclusive' if interval[0]<=0 else 'exploratory_directional_evidence',
      'qualification':qualifications,'retention':retention,'missing_runs':missing,
      'evaluation_seed_contrasts':{seed:mean(v) if len(v)==10 else None for seed,v in by_seed.items()},
      'limitations':'One training seed; intervals resample10selected belief clusters, not independent wordings or training runs. Qualification/control/retention failures limit attribution. Missing/incomplete primary pairs are not dropped or imputed; primary becomes unestimable. Off-topic eval preferences remain untrained; fresh control topics are distinct. No forgetting claim from stance drift.',
      'rows':len(rows),'expected_rows':1200,'group_summary':{}}
    for arm in pilot.ARMS:
        report['group_summary'][arm]={}
        for group in sorted({r['group'] for r in rows}):
            selected=[r for r in rows if r['arm']==arm and r['group']==group]
            expected=sum(v['analysis_group']==group for v in groups.values())*len(pilot.SEEDS)
            complete=len(selected)==expected and all(r['drift'] is not None for r in selected)
            report['group_summary'][arm][group]={'expected_belief_seed_rows':expected,'observed':len(selected),'complete':complete,'mean_drift':mean(r['drift'] for r in selected) if complete else None}
    out=Path('data/results/ethical_stance_sft')/pilot.MASTER
    path=out/'per_belief_results.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(path)
    pilot.dump(out/'analysis.json',report);(out/'analysis.md').write_text('# Exploratory four-arm pilot\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps({k:report[k] for k in ('primary_contrast','belief_cluster_95_interval','primary_verdict','missing_runs','rows')},indent=2))
if __name__=='__main__':main()
