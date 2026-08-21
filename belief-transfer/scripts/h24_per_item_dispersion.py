"""H24 falsifier: is 8B's per-item belief shift TIGHTER than 4B's despite being smaller?

Registered quantities (hypotheses/open/H24, `What would falsify it`):
  (a) relative dispersion  SD(dB_i)/|mean(dB_i)|   -- lower = more uniform
  (b) per-item sign agreement with the arm's own direction (mean-free)
  (c) cross-seed per-item rank correlation of the TREATMENT contrast (no control)
  (d) all of the above after regressing out per-item base log-odds
  + the control pair's own per-item dispersion as the NOISE FLOOR
  + two clamp conventions (1e-6 registered, 1e-2 the known-sensitive alternative)
"""
import json, sys, math, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
R='data/results/factory_farming'

def logit(p, eps):
    p=min(max(p,eps),1-eps); return math.log(p/(1-p))

def items(run, tf):
    rows=[json.loads(l) for l in open(f'{R}/{run}/belief_responses.jsonl')]
    sel=lambda c:[r for r in rows if r['condition']==c]
    per={c:S.per_item(sel(c)) for c in ('base','me_plus','me_minus','m0_plus','m0_minus')}
    ids=sorted(set.intersection(*(set(v) for v in per.values())))
    T={i: tf(per['me_plus'][i])-tf(per['me_minus'][i]) for i in ids}      # treatment contrast
    C={i: tf(per['m0_plus'][i])-tf(per['m0_minus'][i]) for i in ids}      # control contrast
    N={i: T[i]-C[i] for i in ids}                                        # netted per-item dB
    B={i: tf(per['base'][i]) for i in ids}
    return ids,T,C,N,B

def resid(ids, y, x):
    mx,my=st.fmean(x[i] for i in ids), st.fmean(y[i] for i in ids)
    sxx=sum((x[i]-mx)**2 for i in ids)
    b=(sum((x[i]-mx)*(y[i]-my) for i in ids)/sxx) if sxx else 0.0
    return {i: y[i]-(my+b*(x[i]-mx))+my for i in ids}   # keep the mean, remove base slope

def stats(ids, d):
    m=st.fmean(d[i] for i in ids); sd=st.pstdev([d[i] for i in ids])
    agree=sum(1 for i in ids if (d[i]>0)==(m>0))/len(ids)
    return m, sd, (sd/abs(m) if m else float('inf')), agree

def spearman(ids,a,b):
    rk=lambda d:{i:r for r,i in enumerate(sorted(ids,key=lambda k:d[k]))}
    ra,rb=rk(a),rk(b); n=len(ids)
    return 1-6*sum((ra[i]-rb[i])**2 for i in ids)/(n*(n*n-1))

CASES=[('EXPLICIT s42','h8_4b','h8_8b'),('EXPLICIT s7','h8_4b_s7','h8_8b_s7'),
       ('EVIDENCE s42','h8_4b_ev','h8_8b_ev')]

for scale,tf in [('probability',lambda p:p),('log-odds eps=1e-6',lambda p:logit(p,1e-6)),
                 ('log-odds eps=1e-2',lambda p:logit(p,1e-2))]:
    print(f'\n########## {scale}')
    print(f"{'case':14s}{'model':6s}{'mean dB':>9}{'SD':>8}{'rel.disp':>10}{'sign agr':>10}"
          f"{'ctrl SD':>9}{'(d) rel.disp':>13}{'(d) agr':>9}")
    for label,r4,r8 in CASES:
        for mdl,run in (('4B',r4),('8B',r8)):
            ids,T,C,N,B=items(run,tf)
            m,sd,rd,ag=stats(ids,N)
            _,csd,_,_=stats(ids,C)
            _,_,rd2,ag2=stats(ids,resid(ids,N,B))
            print(f'{label if mdl=="4B" else "":14s}{mdl:6s}{m:+9.4f}{sd:8.4f}{rd:10.2f}'
                  f'{ag:10.2f}{csd:9.4f}{rd2:13.2f}{ag2:9.2f}')
    # (c) cross-seed per-item rank correlation of the TREATMENT contrast
    print('  (c) cross-seed per-item Spearman of (me+ - me-), explicit corpus, no control:')
    for mdl,a,b in (('4B','h8_4b','h8_4b_s7'),('8B','h8_8b','h8_8b_s7')):
        ids,T1,*_=items(a,tf); _,T2,*_=items(b,tf)
        print(f'        {mdl}  rho = {spearman(ids,T1,T2):+.3f}   (n={len(ids)} items)')
