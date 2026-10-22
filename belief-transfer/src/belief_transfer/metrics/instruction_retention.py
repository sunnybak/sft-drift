"""Frozen retention counts; standard library only, no new known-item selection."""
from __future__ import annotations
from collections import Counter
FAMILIES = ('sum', 'difference', 'product', 'comparison', 'negated_equality', 'sort', 'uppercase', 'progression')

def report(rows: list[dict],bank: list[dict],known: list[dict]|None=None) -> tuple[dict,list[dict]]:
    if len(bank)!=128:raise ValueError('Require all128retention presentations')
    if Counter(r['example_id'] for r in rows)!=Counter(r['example_id'] for r in bank):raise ValueError('Retention coverage mismatch')
    expected={r['example_id']:r for r in bank}
    if any(any(r[k]!=v for k,v in expected[r['example_id']].items()) for r in rows):raise ValueError('Retention bank identity mismatch')
    if known is None:
        known=[{k:r[k] for k in ['example_id','family','thinking','response_sha256']}
            for r in rows if all(r['assessment'][k] for k in ['semantic_correct','strict_format','response_boundaries_valid','normal_stop'])]
    ids=[r['example_id'] for r in known]
    if len(set(ids))!=len(ids) or not set(ids)<=expected.keys():raise ValueError('Invalid known item identity')
    known_meta={r['example_id']:r for r in known}
    if any(any(v!=expected[k][field] for field,v in meta.items() if field in ['family','thinking']) for k,meta in known_meta.items()):
        raise ValueError('Known mask family/mode changed')
    modes={}
    for mode in (True,False):
        full=[r for r in rows if r['thinking']==mode];eligible=[r for r in full if r['example_id'] in known_meta]
        keys=['semantic_correct','strict_format','response_boundaries_valid','normal_stop']
        full_counts={k:sum(r['assessment'][k] for r in full) for k in keys}
        known_counts={k:sum(r['assessment'][k] for r in eligible) for k in keys}
        sufficient=len(eligible)>=32 and {r['family'] for r in eligible}==set(FAMILIES)
        modes[str(mode)]={'full_n':len(full),'full':full_counts,'known_n':len(eligible),'known':known_counts,
            'reference_sufficient':sufficient,'known_passed':bool(sufficient and known_counts['semantic_correct']/len(eligible)>=.95
                and all(known_counts[k]==len(eligible) for k in keys[1:]))}
    backend_errors=sum(bool(r.get('generation_metadata',{}).get('backend_error')) for r in rows)
    return {'by_mode':modes,'backend_errors':backend_errors,'reference_usable':backend_errors==0 and all(r['reference_sufficient'] for r in modes.values()),
            'known_retention_passed':backend_errors==0 and all(r['known_passed'] for r in modes.values()),'n_all':len(rows)},known

