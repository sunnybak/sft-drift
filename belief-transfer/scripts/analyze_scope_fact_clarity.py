"""Paired syntax effects with frozen native-extractor replay, no qualification gate."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
import re
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import config_sha
from belief_transfer.metrics.response_interface_rca import summarize
from belief_transfer.schemas import JobConfig
from belief_transfer.stages.measurements import observed_backend_reply
from belief_transfer.validation.response_interface_rca import assess
from run_scope_fact_clarity import MASTER,ARMS,read,rows,sha,check_config


def counts(items):
    n=len(items)
    if not n:raise ValueError('An expected nonempty diagnostic grid is required')
    return {'expected':n,'valid':sum(r['native_answer'] is not None and not r['native_error'] for r in items),
        'correct':sum(r['native_correct'] for r in items),'strict':sum(r['native_strict'] for r in items),
        'normal_stop':sum(r['finish_reason']=='stop' for r in items),
        'caps':sum(r['finish_reason']=='length' for r in items),
        'generic_correct':sum(r['generic_correct'] for r in items),
        'parser_disagreements':sum(r['parser_disagreement'] for r in items)}


def inspect_model(root,item,protocol):
    import yaml
    generated=root/'generated/ethical_pilot'/MASTER;folder=root/'results/ethical_pilot'/item['run_id']
    if not (folder/'COMPLETED').exists():raise ValueError('Clarity child incomplete')
    bank=rows(folder/'bank.jsonl');observed=rows(folder/'observations.jsonl')
    manifest=read(folder/'manifest.json');summary=read(folder/'summary.json');proof=protocol['runtime_evidence'][item['arm']]
    if (sha(folder/'bank.jsonl')!=protocol['bank_sha256'] or bank!=rows(generated/'bank.jsonl')
        or len(bank)!=128 or Counter(r['presentation_id'] for r in observed)!=Counter(r['presentation_id'] for r in bank)):
        raise ValueError('Clarity bank/grid changed')
    expected_manifest={'model_label':item['arm'],'bank_sha256':protocol['bank_sha256'],
        'adapter_sha256':item['adapter_sha256'],'model_config':proof['model_config'],
        'backend':proof['backend'],'decoder':proof['decoder'],'max_new_tokens':proof['max_new_tokens'],
        'generation':proof['generation'],'versions':proof['versions']}
    if any(manifest.get(k)!=v for k,v in expected_manifest.items()):raise ValueError('Clarity runtime/model manifest changed')
    started=root/'results/ethical_pilot'/MASTER/'STARTED'
    full_revision=started.read_text().strip();stage_revision=manifest['code_revision']
    if (not re.fullmatch(r'[0-9a-f]{40}',full_revision) or not re.fullmatch(r'[0-9a-f]{7,40}',stage_revision)
        or not full_revision.startswith(stage_revision)):raise ValueError('Clarity source commit changed')
    resolved=JobConfig.model_validate(yaml.safe_load((folder/'config.resolved.yaml').read_text()));check_config(resolved,proof)
    if resolved.run_id!=item['run_id'] or config_sha(resolved)!=item['resolved_config_sha']:raise ValueError('Clarity resolved config changed')
    rebuilt=summarize(observed)
    if any(summary.get(k)!=rebuilt[k] for k in ['overall','by_vocabulary','by_vocabulary_representation']):
        raise ValueError('Clarity generic summary does not reconstruct')
    references={r['presentation_id']:r for r in bank};replayed=[];failures=[]
    for row in observed:
        reference=references[row['presentation_id']]
        if any(row.get(k)!=v for k,v in reference.items()):raise ValueError('Clarity observation input changed')
        meta=row.get('generation_metadata') or {};text=row.get('response')
        if text is None or meta.get('backend_error'):raise ValueError('Clarity backend failure')
        if (meta.get('execution')!=proof['generation'] or meta.get('execution_versions')!=proof['versions']
            or meta.get('model_revision')!=proof['generation']['revision']
            or meta.get('adapter_lora_id')!=(1 if item['adapter_sha256'] else None)
            or meta.get('sampling_seed')!=row['sampling_seed']
            or meta.get('prompt_tokens')!=row['expected_input_tokens']
            or len(meta.get('input_token_ids',[]))!=row['expected_input_tokens']
            or meta.get('generation_tokens')!=len(meta.get('output_token_ids',[]))
            or not 0<meta.get('generation_tokens',0)<=proof['max_new_tokens']
            or meta.get('finish_reason') not in ['stop','length']):raise ValueError('Clarity raw runtime/seed metadata changed')
        generic=assess(reference,text,meta,thinking=proof['decoder']['thinking'])
        if any(row.get(k)!=v for k,v in generic.items()):raise ValueError('Clarity generic extraction changed')
        native=observed_backend_reply(reference['native_reference'],text,meta,
            thinking=proof['decoder']['thinking'],seed=row['sampling_seed'])
        generic_semantic=('agree' if row['support_by_word'][generic['answer']] else 'disagree') if generic['answer'] is not None else None
        correct=native['answer']==reference['native_reference']['expected'] and not native.get('error')
        replayed.append({k:row[k] for k in ['presentation_id','context_id','family','wording_variant','realization','order','changed_prompt','prompt_sha256','sampling_seed']}|{
            'native_answer':native['answer'],'native_error':native.get('error'),'native_correct':bool(correct),
            'native_strict':bool(native['strict_format']),'generic_answer':generic['answer'],
            'generic_correct':bool(generic['correct']),'parser_disagreement':generic_semantic!=native['answer'],
            'finish_reason':meta['finish_reason']})
        if not correct or not native['strict_format'] or generic_semantic!=native['answer']:
            failures.append({'arm':item['arm'],'observation':row,'native_replay':native})
    return bank,observed,replayed,failures


def analyze(root=Path('data'),*,partial=False):
    generated=root/'generated/ethical_pilot'/MASTER;result=root/'results/ethical_pilot'/MASTER
    protocol=read(generated/'protocol.json');models={};pending=[];all_replays=[];failures=[];tokens={};sources=[]
    from run_scope_fact_clarity import run_ids
    if [(j['arm'],'clarity',j['run_id']) for j in protocol['jobs']]!=run_ids():raise ValueError('Clarity schedule changed')
    if len(rows(generated/'bank.jsonl'))!=128 or sha(generated/'bank.jsonl')!=protocol['bank_sha256']:raise ValueError('Clarity frozen bank changed')
    for item in protocol['jobs']:
        folder=root/'results/ethical_pilot'/item['run_id']
        if not (folder/'COMPLETED').exists():pending.append(item['run_id']);continue
        bank,observed,replayed,failed=inspect_model(root,item,protocol)
        for row in observed:
            key=row['prompt_sha256'];ids=row['generation_metadata']['input_token_ids']
            if key in tokens and tokens[key]!=ids:raise ValueError('Clarity tokenization changed between identical inputs')
            tokens[key]=ids
        pairs=defaultdict(dict)
        for row in replayed:
            key=(row['context_id'],row['order'],row['realization'])
            if row['wording_variant'] in pairs[key]:raise ValueError('Duplicate clarity variant')
            pairs[key][row['wording_variant']]=row
        if len(pairs)!=64 or any(set(v)!={'original','explicit_facts'} for v in pairs.values()):raise ValueError('Clarity pair grid changed')
        pair_rows=[]
        for key,pair in pairs.items():
            a,b=pair['original'],pair['explicit_facts']
            if a['sampling_seed']!=b['sampling_seed']:raise ValueError('Clarity matched request seeds changed')
            pair_rows.append({'context_id':key[0],'order':key[1],'realization':key[2],
                'changed_prompt':b['changed_prompt'],'original_correct':a['native_correct'],
                'explicit_correct':b['native_correct'],'both_valid':all(r['native_answer'] is not None and not r['native_error'] for r in [a,b]),
                'same_answer':a['native_answer']==b['native_answer'] if all(r['native_answer'] is not None and not r['native_error'] for r in [a,b]) else None})
        def paired(items):
            return {'expected_pairs':len(items),'eligible_pairs':sum(r['both_valid'] for r in items),
                'same_answer':sum(r['same_answer'] is True for r in items),
                'original_wrong_explicit_correct':sum(not r['original_correct'] and r['explicit_correct'] for r in items),
                'original_correct_explicit_wrong':sum(r['original_correct'] and not r['explicit_correct'] for r in items)}
        models[item['arm']]={'versions':{v:counts([r for r in replayed if r['wording_variant']==v]) for v in ['original','explicit_facts']},
            'families':{f:{v:counts([r for r in replayed if r['family']==f and r['wording_variant']==v]) for v in ['original','explicit_facts']}
                        for f in sorted({r['family'] for r in replayed})},
            'paired_changed':paired([r for r in pair_rows if r['changed_prompt']]),
            'paired_unchanged':paired([r for r in pair_rows if not r['changed_prompt']]),'pairs':pair_rows}
        all_replays += [{'arm':item['arm'],**r} for r in replayed];failures += failed
        sources += [{'path':str(folder/name),'sha256':sha(folder/name)} for name in ['bank.jsonl','observations.jsonl','manifest.json','summary.json','config.resolved.yaml']]
    if pending and not partial:raise ValueError('Clarity jobs pending: '+','.join(pending))
    report={'run_id':MASTER,'complete':not pending,'pending':pending,'models':models,'sources':sources,
        'interpretation':'Paired wording on16reused contexts/one checkpoint per arm; correlated variants and shared RNGare not independent trials. Native frozen extraction is primary; generic/native disagreements explicit. No original score/gate repair, population error-rate claim, independent qualification or automatic training/scale-up.'}
    result.mkdir(parents=True,exist_ok=True);stem='progress' if partial else 'analysis';path=result/(stem+'.json')
    if not partial and path.exists():raise FileExistsError('Completed clarity analysis is immutable')
    path.write_text(json.dumps(report,indent=2)+'\n');path.with_suffix('.md').write_text('# Paired scope-fact wording results\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    for name,items in [('native_replay',all_replays),('failed_responses',failures)]:
        p=result/(name+('_progress' if partial else '')+'.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in items));write_md(p)
    print(json.dumps({'complete':not pending,'models':list(models),'pending':pending}));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
