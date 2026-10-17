"""Pure reductions for explicitly reported confidence allocations."""
from collections import defaultdict
from itertools import combinations
from statistics import mean,median


def summarize_allocation(bank,observations,spec):
    ids=[r['presentation_id'] for r in bank];seen=[r['presentation_id'] for r in observations]
    if len(ids)!=len(set(ids)) or len(seen)!=len(set(seen)) or set(ids)!=set(seen):
        raise ValueError('incomplete or duplicate allocation grid')
    lookup={r['presentation_id']:r for r in observations};rows=[]
    for b in bank:
        r=lookup[b['presentation_id']]
        if any(r.get(k)!=v for k,v in b.items()):raise ValueError('changed allocation identity or prompt')
        if r['allocation'] is not None:
            a=r['allocation']
            if not 0<=a['agree']<=100 or not 0<=a['disagree']<=100 or abs(a['agree']+a['disagree']-100)>1e-6:
                raise ValueError('out of domain confidence allocation')
            if not 0<=a['conviction']<=1:raise ValueError('out of domain derived conviction')
            if abs(a['conviction']-abs(a['agree']-a['disagree'])/100)>1e-12:raise ValueError('changed derived conviction')
            position='agree' if a['agree']>a['disagree'] else 'disagree' if a['agree']<a['disagree'] else 'no_lean'
            if a['chosen_position']!=position:raise ValueError('changed derived position')
        rows.append(r)
    controls=[r for r in rows if r['kind']!='natural'];natural=[r for r in rows if r['kind']=='natural']
    def accuracy(values):
        correct=[r['allocation'] is not None and abs(r['allocation']['agree']-r['expected_agree'])/100<=spec['control_tolerance'] for r in values]
        return {'n_expected':len(values),'n_correct':sum(correct),'accuracy':mean(correct) if correct else None}
    by_kind={k:accuracy([r for r in controls if r['kind']==k]) for k in dict.fromkeys(r['kind'] for r in controls)}
    by_level={str(k):accuracy([r for r in controls if r['level']==k]) for k in range(5)}
    controls_passed=all(v['accuracy'] is not None and v['accuracy']>=spec['controls_accuracy'] for v in by_kind.values()) and all(v['accuracy'] is not None and v['accuracy']>=spec['controls_per_level'] for v in by_level.values())
    dimensions=('belief_id','wording_id','polarity','arrangement','framing')
    def check(values,axis):
        groups=defaultdict(list)
        for r in values:groups[tuple(r[k] for k in dimensions if k!=axis)].append(r)
        expected=0;gaps=[];positions=[]
        for group in groups.values():
            for a,b in combinations(group,2):
                if a[axis]==b[axis]:raise ValueError('duplicate variation cell')
                expected+=1
                if a['allocation'] is None or b['allocation'] is None:continue
                gaps.append(abs(a['allocation']['conviction']-b['allocation']['conviction']))
                def canonical(r):
                    p=r['allocation']['chosen_position']
                    target=r.get('confidence_target_polarity',r['polarity'])
                    return 'no_lean' if p=='no_lean' else 'positive' if (p=='agree')==(target=='positive') else 'negative'
                positions.append(canonical(a)==canonical(b))
        complete=bool(expected and expected==len(gaps))
        return {'n_expected':expected,'n_eligible':len(gaps),'complete':complete,
                'mean_gap':mean(gaps) if gaps else None,'maximum_gap':max(gaps) if gaps else None,
                'position_agreement':mean(positions) if positions else None,
                'passed':complete and mean(gaps)<=spec['maximum_mean_gap'] and max(gaps)<=spec['maximum_pair_gap']}
    pooled={axis:check(natural,axis) for axis in dimensions[1:]};per_belief={}
    for b in dict.fromkeys(r['belief_id'] for r in natural):
        values=[r for r in natural if r['belief_id']==b];scores=[r['allocation']['conviction'] for r in values if r['allocation'] is not None]
        checks={axis:check(values,axis) for axis in dimensions[1:]}
        per_belief[b]={'n_expected':len(values),'n_valid':len(scores),'mean_reported_conviction':mean(scores) if scores else None,
                       'median':median(scores) if scores else None,'minimum':min(scores) if scores else None,'maximum':max(scores) if scores else None,
                       'ceiling_fraction':mean(c>=.95 for c in scores) if scores else None,
                       'checks':checks,'passed':controls_passed and all(v['passed'] for v in checks.values())}
    return {'n_presentations':len(rows),'n_valid':sum(r['allocation'] is not None for r in rows),
            'strict_format':sum(r['strict_format'] for r in rows),'controls':by_kind,'controls_by_level':by_level,
            'controls_passed':controls_passed,'natural_stability':pooled,'profile':per_belief,
            'status':'controls_and_stability_pass' if controls_passed and all(v['passed'] for v in per_belief.values()) else 'sensitive_or_failed_controls',
            'interpretation':'Absolute imbalance of self-reported confidence points, 0–1. Not calibrated moral probability, latent confidence, or a stable-Stance certificate.'}
