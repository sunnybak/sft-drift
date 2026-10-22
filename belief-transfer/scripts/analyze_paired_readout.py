"""Relative-choice surface and sampling variability; never replace endorsement scores."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from itertools import combinations
import json
from pathlib import Path
from statistics import stdev
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.measurements import align,summarize_measurement,summarize_controls
from belief_transfer.metrics.measurements import request_sampling_seed
from belief_transfer.metrics.support_bounds import support_bounds
from belief_transfer.stages.measurements import observed_backend_reply,measurement_bank_fingerprint
from belief_transfer.validation.measurements import EXTRACTOR_VERSION
from run_paired_readout import MASTER,SEEDS,ARMS,BANK_SHA,POLICY,read,rows,sha

def valid(r):return not r.get('error') and r.get('answer') in ['agree','disagree']
def choice(r):return (r['answer']=='agree')==(r['polarity']=='positive')
def combine(counts):
    c={k:sum(r[k] for r in counts) for k in ['expected','eligible','agreeing']}
    return {**c,'rate_over_eligible':c['agreeing']/c['eligible'] if c['eligible'] else None}

def agreement(observed,axis):
    keys={'order':['belief_id','wording_id','polarity'],'wording':['belief_id','polarity','arrangement'],
        'target_mirror':['belief_id','wording_id','arrangement'],'same_prompt':['presentation_id']}
    grouped=defaultdict(list)
    for r in observed:
        # Mirror the target line while holding the physical canonical A/B order fixed.
        key=(r['belief_id'],r['wording_id'],r['arrangement']^(r['polarity']=='negative')) if axis=='target_mirror' else tuple(r[k] for k in keys[axis])
        grouped[key].append(r)
    counts={'expected':0,'eligible':0,'agreeing':0}
    for group in grouped.values():
        for a,b in combinations(group,2):
            counts['expected']+=1
            if valid(a) and valid(b):counts['eligible']+=1;counts['agreeing']+=choice(a)==choice(b)
    return combine([counts])

def endpoint(after,before):
    a,b=support_bounds(after),support_bounds(before)
    return {**a,'base':b,'drift':a['value']-b['value'] if a['complete'] and b['complete'] else None,
        'drift_lower':a['lower']-b['upper'],'drift_upper':a['upper']-b['lower']}

def spread(values):
    good=[v for v in values if v is not None]
    return {'planned_seeds':len(values),'complete_seeds':len(good),'values':values,
        'mean':sum(good)/len(good) if len(good)==len(values) else None,
        'min':min(good) if len(good)==len(values) else None,'max':max(good) if len(good)==len(values) else None,
        'sample_stdev':stdev(good) if len(good)>1 and len(good)==len(values) else None,
        'interpretation':'Descriptive evaluation-seed spread, not a confidence interval or training replication.'}

def validate_child(summary,bank,observed,control_bank,controls,proof,item,*,bank_sha=None,batch_size=256):
    if (summary['measurement_bank_sha']!=(BANK_SHA if bank_sha is None else bank_sha) or summary['extractor_version']!=EXTRACTOR_VERSION
        or summary.get('adapter')!=item['adapter_path'] or summary['model_config_sha']!=fingerprint(proof['model_config']) or summary['backend']!=proof['backend']):raise ValueError('Paired model/bank/extractor/backend changed')
    d=summary['decoding']
    if (any(d.get(k)!=v for k,v in proof['decoder'].items()) or d.get('max_new_tokens')!=proof['max_new_tokens']
        or d.get('execution')!=proof['generation'] or d.get('execution_versions')!=proof['versions']
        or d.get('seed')!=item['seed'] or d.get('batch_size')!=batch_size):raise ValueError('Paired decoder/execution changed')
    if summarize_measurement(bank,observed)!=summary['measurements']['stance'] or summarize_controls(control_bank,controls)!=summary['meta_eval']['model_controls']['stance']:
        raise ValueError('Paired summary scores do not reconstruct')
    references={r['presentation_id']:r for r in bank+control_bank}
    for r in [*align(bank,observed),*align(control_bank,controls)]:
        if r.get('response') is None:
            if not r.get('error') or r.get('answer') is not None or r.get('strict_format'):raise ValueError('Unmarked missing paired response')
            continue
        m=r.get('generation_metadata') or {};seed=request_sampling_seed(references[r['presentation_id']],item['seed'])
        rebuilt=observed_backend_reply(references[r['presentation_id']],r['response'],m,thinking=proof['decoder']['thinking'],seed=seed)
        # Compare outcome fields only; metadata identity is checked independently below.
        for k in ['answer','answer_extraction','strict_format','error','final_response','reasoning_extraction','sampling_seed']:
            if r.get(k)!=rebuilt.get(k):raise ValueError('Paired extraction does not reconstruct: '+k)
        if (m.get('adapter_lora_id')!=(1 if item['adapter_sha256'] else None) or m.get('model_revision')!=proof['generation']['revision']
            or m.get('sampling_seed')!=seed or m.get('execution_versions')!=proof['versions']):raise ValueError('Paired request identity changed')

def analyze(root=Path('data'),*,partial=False):
    generated=root/'generated/ethical_pilot'/MASTER;result=root/'results/ethical_pilot'/MASTER
    protocol=read(generated/'protocol.json');groups=read(generated/'analysis_groups.json')['beliefs'];reference=rows(generated/'stance_bank.jsonl');control_bank=rows(generated/'control_bank.jsonl')
    if len(groups)!=100 or Counter(r['belief_id'] for r in reference)!=Counter({b:24 for b in groups}) or len(control_bank)!=32:raise ValueError('Require full100 paired grid')
    if protocol['measurement_bank_sha']!=BANK_SHA or protocol['evaluation_seeds']!=SEEDS:raise ValueError('Changed paired protocol')
    identity=[(j['arm'],j['seed'],j['run_id']) for j in protocol['jobs']]
    from run_paired_readout import run_ids
    if identity!=run_ids():raise ValueError('Changed fifteen-job paired schedule')
    proofs=protocol['runtime_evidence'];data={};summaries={};pending=[];sources=[]
    for item in protocol['jobs']:
        folder=root/'results/ethical_pilot'/item['run_id'];p=folder/'measurement_summary.json'
        if not p.exists():pending.append(item['run_id']);continue
        bank=rows(folder/'stance_bank.jsonl');cb=rows(folder/'stance_control_bank.jsonl')
        if bank!=reference or cb!=control_bank:raise ValueError('Changed paired prompt bank')
        observed=rows(folder/'stance_observations.jsonl');controls=rows(folder/'stance_controls.jsonl');summary=read(p)
        manifest=read(folder/'measurement_manifest.json')
        if (manifest['banks']['stance']!=fingerprint(bank) or manifest['controls']['stance']!=fingerprint(cb)
            or measurement_bank_fingerprint(manifest)!=BANK_SHA or summary['bank_sha']!=fingerprint(manifest)):
            raise ValueError('Paired manifest/bank identity does not reconstruct')
        if Counter(r['presentation_id'] for r in observed)!=Counter(r['presentation_id'] for r in reference) or Counter(r['presentation_id'] for r in controls)!=Counter(r['presentation_id'] for r in cb):raise ValueError('Missing/duplicate paired observations')
        validate_child(summary,bank,observed,cb,controls,proofs[item['arm']],item)
        key=(item['arm'],item['seed']);data[key]=align(bank,observed);summaries[key]=summary
        for name in ['measurement_summary.json','measurement_manifest.json','stance_bank.jsonl','stance_observations.jsonl','stance_control_bank.jsonl','stance_controls.jsonl']:
            sources.append({'path':str(folder/name),'sha256':sha(folder/name)})
    if pending and not partial:raise ValueError('Paired readout pending: '+','.join(pending))
    if not any(arm=='base' for arm,_ in data):raise ValueError('Collect new paired BASE first')
    # The identical bank must also produce identical tokenized inputs across weights/seeds.
    tokens={}
    for observed in data.values():
        for r in observed:
            m=r.get('generation_metadata') or {}
            if r.get('response') is None or m.get('backend_error'):continue
            ids=m.get('input_token_ids');key=r['presentation_id']
            if ids is None or key in tokens and tokens[key]!=ids:raise ValueError('Paired input tokenization changed')
            tokens[key]=ids
    sets={'all':set(groups),'target':{b for b,g in groups.items() if g['analysis_group']=='target'},
        'untrained_ethical':{b for b,g in groups.items() if g['analysis_group'] in ['related_untrained','other_untrained_ethical']}}
    sets.update({g:{b for b,v in groups.items() if v['analysis_group']==g} for g in sorted({v['analysis_group'] for v in groups.values()})})
    models={};belief_rows=[]
    for arm in ARMS:
        available=[s for s in SEEDS if (arm,s) in data and ('base',s) in data]
        if not available:continue
        seeds={}
        for seed in available:
            observed=data[arm,seed];before=data['base',seed]
            seeds[str(seed)]={'endpoints':{name:endpoint([r for r in observed if r['belief_id'] in ids],[r for r in before if r['belief_id'] in ids]) for name,ids in sets.items()},
                'agreement':{axis:agreement(observed,axis) for axis in ['order','wording','target_mirror']},
                'legacy_controls':summaries[arm,seed]['meta_eval']['model_controls']['stance'],
                'strict':sum(bool(r.get('strict_format')) for r in observed),'expected':len(observed),
                'failures':[{k:r.get(k) for k in ['presentation_id','error','strict_format','final_response']}|{'finish_reason':(r.get('generation_metadata') or {}).get('finish_reason')} for r in observed if r.get('error') or not r.get('strict_format')]}
        pooled=[r for s in available for r in data[arm,s]];base=[r for s in available for r in data['base',s]]
        endpoints={name:endpoint([r for r in pooled if r['belief_id'] in ids],[r for r in base if r['belief_id'] in ids]) for name,ids in sets.items()}
        # An unfinished planned repeat is not silently pooled into a full estimate.
        complete=len(available)==len(SEEDS)
        models[arm]={'complete_seeds':complete,'seeds':seeds,'pooled_completed_seeds':endpoints,
            'drift_seed_variability':{name:spread([seeds.get(str(s),{}).get('endpoints',{}).get(name,{}).get('drift') for s in SEEDS]) for name in sets},
            'same_prompt':agreement(pooled,'same_prompt') if complete else None,
            'within_prompt':{axis:combine([seeds[str(s)]['agreement'][axis] for s in available]) for axis in ['order','wording','target_mirror']}}
        for bid in sorted(groups):
            belief_rows.append({'model':arm,'belief_id':bid,**groups[bid],'complete_seeds':complete,'evaluation_seeds':available,
                **endpoint([r for r in pooled if r['belief_id']==bid],[r for r in base if r['belief_id']==bid])})
    contrast=[]
    for seed in SEEDS:
        if ('positive',seed) not in data or ('negative',seed) not in data:continue
        p=[r for r in data['positive',seed] if r['belief_id'] in sets['target']];n=[r for r in data['negative',seed] if r['belief_id'] in sets['target']]
        contrast.append({'seed':seed,**endpoint(p,n)})
    interpretation='Relative forced preference under paired statements, not absolute endorsement or confidence. All100beliefs retained. Target-mirror agreement holds canonical A/B positions fixed and measures target-line framing; within-question exclusivity is structural, not general negation competence. Missing-response bounds are not confidence intervals. Three evaluation seeds on one training seed, no training replication or significance claim. Historical independent-endorsement results and failed gates remain unchanged. No automatic training approval or scale-up.'
    report={'run_id':MASTER,'policy_id':POLICY,'complete':not pending,'pending':pending,'models':models,
        'positive_minus_negative_target':contrast,'contrast_seed_variability':spread([next((c['drift'] for c in contrast if c['seed']==s),None) for s in SEEDS]),
        'sources':sources,'interpretation':interpretation}
    result.mkdir(parents=True,exist_ok=True);stem='progress' if partial else 'analysis';out=result/(stem+'.json')
    if not partial and out.exists():raise FileExistsError('Completed paired analysis exists')
    out.write_text(json.dumps(report,indent=2)+'\n');out.with_suffix('.md').write_text('# Paired-position readout\n\n'+interpretation+'\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    p=result/('per_belief_progress.jsonl' if partial else 'per_belief_results.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in belief_rows));write_md(p)
    print(json.dumps({'complete':not pending,'pending':pending,'models':list(models),'contrast_seed_variability':report['contrast_seed_variability']},indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
