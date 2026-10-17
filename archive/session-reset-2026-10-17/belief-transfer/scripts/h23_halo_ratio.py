"""Bootstrap CI on the HALO RATIO itself. The ratio's denominator is a small netted
number, so a point estimate is not enough to invert a shelving decision on."""
import json, sys, random, statistics
sys.path.insert(0, 'src')
from belief_transfer.evals import suite as S

R='data/results'; NULL={'factory_farming':'labor_productivity','software_architecture':'request_volume'}
B=10000; random.seed(20260821)

def netted_per_item(rows, plus, minus):
    sel=lambda c:[r for r in rows if r['condition']==c]
    a,b=S.per_item(sel(plus)),S.per_item(sel(minus))
    c,d=S.per_item(sel('m0_plus')),S.per_item(sel('m0_minus'))
    ids=sorted(set(a)&set(b)&set(c)&set(d))
    facet={r['item_id']:r['facet'] for r in rows}
    return [(i, facet[i], (a[i]-b[i])-(c[i]-d[i])) for i in ids]

def ratios(exp, run, plus, minus, label):
    rows=[json.loads(l) for l in open(f'{R}/{exp}/{run}/inference_responses.jsonl')]
    nf=NULL[exp]; items=netted_per_item(rows, plus, minus)
    def calc(sample):
        allv=[v for _,_,v in sample]
        nul=[v for _,f,v in sample if f==nf]
        non=[v for _,f,v in sample if f!=nf]
        if not nul or not non or statistics.fmean(allv)==0 or statistics.fmean(non)==0: return None
        return statistics.fmean(nul)/statistics.fmean(allv), statistics.fmean(nul)/statistics.fmean(non)
    pt=calc(items)
    draws=[c for _ in range(B) if (c:=calc([random.choice(items) for _ in items]))]
    for k,name in ((0,'null/ALL  (registered)'),(1,'null/non-null (cleaner)')):
        v=sorted(d[k] for d in draws)
        lo,hi=v[int(.025*len(v))],v[int(.975*len(v))]
        print(f"{label:34s} {name:24s} {pt[k]:6.2f}x  [{lo:7.2f}, {hi:7.2f}]  "
              f"({100*sum(1 for x in v if x>2)/len(v):4.1f}% of draws > 2x)")
    print()

ratios('factory_farming','inference_v1_step24','m_plus','m_minus','ff EVIDENCE (s42)')
ratios('factory_farming','inference_v1_step24','me_plus','me_minus','ff EXPLICIT (s42)')
ratios('software_architecture','sw_arms_v1','m_plus','m_minus','sw EVIDENCE (s42)')
ratios('software_architecture','sw_arms_v1_s7','m_plus','m_minus','sw EVIDENCE (s7)')
