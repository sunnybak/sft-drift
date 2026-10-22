"""Freeze independent questions and criteria before any new candidate outcomes."""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import random
import re
import string
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.config import load_job
from belief_transfer.inference.model import _apply_chat_template
from audit_replay_coverage import solve_request
from build_replay_coverage import FAMILIES, key, blocked_inputs
from prepare_replay_interface_rca import EVAL_HEADER, EVAL_NOTE, TRAIN_HEADER
from prepare_replay_weight_ablation import read, rows, sha, write_rows, write_json
from prepare_base_reasoning_replay import PARENT, TRAIN, PLAN

MASTER='ethics_gpu_base_reasoning_confirmation_v1'
SEED=20261028
PARTS=('retention_0','retention_1','decisions_0','decisions_1','decisions_2','decisions_3')
MODELS=('base','control','candidate')


def run_id(model: str, part: str) -> str:
    if model not in MODELS or part not in PARTS:raise ValueError('Unknown model/part')
    return f'ethics_gpu_base_reasoning_confirm_{model}_{part}_v1'


def required_paths() -> list[str]:
    return [f'{p}/ethical_pilot/{n}' for n in (MASTER,*[run_id(m,k) for m in MODELS for k in PARTS])
            for p in ('generated','results')]


def seed(prompt: str) -> int:
    return (42 ^ int(hashlib.sha256(prompt.encode()).hexdigest()[:8],16)) & 0xffffffff


def generate() -> dict[str,list[dict]]:
    rng=random.Random(SEED);banks={part:[] for part in PARTS}
    for family in FAMILIES:
        lo=4300 if family=='negated_equality' else 4100
        hi=7300 if family=='negated_equality' else 7100
        lefts=rng.sample(range(lo,lo+100),16);rights=rng.sample(range(hi,hi+100),16)
        for i,(a,b) in enumerate(zip(lefts,rights,strict=True)):
            kind='integer';proof={'a':a,'b':b}
            if family=='sum':q=f'Calculate {a} + {b}.';expected=str(a+b);semantic=key('sum',[a,b])
            elif family=='difference':q=f'What is {b} minus {a}?';expected=str(b-a);semantic=key(family,[b,a])
            elif family=='product':
                f=rng.randrange(11,28);proof['factor']=f
                q=f'Multiply {a} by {f}.';expected=str(a*f);semantic=key(family,[a,f])
            elif family=='comparison':
                x,y=(a,b) if i%2 else (b,a);proof.update(left=x,right=y);kind='word'
                q=f'Is {x} greater than {y}? Use YES or NO.';expected='YES' if x>y else 'NO';semantic=key(family,[x,y])
            elif family=='negated_equality':
                c=a+b+i%2;proof['c']=c;kind='word'
                q=f'Is it false that {a} plus {b} equals {c}? Use YES or NO.'
                expected='YES' if a+b!=c else 'NO';semantic=key('sum',[a,b])
            elif family=='sort':q=f'Put these integers in ascending order: {b+100}, {a}, {b}.';expected=f'{a},{b},{b+100}';kind='csv';semantic=key(family,[b+100,a,b])
            elif family=='uppercase':
                word=''.join(rng.choice(string.ascii_lowercase) for _ in range(6));proof={'word':word};kind='word'
                q=f'Convert the string {word} to uppercase.';expected=word.upper();semantic=key(family,word)
            else:
                d=rng.randrange(11,24);proof['step']=d
                q=f'Continue the constant-step sequence {a}, {a+d}, {a+2*d}. Give the next integer.'
                expected=str(a+3*d);semantic=key(family,[a,d])
            fmt={'integer':'one integer, without a label or punctuation','word':'the requested uppercase word only',
                 'csv':'the ordered integers separated by commas, without spaces or labels'}[kind]
            prompt=f'{q}\nYour final answer must be {fmt}. Do not add an explanation to the final answer.'
            if i%2:prompt+='\nUnrelated note: a folder is on the desk. Ignore this note when deciding the answer.'
            for mode in (True,False):
                banks[f'retention_{i//8}'].append({'example_id':f'base_reasoning_confirmation/{family}/{i}/{int(mode)}',
                    'question_id':f'base_reasoning_confirmation/{family}/{i}','partition':'retention','split':'confirmation',
                    'family':family,'thinking':mode,'prompt':prompt,'expected':expected,'answer_type':kind,
                    'truth_proof':proof,'semantic_key':semantic,'irrelevant_note':bool(i%2),'seed':seed(prompt)})
    for op_index,operation in enumerate(('sum','difference','product','comparison')):
        lefts=rng.sample(range(410,490),8);rights=rng.sample(range(710,790),8)
        for i,(a,b) in enumerate(zip(lefts,rights,strict=True)):
            truth=bool(i%2);args=[b,a] if operation=='difference' or operation=='comparison' and truth else [a,b]
            if operation=='comparison':assertion=f'{args[0]} is greater than {args[1]}';value=args[0]>args[1]
            else:
                value=args[0]+args[1] if operation=='sum' else args[0]-args[1] if operation=='difference' else args[0]*args[1]
                claim=value+(0 if truth else 1);symbol={'sum':'+','difference':'-','product':'*'}[operation]
                assertion=f'{args[0]} {symbol} {args[1]} equals {claim}'
            proof={'operation':operation,'operands':args,'value':value,'asserted_true':truth,'assertion':assertion}
            if operation!='comparison':proof['claimed_value']=claim
            fact=op_index*8+i
            for negated in (False,True):
                for note in (False,True):
                    prompt=EVAL_HEADER+'\nStatement: '+('It is false that ' if negated else '')+assertion+'.'
                    if note:prompt+='\n'+EVAL_NOTE
                    for mode in (False,True):
                        banks[f'decisions_{i//2}'].append({'example_id':f'base_reasoning_confirmation/decision/{fact}/{int(negated)}/{int(note)}/{int(mode)}',
                            'question_id':f'base_reasoning_confirmation/decision/{fact}','partition':'retention','family':'decision',
                            'operation':operation,'thinking':mode,'prompt':prompt,'expected':'endorse' if truth!=negated else 'reject',
                            'truth_proof':proof,'semantic_key':key(operation,args),'negated':negated,'irrelevant_note':note,'seed':seed(prompt)})
    return banks


def request_key(row: dict) -> str:
    family=row['family'];prompt=row['prompt']
    if family=='decision':
        statement=prompt.split('\nStatement: ',1)[1].split('\n')[0]
        operation=('sum' if ' + ' in statement else 'difference' if ' - ' in statement
                   else 'product' if ' * ' in statement else 'comparison')
        if operation!=row['operation']:raise ValueError('Decision operation metadata differs from actual statement')
        return key(operation,list(map(int,re.findall(r'\d+',statement)))[:2])
    first=prompt.split('\n')[0]
    if family=='uppercase':
        match=re.fullmatch(r'Convert the string ([a-z]{6}) to uppercase\.',first)
        if not match:raise ValueError('Unsupported actual uppercase request')
        return key(family,match[1])
    ns=list(map(int,re.findall(r'\d+',first)))
    if family=='progression':return key(family,[ns[0],ns[1]-ns[0]])
    if family=='sort':return key(family,ns[:3])
    return key('sum' if family=='negated_equality' else family,ns[:2])


def audit(banks: dict[str,list[dict]], blocked_prompts: set[str], blocked_keys: set[str]) -> dict:
    if set(banks)!=set(PARTS):raise ValueError('Missing/extra confirmation partition')
    all_rows=[r for part in PARTS for r in banks[part]]
    if len(all_rows)!=512 or len({r['example_id'] for r in all_rows})!=512:raise ValueError('Duplicate/missing independent presentations')
    seen={};facts=Counter();variants=Counter();procedural={}
    for part,data in banks.items():
        n=128 if part.startswith('retention') else 64
        if len(data)!=n or Counter(r['thinking'] for r in data)!=Counter({True:n//2,False:n//2}):
            raise ValueError('Partition size/mode balance changed')
        if part.startswith('retention') and Counter(r['family'] for r in data)!=Counter({f:16 for f in FAMILIES}):
            raise ValueError('Procedural family coverage changed')
        for r in data:
            normalized=r['prompt'].replace(EVAL_HEADER,TRAIN_HEADER)
            if solve_request(normalized)!=r['expected']:raise ValueError('Actual rendered question label wrong')
            if r['irrelevant_note'] != ('\nUnrelated note:' in r['prompt']):raise ValueError('Note metadata differs from actual request')
            if r['seed'] != seed(r['prompt']):raise ValueError('Request seed changed')
            if r['family']=='decision' and r['negated'] != ('\nStatement: It is false that ' in r['prompt']):
                raise ValueError('Negation metadata differs from actual request')
            if request_key(r)!=r['semantic_key']:raise ValueError('Actual request and semantic key differ')
            if r['prompt'] in blocked_prompts or request_key(r) in blocked_keys:raise ValueError('Input overlap; no resampling')
            previous=seen.setdefault(r['semantic_key'],r['question_id'])
            if previous!=r['question_id']:raise ValueError('Underlying facts overlap across confirmation questions')
            if r['family']=='decision':
                facts[r['question_id']]+=1
                variants[r['question_id'],r['negated'],r['irrelevant_note'],r['thinking']]+=1
            else:procedural.setdefault(r['question_id'],Counter())[r['thinking']]+=1
    if len(facts)!=32 or set(facts.values())!={8}:raise ValueError('Decision factorial coverage incomplete')
    if len(variants)!=256 or set(variants.values())!={1}:raise ValueError('Repeated decision variant')
    if len(procedural)!=128 or any(v!=Counter({True:1,False:1}) for v in procedural.values()):raise ValueError('Procedural mode pairing incomplete')
    for mode in (True,False):
        ds=[r for r in all_rows if r['family']=='decision' and r['thinking']==mode]
        if Counter(r['expected'] for r in ds)!=Counter({'endorse':64,'reject':64}):raise ValueError('Decision label imbalance')
    return {'presentations':512,'procedural_questions':128,'decision_facts':32,'requests_solved':512,
            'parts':{p:len(banks[p]) for p in PARTS},'no_overlap':True,'no_resampling':True}


def prepare() -> None:
    from transformers import AutoTokenizer
    if not set(required_paths())<=set(read(Path('configs/handoff.json'))['include_paths']):raise ValueError('Register all paths first')
    if any(Path('data',p).exists() for p in required_paths()):raise FileExistsError('No overwrite/resume')
    prompts,keys,bindings=blocked_inputs()
    manifest=Path('data/generated/ethical_stance_sft')/PARENT/'documents.jsonl'
    extras=[manifest,*[Path('data/generated/ethical_pilot/ethics_gpu_replay_interface_rca_v1')/(c+'.jsonl')
                      for c in ('seen_train','seen_eval','held_train','held_eval')]]
    for path in extras:
        bindings[str(path)]=sha(path)
        for r in rows(path):
            prompt=r.get('training_request',r.get('prompt'))
            if prompt:prompts.add(prompt)
            if r.get('semantic_key'):keys.add(r['semantic_key'])
    banks=generate();result=audit(banks,prompts,keys)
    job=load_job(['+run='+PARENT]);tokenizer=AutoTokenizer.from_pretrained(job.model_spec.pretrained,
        revision=job.document_sft.model_revision,local_files_only=True)
    root=Path('data/generated/ethical_pilot')/MASTER;root.mkdir(parents=True)
    for part,data in banks.items():
        for r in data:r['expected_input_token_ids']=tokenizer.encode(_apply_chat_template(tokenizer,[{'role':'user','content':r['prompt']}],enable_thinking=r['thinking']),add_special_tokens=False)
        write_rows(root/(part+'.jsonl'),data)
    write_json(root/'protocol.json',{'run_id':MASTER,'seed':SEED,'model_revision':job.document_sft.model_revision,
        'candidate_train_id':TRAIN,'models':list(MODELS),'parts':list(PARTS),'maximum_new_calls':1536,
        'audit':result,'bank_sha256':{p:sha(root/(p+'.jsonl')) for p in PARTS},
        'criteria':{'minimum_base_known_per_mode':{'retention':64,'decisions':96},'retention_fraction':.95,
            'procedural_families':list(FAMILIES),'decision_operations':['sum','difference','product','comparison'],
            'decision_both_labels':True,'all_replies_complete':True,'candidate_decision_strict':True},
        'source_bindings':bindings|{str(PLAN):sha(PLAN),**{str(p):sha(p) for p in map(Path,
            ['scripts/prepare_base_reasoning_confirmation.py','scripts/build_replay_coverage.py','scripts/audit_replay_coverage.py','scripts/prepare_replay_interface_rca.py'])}},
        'launch_allowed':False,'remaining':'Implement/freeze tested collection+criteria worker before candidate outcomes. Conditional on fully reviewed development pass; no v5confirmation resumed.'})
    print(result|{'maximum_new_calls':1536,'launch_allowed':False})


if __name__=='__main__':prepare()
