"""How many null-facet items would it take to MEASURE the halo ratio?

The ratio scale, stated because H3/H23 read it backwards:
  0.0 = null facet clean (all of dI is premise-specific)
  1.0 = null facet moves as much as the average facet (NO premise-specific signal)
So the question the suite must answer is "is the ratio nearer 0 or nearer 1", and the
current CIs contain BOTH. Simulate wider null facets by resampling the observed per-item
null distribution, holding the all-facet denominator fixed at its observed value.
"""
import json, sys, random, statistics
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
R='data/results'; NULL={'factory_farming':'labor_productivity','software_architecture':'request_volume'}
random.seed(20260821); B=4000

def per_item_netted(exp,run,plus,minus):
    rows=[json.loads(l) for l in open(f'{R}/{exp}/{run}/inference_responses.jsonl')]
    sel=lambda c:[r for r in rows if r['condition']==c]
    a,b,c,d=(S.per_item(sel(x)) for x in (plus,minus,'m0_plus','m0_minus'))
    facet={r['item_id']:r['facet'] for r in rows}
    ids=sorted(set(a)&set(b)&set(c)&set(d))
    nul=[(a[i]-b[i])-(c[i]-d[i]) for i in ids if facet[i]==NULL[exp]]
    allv=[(a[i]-b[i])-(c[i]-d[i]) for i in ids]
    return nul, statistics.fmean(allv)

for label,args in [('sw EVIDENCE s42',('software_architecture','sw_arms_v1','m_plus','m_minus')),
                   ('sw EVIDENCE s7', ('software_architecture','sw_arms_v1_s7','m_plus','m_minus'))]:
    nul,den=per_item_netted(*args)
    print(f'{label}: observed n={len(nul)} null items, all-facet denominator {den:+.4f}')
    for n in (6,12,24,48,96):
        draws=sorted(statistics.fmean([random.choice(nul) for _ in range(n)])/den for _ in range(B))
        lo,hi=draws[int(.025*B)],draws[int(.975*B)]
        verdict = 'separates 0 from 1' if (hi<1.0 or lo>1.0) or (hi<0.5 and lo>0.0) else 'still contains both'
        print(f'   n={n:3d} null items -> ratio CI [{lo:5.2f}, {hi:5.2f}]  width {hi-lo:4.2f}   {verdict}')
    print()
