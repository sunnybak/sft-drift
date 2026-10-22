"""Prospective pooled confirmation counts; no model calls or quality-based selection."""
from __future__ import annotations

from collections import Counter

FAMILIES={'sum','difference','product','comparison','negated_equality','sort','uppercase','progression'}
OPERATIONS={'sum','difference','product','comparison'}


def indexed(data: list[dict],kind: str) -> dict:
    if kind not in ('retention','decisions'):raise ValueError('Unknown confirmation kind')
    lookup={r['example_id']:r for r in data}
    if len(data)!=256 or len(lookup)!=256 or Counter(r['thinking'] for r in data)!=Counter({True:128,False:128}):
        raise ValueError('Require complete unique256row/two-mode confirmation')
    for r in data:
        value=r['value']['value_correct']
        if value is not None and type(value) is not bool:raise ValueError('Value must be bool or explicit unknown')
    return lookup


def reference_cohort(base: list[dict],kind: str) -> dict:
    indexed(base,kind)
    field='family' if kind=='retention' else 'operation'
    required=FAMILIES if kind=='retention' else OPERATIONS
    minimum=64 if kind=='retention' else 96
    known=[{k:r[k] for k in ('example_id','thinking',field,'expected','response_sha256')}
           for r in base if r['value']['value_correct'] is True]
    modes={}
    for mode in (True,False):
        group=[r for r in known if r['thinking']==mode]
        whole=[r for r in base if r['thinking']==mode]
        complete=all(r['native_assessment']['normal_stop'] and r['native_assessment']['response_boundaries_valid'] for r in whole)
        covered={r[field] for r in group}==required
        labels=kind!='decisions' or {r['expected'] for r in group}=={'endorse','reject'}
        modes[str(mode)]={'known_n':len(group),'minimum':minimum,'all_domains':covered,'both_labels_if_decisions':labels,
                          'all_base_replies_complete':complete,'usable':len(group)>=minimum and covered and labels and complete}
    return {'kind':kind,'known':known,'by_mode':modes,'usable':all(v['usable'] for v in modes.values()),
            'selection':'One fixed BASE-only task-value cohort; never selected on candidate/control results.'}


def compare(values: list[dict],base: list[dict],cohort: dict,kind: str) -> dict:
    a=indexed(base,kind);b=indexed(values,kind)
    if a.keys()!=b.keys() or reference_cohort(base,kind)!=cohort:raise ValueError('Changed reference mask/paired identities')
    fields=('thinking','family','prompt','expected')+(('operation','negated','irrelevant_note') if kind=='decisions' else ())
    if any(any(a[i][k]!=b[i][k] for k in fields) for i in a):raise ValueError('Paired confirmation request differs')
    known_ids={r['example_id'] for r in cohort['known']};by_mode={}
    for mode in (True,False):
        full=[r for r in values if r['thinking']==mode]
        selected=[r for r in full if r['example_id'] in known_ids]
        n=len(selected);correct=sum(r['value']['value_correct'] is True for r in selected)
        unknown=sum(r['value']['value_correct'] is None for r in selected)
        complete=all(r['native_assessment']['normal_stop'] and r['native_assessment']['response_boundaries_valid'] for r in full)
        strict=all(r['native_assessment']['strict_format'] for r in full)
        by_mode[str(mode)]={'full_n':128,'full_correct':sum(r['value']['value_correct'] is True for r in full),
            'full_wrong':sum(r['value']['value_correct'] is False for r in full),
            'full_unscorable':sum(r['value']['value_correct'] is None for r in full),
            'known_n':n,'known_correct':correct,'known_unscorable':unknown,
            'known_accuracy':correct/n if n and not unknown else None,
            'known_missing_bounds':[correct/n,(correct+unknown)/n] if n else None,
            'all_complete':complete,'all_native_strict':strict,
            'known_losses':[r['example_id'] for r in selected if r['value']['value_correct'] is False],
            'known_unscorable_ids':[r['example_id'] for r in selected if r['value']['value_correct'] is None],
            'full_gains':[r['example_id'] for r in full if r['value']['value_correct'] is True and a[r['example_id']]['value']['value_correct'] is not True],
            'full_losses':[r['example_id'] for r in full if r['value']['value_correct'] is False and a[r['example_id']]['value']['value_correct'] is True],
            'passed':cohort['by_mode'][str(mode)]['usable'] and n>0 and correct*100>=95*n and complete and (kind!='decisions' or strict)}
    return {'kind':kind,'by_mode':by_mode,'passed':all(v['passed'] for v in by_mode.values()),
            'criteria':'Frozen pooled independent plan:>=95%BASE-known each mode, complete replies, decision exact finals. Missing values remain explicit; correctness lower bound used for gate. Native formatting reported separately.'}
