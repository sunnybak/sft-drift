"""H25's registered test, read on the expanded suite (sw_evalgen_v3, null facet n=28).

Estimator copied from scripts/h23_halo_ratio.py (the registered null/ALL form plus the
cleaner null/non-null) so the numbers are comparable to the v1-suite reads that opened
this thread. Branches are H25's "What would falsify it"; three seeds now exist.
Also reads: the positive-control check (recovery_time vs null, per h25_positive_control)
and the new suite's sensitivity (rule 4).
"""
import json, sys, random, statistics
sys.path.insert(0, 'src')
from belief_transfer.evals import suite as S

R='data/results/software_architecture'; NULLF='request_volume'
B=10000; random.seed(20260822)

def netted_items(run):
    rows=[json.loads(l) for l in open(f'{R}/{run}/inference_responses.jsonl')]
    sel=lambda c:[r for r in rows if r['condition']==c]
    a,b=S.per_item(sel('m_plus')),S.per_item(sel('m_minus'))
    c,d=S.per_item(sel('m0_plus')),S.per_item(sel('m0_minus'))
    ids=sorted(set(a)&set(b)&set(c)&set(d))
    facet={r['item_id']:r['facet'] for r in rows}
    return [(i,facet[i],(a[i]-b[i])-(c[i]-d[i])) for i in ids]

for run,seed in (("sw_inf_v2","s42"),("sw_inf_v2_s7","s7"),("sw_inf_v2_s123","s123")):
    items=netted_items(run)
    nnull=sum(1 for _,f,_ in items if f==NULLF)
    def calc(sample):
        allv=[v for _,_,v in sample]; nul=[v for _,f,v in sample if f==NULLF]
        if not nul or statistics.fmean(allv)==0: return None
        return statistics.fmean(nul)/statistics.fmean(allv)
    pt=calc(items)
    draws=sorted(c for _ in range(B) if (c:=calc([random.choice(items) for _ in items])) is not None)
    lo,hi=draws[int(.025*len(draws))],draws[int(.975*len(draws))]
    sep = "SEPARATES 0 from 1" if (lo>0 and hi<1) or (lo>1) or (hi<0) else "spans both ends" if lo<0 and hi>1 else ("excludes 0" if lo>0 else "excludes 1" if hi<1 else "?")
    # branch bookkeeping
    print(f"{seed}: n_null={nnull}, n_all={len(items)}  halo null/ALL {pt:5.2f}x  [{lo:5.2f}, {hi:5.2f}]  -> {sep}")
    # all-facet netted dI and per-facet vs null (positive-control check)
    allv=[v for _,_,v in items]
    from belief_transfer.metrics import bootstrap_ci
    alo,ahi=bootstrap_ci(allv)
    print(f"     all-facet netted dI {statistics.fmean(allv):+.4f} [{alo:+.4f}, {ahi:+.4f}]")
    byf={}
    for _,f,v in items: byf.setdefault(f,[]).append(v)
    rank=sorted(byf, key=lambda f:-statistics.fmean(byf[f]))
    nulmean=statistics.fmean(byf[NULLF])
    rt=byf.get('recovery_time',[])
    # recovery_time minus null, paired bootstrap over items (unpaired facets -> two-sample bootstrap)
    diffs=sorted(statistics.fmean(random.choices(rt,k=len(rt)))-statistics.fmean(random.choices(byf[NULLF],k=len(byf[NULLF]))) for _ in range(B))
    dlo,dhi=diffs[int(.025*B)],diffs[int(.975*B)]
    print(f"     null rank {rank.index(NULLF)+1}/8 ({nulmean:+.4f});  recovery_time rank {rank.index('recovery_time')+1}/8, minus null {statistics.fmean(rt)-nulmean:+.4f} [{dlo:+.4f}, {dhi:+.4f}]\n")
