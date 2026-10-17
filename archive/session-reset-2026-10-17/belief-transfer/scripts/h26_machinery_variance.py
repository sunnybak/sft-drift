"""H26 falsifier: is the off-topic control's machinery term seed-unstable in general, or is
m0_multiform_s123 a one-off outlier?

Measured on control pairs NOT used to generate the claim (the sw_arms_v1 family is excluded).
Machinery = (m0+ - m0-), paired per item, with a bootstrap CI, on both scales.
"""
import json, sys, math, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
from belief_transfer.metrics import bootstrap_ci
def logit(p,e=1e-6):
    p=min(max(p,e),1-e); return math.log(p/(1-p))

# (family, {seed: (experiment, run_id)}) -- runs whose responses carry m0_plus/m0_minus
FAMILIES = {
 'h8_4b   (explicit, 4B)': {42:('factory_farming','h8_4b'), 7:('factory_farming','h8_4b_s7')},
 'h8_8b   (explicit, 8B)': {42:('factory_farming','h8_8b'), 7:('factory_farming','h8_8b_s7')},
 'h19_full_ft (full-FT)':  {42:('factory_farming','h19_full_ft'), 7:('factory_farming','h19_full_ft_s7')},
}
R='data/results'
def machinery(exp,run,suite,tf):
    try: rows=[json.loads(l) for l in open(f'{R}/{exp}/{run}/{suite}_responses.jsonl')]
    except FileNotFoundError: return None
    sel=lambda c:[r for r in rows if r['condition']==c]
    if not sel('m0_plus'): return None
    a,b=S.per_item(sel('m0_plus')),S.per_item(sel('m0_minus'))
    ids=sorted(set(a)&set(b))
    v=[tf(a[i])-tf(b[i]) for i in ids]
    lo,hi=bootstrap_ci(v)
    return st.fmean(v),lo,hi,len(v)

for scale,tf in (('probability',lambda p:p),('log-odds 1e-6',logit)):
    print(f'\n########## {scale}')
    for suite in ('belief','action'):
        print(f'  --- {suite} suite')
        for fam,seeds in FAMILIES.items():
            vals={}
            for s,(exp,run) in seeds.items():
                m=machinery(exp,run,suite,tf)
                if m: vals[s]=m
            if len(vals)<2: continue
            # NOT a ratio: machinery values are small and some straddle zero, so a
            # ratio-of-small-numbers is the same pathology diagnosed in H23/H24 today.
            # The unambiguous statistic is whether the two seeds' CIs OVERLAP.
            vv=[v for _,v in sorted(vals.items())]
            overlap = not (vv[0][2] < vv[1][1] or vv[1][2] < vv[0][1])
            cells=' | '.join(f's{s} {v[0]:+.4f} [{v[1]:+.4f},{v[2]:+.4f}]' for s,v in sorted(vals.items()))
            print(f'    {fam:24s} {cells}   {"CIs overlap -> consistent" if overlap else "CIs DISJOINT -> seeds genuinely differ"}')
print('\n  reference (the GENERATING observation, excluded from the test):')
print('    m0_multiform belief log-odds  s42 +0.0916 | s7 +0.0856 | s123 +0.1917   ratio 2.24x')
