"""Prospective known-reference interface checks; never ethical-outcome selection."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.metrics.response_interface_rca import summarize
from belief_transfer.validation.response_interface_rca import assess
from run_error_rca import sha,dump
MASTER='ethics_gpu_interface_controls_v1'
FORMS=['current','explicit','paired']

def rows(path):return list(map(json.loads,path.read_text().splitlines()))
def read(path):return json.loads(path.read_text())
def valid(r):return not r.get('error') and r.get('answer') in r['options']
def support(r):return r['support_by_word'][r['answer']]

def compare(groups,keys):
    eligible=disagreeing=0
    for pair in groups.values():
        if set(pair)!=set(keys):raise ValueError('Incomplete paired interface control')
        a,b=[pair[k] for k in keys]
        if valid(a) and valid(b):eligible+=1;disagreeing+=support(a)!=support(b)
    n=len(groups)
    return {'expected_pairs':n,'eligible_pairs':eligible,'disagreements':disagreeing,
        'disagreement_rate':disagreeing/eligible if eligible else None}

def split_summary(observed):
    if not observed:raise ValueError('Empty interface split')
    variants=defaultdict(dict);orders=defaultdict(dict);polarities=defaultdict(dict)
    for r in observed:
        if r['variant'] in variants[r['context_id'],r['negative'],r['order']]:raise ValueError('Duplicate interface view')
        variants[r['context_id'],r['negative'],r['order']][r['variant']]=r
        orders[r['context_id'],r['negative'],r['variant']][r['order']]=r
        polarities[r['context_id'],r['order'],r['variant']][r['negative']]=r
    for group in variants.values():
        if set(group)!={'plain','repeat','note'}:raise ValueError('Incomplete interface views')
        p,n,r=[group[k] for k in ['plain','note','repeat']]
        if p['prompt']!=r['prompt'] or p['sampling_seed']==r['sampling_seed'] or p['sampling_seed']!=n['sampling_seed']:
            raise ValueError('Incorrect repeat/note RNG design')
    notes=compare({k:{s:g[s] for s in ['plain','note']} for k,g in variants.items()},['plain','note'])
    repeats=compare({k:{s:g[s] for s in ['plain','repeat']} for k,g in variants.items()},['plain','repeat'])
    counts=summarize(observed)['overall'];domains={d:summarize([r for r in observed if r['domain']==d])['overall'] for d in ['normative','factual']}
    checks={d+'_accuracy_at_least_95pct':v['accuracy'] is not None and v['accuracy']>=.95 for d,v in domains.items()}
    checks.update(complete_extraction=counts['valid']==counts['expected'],strict_format=counts['strict']==counts['expected'],
        complete_note_pairs=notes['eligible_pairs']==notes['expected_pairs'],note_flips_at_most_5pct=notes['disagreement_rate'] is not None and notes['disagreement_rate']<=.05)
    by_domain={d:compare({k:{s:g[s] for s in ['plain','note']} for k,g in variants.items() if g['plain']['domain']==d},['plain','note']) for d in domains}
    return {'counts':counts,'domains':domains,'checks':checks,'passed':all(checks.values()),'note_comparison':notes,
        'note_by_domain':by_domain,'independent_repeat':repeats,'order_agreement':compare(orders,[0,1]),
        'target_mirror_agreement':compare(polarities,[False,True]),
        'failures':[{k:r.get(k) for k in ['presentation_id','context_id','domain','expected_word','answer','strict_format','error','final_response']} for r in observed if not r.get('correct') or not r.get('strict_format') or r.get('error')]}

def analyze(root=Path('data'),*,partial=False):
    generated=root/'generated/ethical_pilot'/MASTER;result=root/'results/ethical_pilot'/MASTER
    protocol=read(generated/'protocol.json');bank=rows(generated/'bank.jsonl');expected={r['presentation_id']:r for r in bank}
    if len(bank)!=1152 or len(expected)!=1152:raise ValueError('Full unique interface bank required')
    models={};pending=[];sources=[]
    for job in protocol['jobs']:
        child=root/'results/ethical_pilot'/job['run_id']
        if not (child/'COMPLETED').exists():pending.append(job['run_id']);continue
        manifest=read(child/'manifest.json');observed=rows(child/'observations.jsonl');proof=protocol['runtime_evidence'][job['arm']]
        if Counter(r['presentation_id'] for r in observed)!=Counter(expected.keys()):raise ValueError('Incomplete/duplicate interface responses')
        if manifest.get('model_label')!=job['arm']:raise ValueError('Wrong interface model label')
        for k in ['model_config','backend','decoder','generation','versions','max_new_tokens']:
            if manifest[k]!=proof[k]:raise ValueError('Runtime identity changed: '+k)
        if manifest['bank_sha256']!=sha(generated/'bank.jsonl') or manifest['adapter_sha256']!=job['adapter_sha256']:raise ValueError('Bank/adapter identity changed')
        for r in observed:
            if any(r.get(k)!=v for k,v in expected[r['presentation_id']].items()):raise ValueError('Changed interface bank fields')
            if r.get('response') is None:
                if not r.get('error') or r.get('answer') is not None or r.get('correct') or r.get('strict_format'):raise ValueError('Unmarked/inconsistently scored missing interface response')
                continue
            recheck=assess(r,r['response'],r.get('generation_metadata') or {},thinking=True)
            if any(r.get(k)!=v for k,v in recheck.items()):raise ValueError('Interface assessment does not reconstruct')
            if not r.get('error'):
                m=r.get('generation_metadata') or {}
                if m.get('model_revision')!=proof['generation']['revision'] or m.get('adapter_lora_id')!=(1 if job['adapter_sha256'] else None) or m.get('sampling_seed')!=r['sampling_seed'] or m.get('execution_versions')!=proof['versions']:
                    raise ValueError('Unverified interface request/model counted')
                if 'expected_input_tokens' in r and len(m.get('input_token_ids') or [])!=r['expected_input_tokens']:raise ValueError('Interface prompt tokenization changed')
        forms={f:{split:split_summary([r for r in observed if r['interface']==f and r['split']==split]) for split in ['development','validation']} for f in FORMS}
        models[job['arm']]={'run_id':job['run_id'],'forms':forms,'passed':{f:all(s['passed'] for s in splits.values()) for f,splits in forms.items()}}
        sources.extend({'path':str(child/name),'sha256':sha(child/name)} for name in ['manifest.json','bank.jsonl','observations.jsonl','summary.json'])
    if pending and not partial:raise ValueError('Pending interface controls: '+','.join(pending))
    paired_eligible=not pending and len(models)==5 and all(m['passed']['paired'] for m in models.values())
    report={'run_id':MASTER,'complete':not pending,'pending':pending,'models':models,'paired_eligible_for_prospective_readout':paired_eligible,
        'sources':sources,'interpretation':'Known-reference task mapping only. Paired candidate was preselected; explicit reminder is an ablation, not outcome-selected fallback. Paired within-question exclusivity is structural; mirror agreement is framing stability, not recovered general negation competence. Historical failures and current ethical outcomes unchanged. No training selection or scale-up follows automatically.'}
    result.mkdir(parents=True,exist_ok=True);name='progress' if partial else 'analysis';p=result/(name+'.json')
    if not partial and p.exists():raise FileExistsError('Completed interface analysis exists')
    dump(p,report);p.with_suffix('.md').write_text('# Response-interface controls\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps({'complete':not pending,'pending':pending,'paired_eligible':paired_eligible,'models':{a:m['passed'] for a,m in models.items()}},indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
