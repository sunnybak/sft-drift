"""Is `recovery_time` -- now the project's ONLY surviving dI signal -- an instrument
artifact? Runs the two validity checks AGENTS.md requires (D4 presentation-order gap,
D7 forward/reverse acquiescence) on that facet specifically, plus a leave-one-out, before
H25's registered falsifier is paid for."""
import json, sys, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
from belief_transfer.evals.belief import acquiescence
from belief_transfer.metrics import bootstrap_ci
R='data/results/software_architecture'
ARMS=('base','m_plus','m_minus','m0_plus','m0_minus')  # base FIRST: D7 says read
# arm acquiescence as a SHIFT FROM THAT ARM'S OWN BASE, not as an absolute level.

for run in ('sw_arms_v1','sw_arms_v1_s7'):
    rows=[json.loads(l) for l in open(f'{R}/{run}/inference_responses.jsonl')]
    print(f'\n===== {run}')
    for facet in ('recovery_time','request_volume'):
        print(f'  --- {facet}')
        for arm in ARMS:
            sub=[r for r in rows if r['condition']==arm and r['facet']==facet]
            vg=S.variant_gap(sub); acq=acquiescence(sub)
            acq_s = (f"{acq['mean']:+.3f} [{acq['ci95'][0]:+.3f},{acq['ci95'][1]:+.3f}] "
                     f"n={acq['n_pairs']}") if acq else 'no whole pair'
            print(f'      {arm:10s} D4 variant gap {vg:.4f}   D7 acquiescence {acq_s}')
        # leave-one-out on the netted contrast
        sel=lambda c:[r for r in rows if r['condition']==c and r['facet']==facet]
        a,b,c,d=(S.per_item(sel(x)) for x in ARMS[1:])
        ids=sorted(set(a)&set(b)&set(c)&set(d))
        net={i:(a[i]-b[i])-(c[i]-d[i]) for i in ids}
        full=st.fmean(net.values())
        loo=[(st.fmean([net[j] for j in ids if j!=i]), i) for i in ids]
        lo,hi=bootstrap_ci(list(net.values()))
        print(f'      netted {full:+.4f} [{lo:+.4f},{hi:+.4f}]  '
              f'leave-one-out range [{min(loo)[0]:+.4f}, {max(loo)[0]:+.4f}]  '
              f'{"ALL LOO SAME SIGN" if min(loo)[0]*max(loo)[0]>0 else "LOO FLIPS SIGN"}')
