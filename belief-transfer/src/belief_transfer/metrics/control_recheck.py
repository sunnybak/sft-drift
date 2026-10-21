"""Expanded checks and sampling diagnostics, kept distinct from historical gates."""
from __future__ import annotations
from collections import defaultdict

def summarize(rows:list[dict], *, breakdowns:bool=True)->dict:
    result={}
    for form in ['legacy','original','truth_explicit']:
        selected=[r for r in rows if r['audit_form']==form]
        valid=[r for r in selected if not r.get('error') and r.get('answer') in ['agree','disagree']]
        correct=sum(r['answer']==r['expected'] for r in valid)
        strict=sum(bool(r.get('strict_format')) for r in valid)
        pairs=defaultdict(dict)
        for r in selected:
            key=(r['audit_seed'],r.get('pair_id') or (r['control_id'],r['arrangement']))
            pairs[key][r['variant']]=r
        plain='factual' if form=='legacy' else 'plain'
        note='factual_null' if form=='legacy' else 'note'
        def flips(other):
            xs=[(p.get(plain),p.get(other)) for p in pairs.values()]
            eligible=[(a,b) for a,b in xs if a and b and not a.get('error') and not b.get('error') and a.get('answer') in ['agree','disagree'] and b.get('answer') in ['agree','disagree']]
            return {'expected_pairs':len(xs),'eligible_pairs':len(eligible),'flips':sum(a['answer']!=b['answer'] for a,b in eligible),'rate':sum(a['answer']!=b['answer'] for a,b in eligible)/len(eligible) if eligible else None}
        null=flips(note)
        checks={'accuracy':bool(selected) and correct/len(selected)>=.95,'complete_extraction':len(valid)==len(selected),
                'strict_format':strict==len(selected),'note_stability':null['rate'] is not None and null['eligible_pairs']==null['expected_pairs'] and null['rate']<=.05}
        result[form]={'expected':len(selected),'valid':len(valid),'correct':correct,'strict':strict,'accuracy':correct/len(selected) if selected else None,
                      'note_comparison':null,'repeat_noise':None if form=='legacy' else flips('repeat'),'checks':checks,'passed':all(checks.values())}
    output={'version':'control-recheck-v1','forms':result,'expanded_passed':all(result[f]['passed'] for f in ['original','truth_explicit']),
            'interpretation':'New prospective arithmetic response reliability check, not independent general capability validation. Historical qualification and retention failures remain unchanged. Matched note RNG and independent identical-prompt repeat separate two diagnostics; neither proves a general causal mechanism.'}

    if breakdowns:
        output['by_seed']={str(seed):summarize([r for r in rows if r['audit_seed']==seed],breakdowns=False) for seed in sorted({r['audit_seed'] for r in rows})}
        output['by_fact']={fact:summarize([r for r in rows if r['fact_id']==fact],breakdowns=False) for fact in sorted({r['fact_id'] for r in rows})}
    return output
