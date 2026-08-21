"""H23 falsifier, part 1: valence coherence from the experiment SPEC ALONE.

Registered measure (hypotheses/open/H23, `What would falsify it`):
  "mean pairwise correlation of per-dimension premise valence, computed from the
   experiment spec alone, before looking at any halo number"

Valence of a dimension = +1 if the POSITIVE polarity's premise values are the
favourable/desirable ones for that dimension, -1 if the NEGATIVE polarity's are.
Direction of "favourable" is fixed per dimension by whether the quantity is a
good-thing-more (wages, manure captured, deployments) or a bad-thing-more
(mortality, outages, cost, water use, lead time, injuries).
"""
import yaml, re, itertools, statistics

# hand-coded ONCE from the metric names, not from any result: does a LARGER number
# on this quantity mean a BETTER outcome?
HIGHER_IS_BETTER = {
    'mortality': False, 'lameness': False, 'water': False, 'manure': True,
    # 'prices' is stated as "N percent BELOW the small-farm equivalent" -- a DISCOUNT
    # DEPTH, not a price. A larger N is a cheaper product, i.e. favourable to the case
    # that the practice is acceptable. Coded False on the first pass, which flipped this
    # dimension's valence and manufactured a coherence difference that is not there.
    'prices': True,
    'injuries': False, 'wages': True,
    'outages': False, 'recovery': False, 'lead time': False, 'deployments': True,
    'spend': False, 'first release': False, 'feature work': True,
}

NUM = re.compile(r'(\d+(?:\.\d+)?)')

def facts(txt):
    ns = [float(x) for x in NUM.findall(txt.replace(',', ''))]
    return statistics.mean(ns) if ns else None

def quantity(txt):
    for k in HIGHER_IS_BETTER:
        if k in txt:
            return k
    return None

for exp in ['factory_farming', 'software_architecture']:
    spec = yaml.safe_load(open(f'configs/experiment/{exp}.yaml'))
    dims = spec['dataset']['dimensions']
    print(f'=== {exp}')
    vals = {}
    for dim, pol in dims.items():
        pos, neg = pol['positive'], pol['negative']
        if pos == neg:
            print(f'  {dim:22s} NULL (identical across polarities) -- excluded')
            continue
        signs, ratios = [], []
        for p, n in zip(pos, neg):
            q = quantity(p)
            assert q is not None, (dim, p)
            vp, vn = facts(p), facts(n)
            better_is_pos = (vp > vn) == HIGHER_IS_BETTER[q]
            signs.append(+1 if better_is_pos else -1)
            ratios.append(max(vp, vn) / min(vp, vn))
        v = +1 if sum(signs) > 0 else -1
        vals[dim] = (v, statistics.mean(ratios))
        print(f'  {dim:22s} valence {v:+d}   mean contrast ratio {statistics.mean(ratios):5.1f}x'
              f'   ({len(pos)} facts)')
    vs = [v for v, _ in vals.values()]
    pairs = list(itertools.combinations(vs, 2))
    coh = statistics.mean([1.0 if a == b else -1.0 for a, b in pairs])
    mag = statistics.mean([m for _, m in vals.values()])
    print(f'  -> VALENCE COHERENCE (registered measure) = {coh:+.2f}   '
          f'[{len(pairs)} dimension pairs, all {"agree" if coh==1 else "mixed"}]')
    print(f'  -> mean contrast magnitude (NOT the registered measure) = {mag:.1f}x')
