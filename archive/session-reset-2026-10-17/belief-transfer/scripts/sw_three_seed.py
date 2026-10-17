"""The three-seed read of software_architecture, against the falsifiers registered in
configs/run/sw_arms_v1_s123.yaml BEFORE seed 123 was trained.

  1. halo ratio (null-facet netted / all-facet netted): stable quantity, or not?
  2. recovery_time: still the top-ranked facet? -> the project's only surviving dI
  3. belief dB on log-odds: third value inside [+0.09,+0.15] earns a band
"""
import json, sys, math, random, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
from belief_transfer.metrics import bootstrap_ci
R='data/results/software_architecture'; NULL='request_volume'
RUNS=[('s42','sw_arms_v1'),('s7','sw_arms_v1_s7'),('s123','sw_arms_v1_s123')]
LOGIT_EPS=1e-6
def logit(p):
    p=min(max(p,LOGIT_EPS),1-LOGIT_EPS); return math.log(p/(1-p))

def netted(run, suite, facet=None, tf=lambda p:p):
    try: rows=[json.loads(l) for l in open(f'{R}/{run}/{suite}_responses.jsonl')]
    except FileNotFoundError: return None
    sel=lambda c:[r for r in rows if r['condition']==c and (facet is None or r['facet']==facet)]
    if not sel('m_plus'): return None
    a,b,c,d=(S.per_item(sel(x)) for x in ('m_plus','m_minus','m0_plus','m0_minus'))
    ids=sorted(set(a)&set(b)&set(c)&set(d))
    v=[(tf(a[i])-tf(b[i]))-(tf(c[i])-tf(d[i])) for i in ids]
    lo,hi=bootstrap_ci(v)
    return {'d':st.fmean(v),'lo':lo,'hi':hi,'n':len(v),'excl':lo>0 or hi<0,'per':v}

def gate(run):
    try: y=open(f'{R}/{run}/choice_bench.yaml').read()
    except FileNotFoundError: return 'no gate file'
    return f"{y.count('passed: true')} pass / {y.count('passed: false')} fail"

print('GATE (choice_bench)');  [print(f'  {s:5s} {r:18s} {gate(r)}') for s,r in RUNS]

print('\n1. HALO RATIO  -- kill if s123 outside [0.4,1.3] or the three span >2x')
ratios=[]
for s,r in RUNS:
    allf,nul=netted(r,'inference'),netted(r,'inference',NULL)
    if not allf: print(f'  {s:5s} (not run)'); continue
    random.seed(20260821)
    draws=sorted(st.fmean(random.choices(nul['per'],k=len(nul['per'])))/st.fmean(random.choices(allf['per'],k=len(allf['per']))) for _ in range(4000))
    rat=nul['d']/allf['d']; ratios.append(rat)
    print(f"  {s:5s} all {allf['d']:+.4f}  null {nul['d']:+.4f}  ratio {rat:5.2f}x  "
          f"[{draws[100]:6.2f},{draws[3900]:6.2f}]")
if len(ratios)==3:
    span=max(ratios)/min(ratios) if min(ratios)>0 else float('inf')
    inband=0.4<=ratios[2]<=1.3
    print(f'  -> s123 in [0.4,1.3]? {inband}   span {span:.2f}x   '
          f'VERDICT: {"quantity holds" if inband and span<=2 else "NOT A STABLE QUANTITY -- do not fund the expansion"}')

print('\n2. recovery_time  -- dies if not top-ranked or sign flips')
for s,r in RUNS:
    rows=netted(r,'inference')
    if not rows: print(f'  {s:5s} (not run)'); continue
    raw=[json.loads(l) for l in open(f'{R}/{r}/inference_responses.jsonl')]
    facets=sorted(set(x['facet'] for x in raw))
    scored=sorted(((netted(r,'inference',f)['d'],f) for f in facets), reverse=True)
    rank=[f for _,f in scored].index('recovery_time')+1
    rt=netted(r,'inference','recovery_time')
    print(f"  {s:5s} recovery_time {rt['d']:+.4f} [{rt['lo']:+.4f},{rt['hi']:+.4f}]  "
          f"RANK {rank}/{len(facets)}  (null facet {netted(r,'inference',NULL)['d']:+.4f})")

print('\n3. BELIEF dB log-odds  -- band if s123 inside [+0.09,+0.15]')
for s,r in RUNS:
    b=netted(r,'belief',tf=logit)
    if not b: print(f'  {s:5s} (not run)'); continue
    p=netted(r,'belief')
    print(f"  {s:5s} log-odds {b['d']:+.4f} [{b['lo']:+.4f},{b['hi']:+.4f}] {'EXCL' if b['excl'] else 'strad'}"
          f"   probability {p['d']:+.4f} {'EXCL' if p['excl'] else 'strad'}")
