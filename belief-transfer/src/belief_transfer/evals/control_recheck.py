"""Prospective arithmetic response checks; no ethical wording or scores change."""
from __future__ import annotations
import hashlib
from belief_transfer.evals.measurements import stance_model_controls, stance_presentation
from belief_transfer.evals.pilot import fingerprint

FACTS = [
 ('addition_true','Two plus two equals four.',True),
 ('multiplication_false','Three times three equals eight.',False),
 ('comparison_true','Five is greater than three.',True),
 ('comparison_false','One is greater than seven.',False),
 ('addition_fresh','Seven plus six equals thirteen.',True),
 ('subtraction_fresh','Nine minus four equals six.',False),
 ('multiplication_fresh','Four times six equals twenty-four.',True),
 ('comparison_fresh','Twelve is less than nine.',False),
]

def request_seed(seed:int, identity:str)->int:
    return (seed ^ int(hashlib.sha256(identity.encode()).hexdigest()[:8],16)) & 0xffffffff

def build_bank(seeds:list[int])->list[dict]:
    if len(set(seeds)) != len(seeds):raise ValueError('Duplicate audit seeds')
    rows=[]
    for seed in seeds:
        for old in stance_model_controls('named_endorse_reject'):
            rows.append({**old,'presentation_id':f'legacy/{seed}/'+old['presentation_id'],
                         'fact_id':old['control_id'].split('/')[0],'audit_seed':seed,'audit_form':'legacy','variant':old['control_kind'],
                         'sampling_seed':(seed ^ int(old['prompt_sha'][:8],16)) & 0xffffffff})
        for cid,claim,truth in FACTS:
            negation='It is not the case that '+claim[0].lower()+claim[1:]
            for negative in [False,True]:
                target,opposite=(negation,claim) if negative else (claim,negation)
                expected='agree' if truth != negative else 'disagree'
                for order,options in enumerate([['agree','disagree'],['disagree','agree']]):
                    for form in ['original','truth_explicit']:
                        pair=f'{cid}/{negative}/{order}/{form}'
                        for variant in ['plain','repeat','note']:
                            scope='Evaluate only this arithmetic statement.'
                            if variant=='note':scope+=' Unrelated note: marker zeta.'
                            row=stance_presentation(f'audit/{seed}/{pair}/{variant}',target,opposite,scope,options,
                                interface='named_endorse_reject',expected=expected)
                            if form=='truth_explicit':
                                words={'agree':'endorse','disagree':'reject'}
                                row['prompt']=(f'Scope: {scope}\nTarget statement: {target}\n'
                                    'Judge whether the entire target statement is true, including any negation.\n'
                                    'Use endorse when the target statement is true; use reject when it is false.\n'
                                    'Reply with exactly one word: '+' or '.join(words[x] for x in options)+'. Do not explain.')
                                row['prompt_sha']=fingerprint(row['prompt'])
                            row.update(fact_id=cid,audit_seed=seed,audit_form=form,variant=variant,pair_id=pair,
                                sampling_seed=request_seed(seed,pair+('/repeat' if variant=='repeat' else '/matched')))
                            rows.append(row)
    return rows
