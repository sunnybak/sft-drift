"""Read-only factorial development analysis; not a qualification or ethical score."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.metrics.response_interface_rca import summarize
MASTER='ethics_gpu_response_interface_rca_v1'
REVISION='1cfa9a7208912126459214e8b04321603b3df60c'
def read(path):return json.loads(path.read_text())
def rows(path):return list(map(json.loads,path.read_text().splitlines()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def paired(a,b):
 left={r['presentation_id']:r for r in a};right={r['presentation_id']:r for r in b}
 if len(left)!=len(a) or len(right)!=len(b) or left.keys()!=right.keys():raise ValueError('Unmatched/duplicate presentations')
 for key,r in left.items():
  s=right[key]
  if any(r[k]!=s[k] for k in ['prompt_sha256','expected_word','sampling_seed']):raise ValueError('Changed paired inputs')
 return {'n':len(a),'answer_changes':sum(r['answer']!=right[k]['answer'] for k,r in left.items()),
  'second_better':sum(right[k]['correct'] and not r['correct'] for k,r in left.items()),
  'second_worse':sum(r['correct'] and not right[k]['correct'] for k,r in left.items()),
  'input_token_mismatches':[k for k,r in left.items() if r.get('generation_metadata',{}).get('input_token_ids')!=right[k].get('generation_metadata',{}).get('input_token_ids')]}
def analyze(root=Path('data'),*,partial=False):
 generated=root/'generated/ethical_pilot'/MASTER;result=root/'results/ethical_pilot'/MASTER
 protocol=read(generated/'protocol.json');bank=rows(generated/'bank.jsonl')
 expected={r['presentation_id']:r for r in bank};collected={};pending=[];sources=[];report={};raw={}
 for job in protocol['jobs']:
  child=root/'results/ethical_pilot'/job['run_id']
  if not (child/'COMPLETED').exists():pending.append(job['run_id']);continue
  observed=rows(child/'observations.jsonl');manifest=read(child/'manifest.json')
  if len(observed)!=256 or Counter(r['presentation_id'] for r in observed)!=Counter(expected.keys()):raise ValueError('Incomplete/duplicate bank')
  if any(any(r.get(k)!=v for k,v in expected[r['presentation_id']].items()) for r in observed):raise ValueError('Changed bank fields')
  if manifest['adapter_sha256']!=job['adapter_sha256'] or manifest['bank_sha256']!=sha(generated/'bank.jsonl'):raise ValueError('Changed adapter/bank binding')
  for r in observed:
   meta=r.get('generation_metadata',{})
   if r.get('response') is not None and meta.get('model_revision')!=REVISION:raise ValueError('Missing/mismatched runtime revision')
  summary=summarize(observed);summary['errors']=dict(Counter(r['error'] for r in observed if r.get('error')))
  summary['by_fact_polarity']={f'{fact}/{negative}':{'n':len(xs),'correct':sum(r['correct'] for r in xs)} for fact in sorted({r['fact_id'] for r in observed}) for negative in [False,True] if (xs:=[r for r in observed if r['fact_id']==fact and r['negative']==negative])}
  report.setdefault(job['mode'],{})[job['arm']]=summary;raw[job['mode'],job['arm']]=observed
  sources.extend({'path':str(child/name),'sha256':sha(child/name)} for name in ['manifest.json','bank.jsonl','observations.jsonl','summary.json'])
 if pending and not partial:raise ValueError('Pending: '+', '.join(pending))
 changes={mode:paired(raw[mode,'base'],raw[mode,'offtopic']) for mode in ['nonthinking','thinking'] if all((mode,a) in raw for a in ['base','offtopic'])}
 candidates=[{'mode':mode,'vocabulary':v} for mode in ['nonthinking','thinking'] for v in ['yes_no','true_false','agree_disagree','endorse_reject'] if report.get(mode,{}).get('base',{}).get('by_vocabulary',{}).get(v,{}).get('development_pass')]
 output={'run_id':MASTER,'complete':not pending,'pending':pending,'profiles':report,'offtopic_vs_base':changes,'base_development_candidates_in_preregistered_order':candidates,'sources':sources,
 'interpretation':'Eight reused development facts. Report every cell. No old gates changed, no independent model qualification, no ethical measurements; fresh held-out all-model validation required before adoption.'}
 result.mkdir(parents=True,exist_ok=True);dest=result/('progress.json' if partial else 'analysis.json')
 if not partial and dest.exists():raise FileExistsError('Completed analysis already exists')
 temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(output,indent=2)+'\n');temp.replace(dest)
 dest.with_suffix('.md').write_text('# Response-interface development results\n\n```json\n'+json.dumps(output,indent=2)+'\n```\n')
 print(json.dumps({k:v for k,v in output.items() if k!='sources'},indent=2));return output
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
