"""H26 part 2, the second registered branch:
  "FALSIFIED if machinery does not track netted instability -- if arms whose
   machinery-to-raw ratio is large replicate across seeds just as well as arms where it is
   small, the predictive half of the claim is dead even if the variance is real."

For each arm family with >=2 seeds: raw (m+ - m-), machinery (m0+ - m0-), netted, per seed.
Then: does machinery/|raw| order the families by how well netted replicates?
"""
import json, sys, math, statistics as st
sys.path.insert(0,'src')
from belief_transfer.evals import suite as S
def logit(p,e=1e-6):
    p=min(max(p,e),1-e); return math.log(p/(1-p))
R='data/results'

FAM = {
 'sw_arms_v1 (GENERATING)': ('m_plus','m_minus',
    {42:('software_architecture','sw_arms_v1'),7:('software_architecture','sw_arms_v1_s7'),
     123:('software_architecture','sw_arms_v1_s123')}),
 'h8_4b explicit':  ('me_plus','me_minus',{42:('factory_farming','h8_4b'),7:('factory_farming','h8_4b_s7')}),
 'h8_8b explicit':  ('me_plus','me_minus',{42:('factory_farming','h8_8b'),7:('factory_farming','h8_8b_s7')}),
 'h19_full_ft':     ('m_plus','m_minus',{42:('factory_farming','h19_full_ft'),7:('factory_farming','h19_full_ft_s7')}),
}
print(f"{'family':26s}{'seed':>6}{'raw':>10}{'machinery':>11}{'netted':>10}{'mach/|raw|':>12}")
summary={}
for fam,(pp,mm,seeds) in FAM.items():
    rows_out=[]
    for s,(exp,run) in sorted(seeds.items()):
        try: rows=[json.loads(l) for l in open(f'{R}/{exp}/{run}/belief_responses.jsonl')]
        except FileNotFoundError: continue
        sel=lambda c:[r for r in rows if r['condition']==c]
        if not sel(pp) or not sel('m0_plus'): continue
        a,b,c,d=(S.per_item(sel(x)) for x in (pp,mm,'m0_plus','m0_minus'))
        ids=sorted(set(a)&set(b)&set(c)&set(d))
        raw=st.fmean(logit(a[i])-logit(b[i]) for i in ids)
        mac=st.fmean(logit(c[i])-logit(d[i]) for i in ids)
        rows_out.append((s,raw,mac,raw-mac,abs(mac)/abs(raw) if raw else float('inf')))
    if len(rows_out)<2: continue
    for s,raw,mac,net,r in rows_out:
        print(f'{fam if s==rows_out[0][0] else "":26s}{s:>6}{raw:>10.4f}{mac:>11.4f}{net:>10.4f}{r:>12.2f}')
    nets=[x[3] for x in rows_out]; ratios=[x[4] for x in rows_out]
    # replication quality: spread of netted RELATIVE to its own mean, and whether sign holds
    inst = st.pstdev(nets)/abs(st.fmean(nets)) if st.fmean(nets) else float('inf')
    summary[fam]=(st.fmean(ratios), inst, len({n>0 for n in nets})==1)
    print(f'{"":26s}{"":6}{"":10}{"":11}  -> mean mach/|raw| {st.fmean(ratios):.2f}   '
          f'netted rel.spread {inst:.2f}   sign holds: {summary[fam][2]}\n')

print('ORDERING TEST -- does mach/|raw| track netted instability?')
for fam,(r,inst,ok) in sorted(summary.items(), key=lambda kv: kv[1][0]):
    print(f'  mach/|raw| {r:5.2f}   netted rel.spread {inst:5.2f}   sign holds {str(ok):5s}   {fam}')
xs=[v[0] for v in summary.values()]; ys=[v[1] for v in summary.values()]
if len(xs)>2:
    rk=lambda v:{x:i for i,x in enumerate(sorted(v))}
    rx,ry=rk(xs),rk(ys); n=len(xs)
    rho=1-6*sum((rx[x]-ry[y])**2 for x,y in zip(xs,ys))/(n*(n*n-1))
    print(f'\n  Spearman(mach/|raw|, netted instability) = {rho:+.3f}  over n={n} families '
          f'-- far too few to be evidence; read the ORDERING, not the coefficient.')
