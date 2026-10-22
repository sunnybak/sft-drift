"""Independent-input retention decision; never rescores historical measurements."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
from run_fresh_retention import MASTER,ARMS,roots,read,rows,sha,inspect,write_rows
from analyze_retention_rca import compare,characterize


def decision(comparison):
    result={}
    for mode in [True,False]:
        deltas=[comparison['by_seed_mode'][str(seed)][str(mode)]['semantic_correct']['delta_pp'] for seed in [42,7,1729]]
        stable=[r for r in comparison['stable_verified_content_differences'] if r['thinking']==mode]
        result[str(mode)]={'conditional_semantic_delta_pp':deltas,'stable_content_loss_count':len(stable),
            'stable_content_loss_ids':[r['example_id'] for r in stable],
            'training_retention_concern':all(v < -5 for v in deltas) and len(stable)>=3}
    return result


def analyze():
    generated,result=roots();protocol=read(generated/'protocol.json')
    if not (result/'COMPLETED').exists() or not (result/'TERMINAL').exists():raise ValueError('Full fresh worker must finish first')
    if (result/'analysis.json').exists():raise FileExistsError('Final fresh analysis is immutable')
    bank=rows(generated/'bank.jsonl');known=None;collected={};summaries={};sources=[];failed=[]
    for arm in ARMS:
        actual,known,summary=inspect(arm,protocol,known);collected[arm]=actual
        folder=Path('data/results/ethical_pilot')/f'ethics_gpu_fresh_retention_{arm}_v1'
        sources += [{'path':str(folder/name),'sha256':sha(folder/name)} for name in ['responses.jsonl','bank.jsonl','known_items.jsonl','manifest.json','summary.json','config.resolved.yaml']]
        summaries[arm]={'native':summary,'by_seed_mode_split_family':{}}
        for seed in [42,7,1729]:
            for mode in [True,False]:
                for split in ['development','validation','all']:
                    for family in ['all',*sorted({r['family'] for r in bank})]:
                        group=[r for r in actual if r['eval_seed']==seed and r['thinking']==mode and (split=='all' or r['split']==split) and (family=='all' or r['family']==family)]
                        eligible=[r for r in group if r['example_id'] in {v['example_id'] for v in known}]
                        keys=['semantic_correct','exact_answer','strict_format','response_boundaries_valid','normal_stop']
                        summaries[arm]['by_seed_mode_split_family'][f'{seed}/{mode}/{split}/{family}']={
                            'expected':len(group),'full':{k:sum(r['assessment'][k] for r in group) for k in keys},
                            'known_n':len(eligible),'known':{k:sum(r['assessment'][k] for r in eligible) for k in keys}}
        failed += [{'arm':arm,'observation':r,'characterization':characterize(r)} for r in actual if not r['assessment']['admissible'] or r.get('error')]
    comparisons={a:compare(collected['base'],collected[a],bank,known) for a in ARMS if a!='base'}
    decisions={a:decision(c) for a,c in comparisons.items()}
    net={}
    for arm,observed in collected.items():
        net[arm]={}
        for seed in [42,7,1729]:
            for mode in [True,False]:
                base={r['example_id']:r for r in collected['base'] if r['eval_seed']==seed and r['thinking']==mode}
                after={r['example_id']:r for r in observed if r['eval_seed']==seed and r['thinking']==mode}
                net[arm][f'{seed}/{mode}']={'expected':len(base),
                    'base_correct':sum(r['assessment']['semantic_correct'] for r in base.values()),
                    'adapter_correct':sum(r['assessment']['semantic_correct'] for r in after.values()),
                    'gains':[i for i in base if not base[i]['assessment']['semantic_correct'] and after[i]['assessment']['semantic_correct']],
                    'losses':[i for i in base if base[i]['assessment']['semantic_correct'] and not after[i]['assessment']['semantic_correct']]}
    output={'run_id':MASTER,'complete':True,'models':summaries,'comparisons':comparisons,'decisions':decisions,
        'full_bank_net':net,'sources':sources,'failed_response_count':len(failed),
        'any_training_retention_concern':any(m['training_retention_concern'] for a in decisions.values() for m in a.values()),
        'interpretation':'Prospective new procedural-input bank, known mask from BASE seed42 only. Full results and frozen grading retained. Nonthinking repeats are greedy; no broad-capability claim, historical requalification or automatic training approval. Agent full-response review pending.'}
    (result/'analysis.json').write_text(json.dumps(output,indent=2)+'\n');(result/'analysis.md').write_text('# Fresh retention results\n\n```json\n'+json.dumps(output,indent=2)+'\n```\n')
    write_rows(result/'failed_responses.jsonl',failed)
    print(json.dumps({'complete':True,'failed_responses':len(failed),'training_retention_concern':output['any_training_retention_concern'],'decisions':decisions}))
    return output

if __name__=='__main__':analyze()
