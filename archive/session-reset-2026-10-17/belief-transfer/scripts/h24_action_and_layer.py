"""H24 items 2 and 3: the ACTION suite's per-item dispersion, and the core/assessment
layer split. Registered in H24 as where the discriminating power sits, given that the
dispersion result itself is anticipated by Grosse et al."""
import json, sys, math, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
R='data/results/factory_farming'
def logit(p,eps=1e-6):
    p=min(max(p,eps),1-eps); return math.log(p/(1-p))

def load(run, suite, tf):
    rows=[json.loads(l) for l in open(f'{R}/{run}/{suite}_responses.jsonl')]
    sel=lambda c:[r for r in rows if r['condition']==c]
    per={c:S.per_item(sel(c)) for c in ('base','me_plus','me_minus','m0_plus','m0_minus')}
    ids=sorted(set.intersection(*(set(v) for v in per.values())))
    meta={r['item_id']:r for r in rows}
    N={i:(tf(per['me_plus'][i])-tf(per['me_minus'][i]))-(tf(per['m0_plus'][i])-tf(per['m0_minus'][i])) for i in ids}
    return ids,N,meta

def rd(ids,d):
    if not ids: return (float('nan'),)*3
    m=st.fmean(d[i] for i in ids); sd=st.pstdev([d[i] for i in ids])
    return m, sd, (sd/abs(m) if m else float('inf'))

for scale,tf in [('probability',lambda p:p),('log-odds 1e-6',logit)]:
    print(f'\n########## {scale}')
    print('--- item 2: ACTION suite per-item dispersion (explicit corpus)')
    print(f"{'case':14s}{'model':6s}{'mean dA':>10}{'SD':>9}{'rel.disp':>10}{'n':>5}")
    for label,r4,r8 in [('s42','h8_4b','h8_8b'),('s7','h8_4b_s7','h8_8b_s7')]:
        for mdl,run in (('4B',r4),('8B',r8)):
            ids,N,_=load(run,'action',tf); m,sd,r=rd(ids,N)
            print(f'{label if mdl=="4B" else "":14s}{mdl:6s}{m:+10.4f}{sd:9.4f}{r:10.2f}{len(ids):5d}')
    print('--- item 3: BELIEF core vs assessment layer (explicit corpus)')
    print(f"{'case':10s}{'model':6s}{'core mean':>11}{'core rd':>9}{'assess mean':>13}{'assess rd':>11}{'ratio a/c':>11}")
    for label,r4,r8 in [('s42','h8_4b','h8_8b'),('s7','h8_4b_s7','h8_8b_s7')]:
        for mdl,run in (('4B',r4),('8B',r8)):
            ids,N,meta=load(run,'belief',tf)
            co=[i for i in ids if meta[i]['layer']=='core']; asr=[i for i in ids if meta[i]['layer']=='assessment']
            mc,_,rc=rd(co,N); ma,_,ra=rd(asr,N)
            print(f'{label if mdl=="4B" else "":10s}{mdl:6s}{mc:+11.4f}{rc:9.2f}{ma:+13.4f}{ra:11.2f}{ma/mc:11.2f}')
