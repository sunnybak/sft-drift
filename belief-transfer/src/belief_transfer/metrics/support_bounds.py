"""Full-grid missing-response identification bounds, never imputed point estimates."""
from __future__ import annotations

def support_bounds(rows:list[dict])->dict:
    if not rows:raise ValueError('An explicit nonempty expected grid is required')
    if any(r.get('polarity') not in ['positive','negative'] for r in rows):raise ValueError('Unknown polarity')
    valid=[r for r in rows if not r.get('error') and r.get('answer') in ['agree','disagree']]
    n=len(rows);missing=n-len(valid)
    supported=sum(r['answer']==('agree' if r['polarity']=='positive' else 'disagree') for r in valid)
    low=supported/n;high=(supported+missing)/n
    return {'expected':n,'valid':len(valid),'missing':missing,'known_support':supported,
            'value':low if missing==0 else None,'lower':low,'upper':high,
            'bound_kind':'missing_response_identification','complete':missing==0}
