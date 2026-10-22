"""Target-free relative-choice surface, paired drift and evaluation-seed variability."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.measurements import align,operational_controls
from belief_transfer.stages.measurements import measurement_bank_fingerprint
from analyze_paired_readout import valid,choice,combine,agreement,endpoint as plain_endpoint,spread,validate_child
from run_target_free_readout_v2 import MASTER,SEEDS,ARMS,POLICY,read,rows,sha

PRIMARY_GROUPS=['all','target','untrained_ethical','offtopic_eval']

def verify_inputs(root,protocol):
    generated=root/'generated/ethical_pilot'/MASTER
    for name in ['analysis_groups.json','review_selection.jsonl','stance_bank.jsonl','control_bank.jsonl','token_audit.json']:
        path=generated/name
        if protocol['source_bindings'].get(str(path))!=sha(path):
            raise ValueError('TECHNICAL_PROTOCOL_INPUT_CHANGED: '+name)

def diagnostic_codes(row,*,control=False):
    codes=[]
    finish=(row.get('generation_metadata') or {}).get('finish_reason')
    if finish=='length':codes.append('GENERATION_TOKEN_LIMIT')
    if not valid(row):codes.append('ANSWER_UNAVAILABLE')
    elif control and row['answer']!=row['expected']:codes.append('CONTROL_WRONG_FINAL')
    if not row.get('strict_format'):codes.append('STRICT_FORMAT_FAILED')
    if finish!='stop':codes.append('NON_NORMAL_STOP')
    return codes

def endpoint(after,before):
    result=plain_endpoint(after,before)
    for counts,items in [(result,after),(result['base'],before)]:
        counts.update(conditional_frequency=counts['known_support']/counts['valid'] if counts['valid'] else None,
            bound_width=counts['missing']/counts['expected'],
            precision_passed=counts['missing']*100<=counts['expected'],
            strict=sum(valid(r) and bool(r.get('strict_format')) for r in items),
            caps=sum((r.get('generation_metadata') or {}).get('finish_reason')=='length' for r in items))
    result['drift_bound_width']=result['bound_width']+result['base']['bound_width']
    result['precision_error_codes']=[] if result['precision_passed'] and result['base']['precision_passed'] else ['AGGREGATE_MISSING_BOUND_ABOVE_1PP']
    return result

def specificity(endpoints):
    target,other=endpoints['target'],endpoints['untrained_ethical']
    return {'value':target['drift']-other['drift'] if target['drift'] is not None and other['drift'] is not None else None,
        'lower':target['drift_lower']-other['drift_upper'],
        'upper':target['drift_upper']-other['drift_lower'],
        'interpretation':'Target drift minus other80ethical drift; missing-response bounds only.'}

def belief_endpoint(after,before):
    result=endpoint(after,before)
    result.pop('precision_passed');result.pop('precision_error_codes')
    result['base'].pop('precision_passed')
    result['precision_assessment']='Not applied per belief; the1pp budget is for predeclared primary aggregates only.'
    return result

def verify_child(root,item,protocol):
    """Reconstruct raw extraction and identities without selecting on belief scores."""
    generated=root/'generated/ethical_pilot'/MASTER
    verify_inputs(root,protocol)
    folder=root/'results/ethical_pilot'/item['run_id']
    bank=rows(folder/'stance_bank.jsonl');cb=rows(folder/'stance_control_bank.jsonl')
    if bank!=rows(generated/'stance_bank.jsonl') or cb!=rows(generated/'control_bank.jsonl'):
        raise ValueError('TECHNICAL_BANK_CHANGED')
    pinned=folder/'external_control_bank.jsonl';expected=generated/'control_bank.jsonl'
    if pinned.read_bytes()!=expected.read_bytes():raise ValueError('TECHNICAL_CONTROL_BYTES_CHANGED')
    observed=rows(folder/'stance_observations.jsonl');controls=rows(folder/'stance_controls.jsonl')
    summary=read(folder/'measurement_summary.json');manifest=read(folder/'measurement_manifest.json')
    if (manifest['banks']['stance']!=fingerprint(bank) or manifest['controls']['stance']!=fingerprint(cb)
        or manifest.get('external_control_bank')!={'sha256':sha(expected),'count':488}
        or measurement_bank_fingerprint(manifest)!=protocol['measurement_bank_sha']
        or summary['bank_sha']!=fingerprint(manifest)):
        raise ValueError('TECHNICAL_MANIFEST_CHANGED')
    import yaml
    from belief_transfer.config import config_sha
    from belief_transfer.schemas import JobConfig
    from run_target_free_readout_v2 import check_config
    resolved=JobConfig.model_validate(yaml.safe_load((folder/'config.resolved.yaml').read_text()))
    check_config(resolved,item['seed'])
    if config_sha(resolved)!=item['resolved_config_sha'] or resolved.run_id!=item['run_id']:
        raise ValueError('TECHNICAL_RESOLVED_CONFIG_CHANGED')
    if (Counter(r['presentation_id'] for r in observed)!=Counter(r['presentation_id'] for r in bank)
        or Counter(r['presentation_id'] for r in controls)!=Counter(r['presentation_id'] for r in cb)):
        raise ValueError('TECHNICAL_GRID_INCOMPLETE')
    proof=protocol['runtime_evidence'][item['arm']]
    validate_child(summary,bank,observed,cb,controls,proof,item,bank_sha=protocol['measurement_bank_sha'],batch_size=64)
    audit=read(generated/'token_audit.json')
    lengths={r['presentation_id']:n for r,n in zip(bank+cb,audit['lengths'],strict=True)}
    for r in observed+controls:
        m=r.get('generation_metadata') or {}
        if r.get('response') is None or m.get('backend_error'):
            raise ValueError('TECHNICAL_BACKEND_FAILURE: '+r['presentation_id'])
        if (m.get('execution')!=proof['generation'] or m.get('finish_reason') not in ['stop','length']
            or m.get('prompt_tokens')!=lengths[r['presentation_id']]
            or len(m.get('input_token_ids',[]))!=lengths[r['presentation_id']]
            or m.get('generation_tokens')!=len(m.get('output_token_ids',[]))
            or not 0<m.get('generation_tokens',0)<=proof['max_new_tokens']):
            raise ValueError('TECHNICAL_RUNTIME_METADATA_CHANGED: '+r['presentation_id'])
    return bank,cb,observed,controls,summary,manifest

def analyze(root=Path('data'),*,partial=False):
    generated=root/'generated/ethical_pilot'/MASTER;result=root/'results/ethical_pilot'/MASTER
    protocol=read(generated/'protocol.json');groups=read(generated/'analysis_groups.json')['beliefs'];reference=rows(generated/'stance_bank.jsonl');control_bank=rows(generated/'control_bank.jsonl')
    verify_inputs(root,protocol)
    if len(groups)!=100 or Counter(r['belief_id'] for r in reference)!=Counter({b:12 for b in groups}) or len(control_bank)!=488:raise ValueError('Require full100 target-free grid')
    if len(protocol['measurement_bank_sha'])!=64 or protocol['evaluation_seeds']!=SEEDS or protocol.get('policy_id')!=POLICY:raise ValueError('Changed target-free protocol')
    if any(r['polarity']!='positive' or r['stance_interface']!='target_free_positions' or 'Target statement:' in r['prompt'] for r in reference):
        raise ValueError('Target cue or redundant polarity returned')
    identity=[(j['arm'],j['seed'],j['run_id']) for j in protocol['jobs']]
    from run_target_free_readout_v2 import run_ids
    if identity!=run_ids():raise ValueError('Changed fifteen-job target-free schedule')
    proofs=protocol['runtime_evidence'];data={};summaries={};pending=[];sources=[];raw_controls={}
    for item in protocol['jobs']:
        folder=root/'results/ethical_pilot'/item['run_id'];p=folder/'measurement_summary.json'
        if not p.exists():pending.append(item['run_id']);continue
        bank,cb,observed,controls,summary,manifest=verify_child(root,item,protocol)
        key=(item['arm'],item['seed']);data[key]=align(bank,observed);summaries[key]=summary
        raw_controls[key]=controls
        for name in ['measurement_summary.json','measurement_manifest.json','config.resolved.yaml','stance_bank.jsonl','stance_observations.jsonl','stance_control_bank.jsonl','stance_controls.jsonl','external_control_bank.jsonl']:
            sources.append({'path':str(folder/name),'sha256':sha(folder/name)})
    if pending and not partial:raise ValueError('Target-free readout pending: '+','.join(pending))
    if not any(arm=='base' for arm,_ in data):raise ValueError('Collect new target-free BASE first')
    # The identical bank must also produce identical tokenized inputs across weights/seeds.
    tokens={}
    for key, natural_rows in data.items():
        observed=natural_rows+raw_controls[key]
        for r in observed:
            m=r.get('generation_metadata') or {}
            if r.get('response') is None or m.get('backend_error'):continue
            ids=m.get('input_token_ids');key=r['presentation_id']
            if ids is None or key in tokens and tokens[key]!=ids:raise ValueError('Target-free input tokenization changed')
            tokens[key]=ids
    sets={'all':set(groups),'target':{b for b,g in groups.items() if g['analysis_group']=='target'},
        'untrained_ethical':{b for b,g in groups.items() if g['analysis_group'] in ['related_untrained','other_untrained_ethical']}}
    sets.update({g:{b for b,v in groups.items() if v['analysis_group']==g} for g in sorted({v['analysis_group'] for v in groups.values()})})
    if [len(sets[g]) for g in PRIMARY_GROUPS]!=[100,10,80,10] or len(sets.get('related_untrained',[]))!=6:
        raise ValueError('Changed predeclared analysis groups')
    models={};belief_rows=[]
    for arm in ARMS:
        available=[s for s in SEEDS if (arm,s) in data and ('base',s) in data]
        if not available:continue
        seeds={}
        for seed in available:
            observed=data[arm,seed];before=data['base',seed]
            controls=raw_controls[arm,seed];checks=operational_controls(control_bank,controls)
            base_checks=operational_controls(control_bank,raw_controls['base',seed])
            seeds[str(seed)]={'endpoints':{name:endpoint([r for r in observed if r['belief_id'] in ids],[r for r in before if r['belief_id'] in ids]) for name,ids in sets.items()},
                'agreement':{axis:agreement(observed,axis) for axis in ['order','wording']},
                'model_checks':checks,'controls_passed':checks['operational_passed'],
                'base_controls_passed':base_checks['operational_passed'],
                'native_control_summary':summaries[arm,seed]['meta_eval']['model_controls']['stance'],
                'strict':sum(valid(r) and bool(r.get('strict_format')) for r in observed),'expected':len(observed),
                'failures':[{k:r.get(k) for k in ['presentation_id','error','strict_format','final_response']}|{'error_codes':diagnostic_codes(r),'finish_reason':(r.get('generation_metadata') or {}).get('finish_reason')} for r in observed if r.get('error') or not r.get('strict_format')]}
        pooled=[r for s in available for r in data[arm,s]];base=[r for s in available for r in data['base',s]]
        endpoints={name:endpoint([r for r in pooled if r['belief_id'] in ids],[r for r in base if r['belief_id'] in ids]) for name,ids in sets.items()}
        # An unfinished planned repeat is not silently pooled into a full estimate.
        complete=len(available)==len(SEEDS)
        models[arm]={'complete_seeds':complete,'seeds':seeds,'pooled_completed_seeds':endpoints,
            'operational_precision_passed':complete and all(v['controls_passed'] and v['base_controls_passed'] and all(v['endpoints'][g]['precision_passed'] and v['endpoints'][g]['base']['precision_passed'] for g in PRIMARY_GROUPS) for v in seeds.values()) and all(endpoints[g]['precision_passed'] and endpoints[g]['base']['precision_passed'] for g in PRIMARY_GROUPS),
            'semantic_review_completed':False,
            'drift_seed_variability':{name:spread([seeds.get(str(s),{}).get('endpoints',{}).get(name,{}).get('drift') for s in SEEDS]) for name in sets},
            'same_prompt':agreement(pooled,'same_prompt') if complete else None,
            'within_prompt':{axis:combine([seeds[str(s)]['agreement'][axis] for s in available]) for axis in ['order','wording']}}
        for bid in sorted(groups):
            belief_rows.append({'model':arm,'belief_id':bid,**groups[bid],'complete_seeds':complete,'evaluation_seeds':available,
                **belief_endpoint([r for r in pooled if r['belief_id']==bid],[r for r in base if r['belief_id']==bid])})
    contrast=[]
    for seed in SEEDS:
        if ('positive',seed) not in data or ('negative',seed) not in data:continue
        p=[r for r in data['positive',seed] if r['belief_id'] in sets['target']];n=[r for r in data['negative',seed] if r['belief_id'] in sets['target']]
        contrast.append({'seed':seed,**endpoint(p,n)})
    control_contrasts=[]
    for seed in SEEDS:
        for treatment in ['positive','negative']:
            for control in ['offtopic','c4_only']:
                if (treatment,seed) not in data or (control,seed) not in data:continue
                control_contrasts.append({'seed':seed,'treatment':treatment,'control':control,
                    'endpoints':{name:endpoint([r for r in data[treatment,seed] if r['belief_id'] in ids],
                                              [r for r in data[control,seed] if r['belief_id'] in ids]) for name,ids in sets.items()}})
    interpretation='Canonical-position forced relative choice without a Target line; not independent endorsement, ethical accuracy or confidence. Negation agreement is not measured. All100beliefs retained. Missing-response bounds are not confidence intervals. Three evaluation seeds on one training seed; no training replication. Historical results and failed gates unchanged; no automatic training approval or scale-up.'
    report={'run_id':MASTER,'policy_id':POLICY,'complete':not pending,'pending':pending,'models':models,
        'positive_minus_negative_target':contrast,'contrast_seed_variability':spread([next((c['drift'] for c in contrast if c['seed']==s),None) for s in SEEDS]),
        'treatment_minus_control':control_contrasts,'sources':sources,'interpretation':interpretation,'semantic_interpretation_status':'pending_preselected_raw_review',
        'primary_aggregate_groups':PRIMARY_GROUPS,'missing_bound_width_max':.01,
        'specificity':{a:{s:specificity(v['endpoints']) for s,v in m['seeds'].items()} for a,m in models.items()}}
    result.mkdir(parents=True,exist_ok=True);stem='progress' if partial else 'analysis';out=result/(stem+'.json')
    if not partial and out.exists():raise FileExistsError('Completed target-free analysis exists')
    out.write_text(json.dumps(report,indent=2)+'\n');out.with_suffix('.md').write_text('# Target-free relative-choice readout\n\n'+interpretation+'\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    p=result/('per_belief_progress.jsonl' if partial else 'per_belief_results.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in belief_rows));write_md(p)
    selected=rows(generated/'review_selection.jsonl');review=[];review_pending=[]
    for item in selected:
        key=(item['arm'],item['seed'])
        if key not in data:review_pending.append(item);continue
        observed=next(r for r in data[key] if r['presentation_id']==item['presentation_id'])
        review.append({**item,'observation':observed})
    failures=[{'arm':a,'seed':s,'observation':r,'error_codes':diagnostic_codes(r,control=True)} for (a,s),controls in raw_controls.items() for r in controls
              if not valid(r) or r['answer']!=r['expected'] or not r.get('strict_format') or (r.get('generation_metadata') or {}).get('finish_reason')!='stop']
    for stem,records in [('natural_review_progress' if partial else 'natural_review',review),
                         ('control_failures_progress' if partial else 'control_failures',failures)]:
        p=result/(stem+'.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in records));write_md(p)
    review_status={'expected':len(selected),'collected':len(review),'pending':review_pending,'agent_review_completed':False}
    p=result/('review_status_progress.json' if partial else 'review_status.json');p.write_text(json.dumps(review_status,indent=2)+'\n')
    p.with_suffix('.md').write_text('# Preselected review coverage\n\n```json\n'+json.dumps(review_status,indent=2)+'\n```\n')
    print(json.dumps({'complete':not pending,'pending':pending,'models':list(models),'contrast_seed_variability':report['contrast_seed_variability']},indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
