"""Read-only matched RCA analysis; no weights or instrument changes."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.metrics.control_recheck import summarize
MASTER='ethics_gpu_error_rca_v1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def rows(path):return list(map(json.loads,path.read_text().splitlines()))
def compare(a,b):
    left={r['presentation_id']:r for r in a};right={r['presentation_id']:r for r in b}
    if left.keys()!=right.keys():raise ValueError('Comparison banks differ')
    input_mismatch=[];status_changes=0;flips=0;better=worse=0
    for key,r in left.items():
        s=right[key]
        if r['prompt_sha']!=s['prompt_sha'] or r['expected']!=s['expected']:raise ValueError('Changed prompt/answer key')
        if r.get('generation_metadata',{}).get('input_token_ids')!=s.get('generation_metadata',{}).get('input_token_ids'):input_mismatch.append(key)
        x,y=r.get('answer'),s.get('answer');status_changes+=x!=y
        flips+=x in ['agree','disagree'] and y in ['agree','disagree'] and x!=y
        ac=not r.get('error') and x==r['expected'];bc=not s.get('error') and y==s['expected']
        better+=bc and not ac;worse+=ac and not bc
    return {'n':len(left),'input_token_mismatches':input_mismatch,'answer_status_changes':status_changes,
            'valid_label_flips':flips,'second_better':better,'second_worse':worse,'agreement':1-status_changes/len(left)}
def summarize_errors(observed):
    return dict(Counter('backend' if r.get('generation_metadata',{}).get('backend_error') else
       'length' if r.get('generation_metadata',{}).get('finish_reason')=='length' else
       'invalid_extraction' if r.get('error') or r.get('answer') not in ['agree','disagree'] else
       'wrong_valid_label' if r['answer']!=r['expected'] else
       'format' if not r.get('strict_format') else 'correct_strict' for r in observed))
def analyze(root=Path('data'),*,partial=False):
    generated=root/'generated/ethical_pilot'/MASTER;result=root/'results/ethical_pilot'/MASTER
    protocol=read(generated/'protocol.json');profiles={};collected={};sources=[];pending=[]
    for job in protocol['jobs']:
        child=root/'results/ethical_pilot'/job['run_id']
        if not (child/'COMPLETED').exists():pending.append(job['run_id']);continue
        bank=rows(child/'control_bank.jsonl');observed=rows(child/'observations.jsonl')
        if len(bank)!=job['expected'] or len(observed)!=len(bank):raise ValueError('Incomplete audit declared complete')
        if Counter(r['presentation_id'] for r in bank)!=Counter(r['presentation_id'] for r in observed) or len({r['presentation_id'] for r in bank})!=len(bank):raise ValueError('Missing/duplicate audit identity')
        expected={r['presentation_id']:r for r in bank}
        if any(any(r.get(k)!=v for k,v in expected[r['presentation_id']].items()) for r in observed):raise ValueError('Observation changed frozen bank fields')
        manifest=read(child/'manifest.json')
        if manifest['adapter_sha256']!=job['adapter_sha256']:raise ValueError('Wrong adapter binding')
        if any(r.get('generation_metadata',{}).get('model_revision')!='1cfa9a7208912126459214e8b04321603b3df60c' for r in observed):raise ValueError('Missing/mismatched model revision')
        summary=summarize(observed)
        profiles.setdefault(job['profile'],{})[job['arm']]={'run_id':job['run_id'],'forms':summary['forms'],'errors':summarize_errors(observed)}
        collected[job['arm'],job['profile']]=observed
        sources.extend({'path':str(child/name),'sha256':sha(child/name)} for name in ['manifest.json','control_bank.jsonl','observations.jsonl','summary.json'])
    if pending and not partial:raise ValueError('Audits pending: '+', '.join(pending))
    parity={}
    for arm in ['base','offtopic']:
        if all((arm,p) in collected for p in ['nonthink_greedy','hf_greedy']):parity[arm]=compare(collected[arm,'hf_greedy'],collected[arm,'nonthink_greedy'])
    changes={}
    for profile,arms in profiles.items():
        if 'base' not in arms:continue
        changes[profile]={arm:{form:{'accuracy_pp':100*(m['forms'][form]['accuracy']-arms['base']['forms'][form]['accuracy']),
            'strict_format_pp':100*(m['forms'][form]['strict']/m['forms'][form]['expected']-arms['base']['forms'][form]['strict']/arms['base']['forms'][form]['expected'])}
            for form in ['legacy','original','truth_explicit']} for arm,m in arms.items() if arm!='base'}
    report={'run_id':MASTER,'complete':not pending,'pending':pending,'profiles':profiles,'adapter_minus_base':changes,'hf_vllm_greedy_parity':parity,'sources':sources,
       'interpretation':'Development checks on reused facts. No gate changes, passing-only selection, independent-presentation confidence claims or new ethical stance measurements. HF/vLLM differences include runtime numerical differences; agreement alone does not establish equal logits.'}
    result.mkdir(parents=True,exist_ok=True)
    dest=result/('progress.json' if partial else 'analysis.json')
    if not partial and dest.exists():raise FileExistsError('Completed analysis already exists')
    temporary=dest.with_suffix('.tmp');temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(dest)
    dest.with_suffix('.md').write_text('# Decoder/backend RCA '+('progress' if partial else 'results')+'\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps({k:v for k,v in report.items() if k!='sources'},indent=2))
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args();analyze(partial=args.allow_partial)
