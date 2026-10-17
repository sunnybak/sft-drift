"""H25 part 1, the free half: is the descriptive-inference suite's POSITIVE CONTROL intact?

AGENTS.md: "`Me+/-` states a stance *and* cites premises and absorbs heavily, so it should
move `dI`. If nothing moves `dI`, `Me+/-` included, the suite is not measuring anything and
no conclusion follows about the evidence arms."

The sharper question H25 asks: does any DIFFERING-premise facet move more than the
byte-identical NULL facet? If not, the suite has no premise-specific signal even on the arm
it is supposed to be most sensitive to.
"""
import json, sys, random, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
from belief_transfer.metrics import bootstrap_ci
R='data/results'
NULL={'factory_farming':'labor_productivity','software_architecture':'request_volume'}

def per_facet(exp, run, plus, minus, label):
    rows=[json.loads(l) for l in open(f'{R}/{exp}/{run}/inference_responses.jsonl')]
    sel=lambda c:[r for r in rows if r['condition']==c]
    a,b,c,d=(S.per_item(sel(x)) for x in (plus,minus,'m0_plus','m0_minus'))
    facet={r['item_id']:r['facet'] for r in rows}
    ids=sorted(set(a)&set(b)&set(c)&set(d))
    net={i:(a[i]-b[i])-(c[i]-d[i]) for i in ids}
    nf=NULL[exp]; nul=[net[i] for i in ids if facet[i]==nf]
    print(f'\n=== {label}   (null facet = {nf}, n={len(nul)})')
    print(f"{'facet':24s}{'dI netted':>11}{'95% CI':>22}{'n':>4}   vs null facet")
    rank=[]
    for f in sorted(set(facet[i] for i in ids)):
        v=[net[i] for i in ids if facet[i]==f]
        lo,hi=bootstrap_ci(v); m=st.fmean(v)
        if f!=nf:
            random.seed(20260821)
            diffs=sorted(st.fmean([random.choice(v) for _ in v])-st.fmean([random.choice(nul) for _ in nul]) for _ in range(4000))
            dlo,dhi=diffs[100],diffs[3900]
            verdict=f'{m-st.fmean(nul):+.4f} [{dlo:+.4f},{dhi:+.4f}]'+(' EXCEEDS' if dlo>0 else '')
            rank.append((m,f))
        else:
            verdict='-- NULL CONTROL --'
        print(f'{f:24s}{m:+11.4f}   [{lo:+.4f},{hi:+.4f}]{len(v):4d}   {verdict}')
    print(f'  all-facet {st.fmean(net[i] for i in ids):+.4f} | null {st.fmean(nul):+.4f} | '
          f'best differing facet: {max(rank)[1]} {max(rank)[0]:+.4f}')

per_facet('factory_farming','inference_v1_step24','me_plus','me_minus','factory_farming EXPLICIT (the POSITIVE CONTROL)')
per_facet('factory_farming','inference_v1_step24','m_plus','m_minus','factory_farming EVIDENCE')
per_facet('software_architecture','sw_arms_v1','m_plus','m_minus','software_architecture EVIDENCE s42')
per_facet('software_architecture','sw_arms_v1_s7','m_plus','m_minus','software_architecture EVIDENCE s7')

# --- Does premise CONTRAST MAGNITUDE predict which facets show inference?
# Facet -> the spec fact it is generated from, contrast ratio computed from the spec.
SW_CONTRAST = {  # software_architecture, from configs/experiment/software_architecture.yaml
    'incident_frequency': 8.8, 'recovery_time': 16.9, 'lead_time': 17.0,
    'deploy_frequency': 23.3, 'cost_position': 3.8, 'onboarding_speed': 7.9,
    'feature_focus': 2.5,
}
def spearman(pairs):
    xs=[p[0] for p in pairs]; ys=[p[1] for p in pairs]; n=len(pairs)
    rk=lambda v:{x:i for i,x in enumerate(sorted(v))}
    rx,ry=rk(xs),rk(ys)
    return 1-6*sum((rx[x]-ry[y])**2 for x,y in pairs)/(n*(n*n-1))

print('\n=== does premise contrast magnitude predict per-facet dI? (software_architecture)')
for run in ('sw_arms_v1','sw_arms_v1_s7'):
    rows=[json.loads(l) for l in open(f'{R}/software_architecture/{run}/inference_responses.jsonl')]
    sel=lambda c:[r for r in rows if r['condition']==c]
    a,b,c,d=(S.per_item(sel(x)) for x in ('m_plus','m_minus','m0_plus','m0_minus'))
    facet={r['item_id']:r['facet'] for r in rows}
    ids=sorted(set(a)&set(b)&set(c)&set(d))
    net={i:(a[i]-b[i])-(c[i]-d[i]) for i in ids}
    pairs=[(SW_CONTRAST[f], st.fmean([net[i] for i in ids if facet[i]==f])) for f in SW_CONTRAST]
    print(f'  {run:16s} Spearman rho = {spearman(pairs):+.3f}  (n=7 facets)')
