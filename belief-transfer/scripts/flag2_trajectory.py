"""LITERATURE.md flag 2: "slow, not inert?"

The Knowing-Using Gap paper (Dai et al., arXiv:2607.08393) shows generalization can emerge
4-6 epochs AFTER memorization saturates. Our long-sparse ("article") cell's dB is read at a
fixed step, so a reviewer can say the effect is SLOW rather than ABSENT. The pre-emption is
the trajectory: if the article cell's netted belief line is FLAT across every gated step
while the short cell's RISES, "slow" is ruled out on our own data.

Free -- reads trajectory.jsonl already on disk. Gate is enforced per step per arm:
AGENTS.md records that m0_plus fails choice_bench at the late steps, so the clean netting
region is 12-36 and 48/60 must be dropped rather than reported.
"""
import json, sys
from collections import defaultdict
R='data/results/factory_farming'
CELLS=[('article  (long-sparse, matrix_v1)','matrix_v1','m_plus','m_minus'),
       ('short    (premise_short, ms_arms)','ms_arms','m_plus','m_minus'),
       ('EXPLICIT (positive control, matrix_v1)','matrix_v1','me_plus','me_minus')]

def load(run):
    rows=[json.loads(l) for l in open(f'{R}/{run}/trajectory.jsonl')]
    sc=defaultdict(dict); gate=defaultdict(dict)
    for r in rows:
        if r['eval_type']=='belief' and r['metric']=='score': sc[r['step']][r['condition']]=r['score']
        if r['eval_type']=='choice' and r['metric']=='passed': gate[r['step']][r['condition']]=bool(r['score'])
    return sc,gate

print(f"{'cell':40s}{'step':>6}{'netted dB':>12}{'gate':>26}")
series={}
for label,run,pp,mm in CELLS:
    sc,gate=load(run); pts=[]
    for step in sorted(sc):
        need=[pp,mm,'m0_plus','m0_minus']
        if not all(c in sc[step] for c in need): continue
        bad=[c for c in need if gate[step].get(c) is False]
        net=(sc[step][pp]-sc[step][mm])-(sc[step]['m0_plus']-sc[step]['m0_minus'])
        tag='ALL PASS' if not bad else 'FAILS: '+','.join(bad)
        print(f"{label if step==sorted(sc)[0] else '':40s}{step:>6}{net:>12.4f}{tag:>26}")
        if not bad: pts.append((step,net))
    series[label]=pts
    print()

print('CLEAN REGION ONLY (every arm gated at that step):')
for label,pts in series.items():
    if not pts: print(f'  {label:40s} no clean steps'); continue
    vals=[v for _,v in pts]
    rng=max(vals)-min(vals)
    trend=vals[-1]-vals[0]
    print(f'  {label:40s} steps {[s for s,_ in pts]}  dB {[round(v,4) for v in vals]}')
    print(f'  {"":40s} range {rng:+.4f}   first->last {trend:+.4f}')
