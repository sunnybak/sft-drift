"""Independent target-free calibration: fresh domains/splits, separate reused probes."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.metrics.response_interface_rca import summarize
from belief_transfer.validation.response_interface_rca import assess
from analyze_interface_controls import compare
from run_error_rca import sha,dump
MASTER='ethics_gpu_target_free_controls_v1'
DOMAINS=['normative','factual','arithmetic']
def read(path):return json.loads(Path(path).read_text())
def rows(path):return list(map(json.loads,Path(path).read_text().splitlines()))

def split_summary(observed):
    if len(observed)!=192 or Counter(r['domain'] for r in observed)!=Counter({'normative':48,'factual':48,'arithmetic':96}):raise ValueError('Full fresh domain split required')
    groups=defaultdict(dict);orders=defaultdict(dict)
    for r in observed:
        key=(r['context_id'],r['order'])
        if r['variant'] in groups[key]:raise ValueError('Duplicate control view')
        groups[key][r['variant']]=r;orders[r['context_id'],r['variant']][r['order']]=r
    for g in groups.values():
        if set(g)!={'plain','note','repeat'}:raise ValueError('Incomplete control views')
        p,n,r=[g[k] for k in ['plain','note','repeat']]
        if p['prompt']!=r['prompt'] or p['sampling_seed']!=n['sampling_seed'] or p['sampling_seed']==r['sampling_seed']:raise ValueError('Changed note/repeat RNG design')
    notes=compare({k:{s:g[s] for s in ['plain','note']} for k,g in groups.items()},['plain','note'])
    repeats=compare({k:{s:g[s] for s in ['plain','repeat']} for k,g in groups.items()},['plain','repeat'])
    counts=summarize(observed)['overall'];domains={d:summarize([r for r in observed if r['domain']==d])['overall'] for d in DOMAINS}
    checks={d+'_accuracy_at_least_95pct':v['accuracy']>=.95 for d,v in domains.items()}
    checks.update(complete_extraction=counts['valid']==192,strict_format=counts['strict']==192,
        complete_note_pairs=notes['eligible_pairs']==notes['expected_pairs'],note_flips_at_most_5pct=notes['disagreement_rate'] is not None and notes['disagreement_rate']<=.05,
        normal_stops=all((r.get('generation_metadata') or {}).get('finish_reason')=='stop' for r in observed))
    return {'counts':counts,'domains':domains,'checks':checks,'passed':all(checks.values()),'note_comparison':notes,
        'independent_repeat':repeats,'order_agreement':compare(orders,[0,1]),
        'failures':[{k:r.get(k) for k in ['presentation_id','domain','expected_word','answer','strict_format','error','final_response']} for r in observed if not r.get('correct') or not r.get('strict_format') or r.get('error')]}

def inspect_model(root:Path,item:dict,protocol:dict)->dict:
    generated=root/'generated/ethical_pilot'/MASTER;child=root/'results/ethical_pilot'/item['run_id']
    if not (child/'COMPLETED').exists():raise ValueError('Child calibration is incomplete')
    bank=rows(generated/'bank.jsonl');expected={r['presentation_id']:r for r in bank};observed=rows(child/'observations.jsonl');manifest=read(child/'manifest.json');proof=protocol['runtime_evidence'][item['arm']]
    if len(bank)!=388 or len(expected)!=388 or Counter(r['presentation_id'] for r in observed)!=Counter(expected.keys()):raise ValueError('Incomplete target-free bank/grid')
    if sha(child/'bank.jsonl')!=sha(generated/'bank.jsonl') or manifest['bank_sha256']!=sha(generated/'bank.jsonl') or manifest['adapter_sha256']!=item['adapter_sha256'] or manifest['model_label']!=item['arm']:raise ValueError('Control bank/model/adapter changed')
    for k in ['model_config','backend','decoder','generation','versions','max_new_tokens']:
        if manifest[k]!=proof[k]:raise ValueError('Control runtime identity changed: '+k)
    for r in observed:
        if any(r.get(k)!=v for k,v in expected[r['presentation_id']].items()):raise ValueError('Control source fields changed')
        if r.get('response') is None:
            if not r.get('error') or r.get('answer') is not None or r.get('correct') or r.get('strict_format'):raise ValueError('Unmarked absent response')
            continue
        m=r.get('generation_metadata') or {};rebuilt=assess(r,r['response'],m,thinking=True)
        if any(r.get(k)!=v for k,v in rebuilt.items()):raise ValueError('Control assessment does not reconstruct')
        if (m.get('model_revision')!=proof['generation']['revision'] or m.get('adapter_lora_id')!=(1 if item['adapter_sha256'] else None)
            or m.get('sampling_seed')!=r['sampling_seed'] or m.get('execution_versions')!=proof['versions'] or len(m.get('input_token_ids') or [])!=r['expected_input_tokens']):raise ValueError('Control request/tokenizer identity changed')
    if read(child/'summary.json')['overall']!=summarize(observed)['overall']:raise ValueError('Stored control counts changed')
    splits={s:split_summary([r for r in observed if r['split']==s]) for s in ['development','validation']}
    reused=[r for r in observed if r['split']=='regression']
    if len(reused)!=4:raise ValueError('Missing separately labeled regression evidence')
    return {'run_id':item['run_id'],'splits':splits,'passed':all(s['passed'] for s in splits.values()),
        'regression':{'counts':summarize(reused)['overall'],'excluded_from_fresh_qualification':True,
            'replies':[{k:r.get(k) for k in ['presentation_id','source_presentation_id','sampling_seed','response','answer','correct','strict_format','error']} for r in reused]},
        'sources':[{'path':str(child/name),'sha256':sha(child/name)} for name in ['manifest.json','bank.jsonl','observations.jsonl','summary.json']]}

def analyze(root=Path('data'),*,partial=False):
    protocol=read(root/'generated/ethical_pilot'/MASTER/'protocol.json');models={};pending=[]
    for item in protocol['jobs']:
        if not (root/'results/ethical_pilot'/item['run_id']/'COMPLETED').exists():pending.append(item['run_id']);continue
        models[item['arm']]=inspect_model(root,item,protocol)
    base_failed=(root/'results/ethical_pilot'/MASTER/'BASE_GATE_FAILED.json').exists()
    if pending and not partial and not base_failed:raise ValueError('Pending target-free calibrations: '+','.join(pending))
    report={'run_id':MASTER,'complete':not pending,'pending':pending,'base_gate_failed':base_failed,'models':models,
        'qualified_for_prospective_readout':not pending and len(models)==5 and all(m['passed'] for m in models.values()),
        'interpretation':'Fresh stipulated normative/provided-fact/arithmetic references. Reused regression probes are excluded from qualification. No own ethical outcomes, training changes, historical gate changes, fallback selection or automatic readout launch.'}
    result=root/'results/ethical_pilot'/MASTER;result.mkdir(parents=True,exist_ok=True);p=result/('progress.json' if partial else 'analysis.json')
    if not partial and p.exists():raise FileExistsError('Completed target-free analysis exists')
    dump(p,report);p.with_suffix('.md').write_text('# Target-free calibration\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps({'complete':not pending,'pending':pending,'models':{a:m['passed'] for a,m in models.items()},'qualified':report['qualified_for_prospective_readout']},indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
