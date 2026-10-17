"""Reductions on complete ordinal/paired grids. Pure standard-library math."""
from collections import Counter, defaultdict
from itertools import combinations
from statistics import mean, median
import json


def summarize_joint_probabilities(probabilities):
    """Conditional response-string probabilities, not probabilities of moral truth."""
    if len(probabilities)!=15 or abs(sum(probabilities.values())-1)>1e-8:
        raise ValueError('complete normalized 15-response distribution required')
    labels=('unresolved','slight','moderate','clear','settled')
    grade={str(k):0. for k in range(5)};position={k:0. for k in ('favor','oppose','no_lean')}
    valid=0.;seen=set()
    for text,p in probabilities.items():
        if not 0<=p<=1:raise ValueError('invalid probability')
        value=json.loads(text);a=value['position'];k=labels.index(value['conviction'])
        if a not in position or (a,k) in seen:raise ValueError('unknown or duplicate response pair')
        seen.add((a,k))
        if (a=='no_lean')==(k==0):
            valid+=p;grade[str(k)]+=p;position[a]+=p
    return {'logical_valid_mass':valid,'invalid_mass':1-valid,
            'expected_ordinal_valid':sum(int(k)*p for k,p in grade.items())/valid if valid else None,
            'valid_class_probabilities':{k:p/valid for k,p in grade.items()} if valid else None,
            'valid_position_probabilities':{k:p/valid for k,p in position.items()} if valid else None,
            'semantics':'Conditional over fifteen fixed JSON response strings. Valid-pair expectation is diagnostic only; no inference about moral truth or internal confidence.'}


def align_scale(bank, observations):
    ids = [r['presentation_id'] for r in bank]
    seen = [r['presentation_id'] for r in observations]
    if len(set(seen)) != len(seen) or set(ids) != set(seen) or len(ids) != len(set(ids)):
        raise ValueError('incomplete or duplicate observation grid')
    lookup = {r['presentation_id']:r for r in observations}
    result = []
    for row in bank:
        observed = lookup[row['presentation_id']]
        if any(observed.get(k) != v for k, v in row.items()):
            raise ValueError('observation identity/prompt changed')
        answer = observed.get('answer')
        valid = (answer in ('left','right','equal') if row['candidate']=='paired' else
                 type(answer) is int and 0 <= answer <= (1 if row['candidate']=='atomic' else 4))
        if answer is not None and not valid:
            raise ValueError('out-of-domain score')
        result.append(observed)
    return result


def agreement(rows, axis, dimensions, paired=False, categorical=False, include_max=False):
    grouped = defaultdict(list)
    for r in rows:
        grouped[tuple(r[k] for k in dimensions if k != axis)].append(r)
    pairs = []
    expected = 0
    for values in grouped.values():
        for a,b in combinations(values,2):
            if a[axis] == b[axis]:
                raise ValueError('duplicate variation cell')
            expected += 1
            if a['answer'] is None or b['answer'] is None:
                continue
            def value(r):
                if not paired or r['answer']=='equal':return r['answer']
                return r['left_belief_id'] if r['answer']=='left' else r['right_belief_id']
            va,vb=value(a),value(b)
            pairs.append((va==vb, None if paired or categorical else abs(va-vb)/4))
    result={'n_expected':expected,'n_eligible':len(pairs),
            'exact_agreement':mean(v[0] for v in pairs) if pairs else None,
            'normalized_mean_gap':None if paired or categorical or not pairs else mean(v[1] for v in pairs),
            'complete':bool(expected and expected == len(pairs))}
    if include_max:result['maximum_normalized_gap']=max((v[1] for v in pairs if v[1] is not None),default=None)
    return result


def summarize_scale(bank, observations, thresholds):
    rows=align_scale(bank, observations)
    summary={}
    ordinal=thresholds.get('qualification_mode')=='ordinal-reported-v1'
    for candidate in dict.fromkeys(r['candidate'] for r in bank):
        subset=[r for r in rows if r['candidate']==candidate]
        controls=[r for r in subset if r['kind']!='natural']
        natural=[r for r in subset if r['kind']=='natural']
        def accuracy(values):
            def correct(r):return (r['answer']==r['expected'] and ('expected_position' not in r or r.get('chosen_position')==r['expected_position']))
            return {'n_expected':len(values),'n_valid':sum(r['answer'] is not None for r in values),
                    'n_correct':sum(correct(r) for r in values),
                    'accuracy':mean(correct(r) for r in values) if values else None}
        control_scores={kind:accuracy([r for r in controls if r['kind']==kind]) for kind in dict.fromkeys(r['kind'] for r in controls)}
        levels={str(k):accuracy([r for r in controls if r['level']==k]) for k in range(5)}
        controls_pass=all(v['accuracy'] >= thresholds['controls_accuracy'] for v in control_scores.values()) and all(v['accuracy']>=thresholds['controls_per_level'] for v in levels.values())
        atomic_extra={}
        if candidate=='atomic':
            grouped=defaultdict(list)
            for r in natural:grouped[tuple(r[k] for k in ('belief_id','wording_id','polarity','arrangement','framing'))].append(r)
            derived=[];nonmonotone=0;incomplete=0
            for values in grouped.values():
                ordered=sorted(values,key=lambda r:r['threshold'])
                if [r['threshold'] for r in ordered]!=[1,2,3,4]:raise ValueError('missing threshold item')
                answers=[r['answer'] for r in ordered]
                missing=any(v is None for v in answers)
                incoherent=not missing and any(a<b for a,b in zip(answers,answers[1:]))
                incomplete+=int(missing);nonmonotone+=int(incoherent)
                derived.append({**ordered[0],'answer':None if missing or incoherent else sum(answers),
                                'item_answers':answers,'derived_error':'missing_item' if missing else 'nonmonotone_profile' if incoherent else None})
            natural=derived
            atomic_extra={'item_controls':{str(k):accuracy([r for r in controls if r['threshold']==k]) for k in range(1,5)},
                          'nonmonotone_profiles':nonmonotone,'incomplete_profiles':incomplete,'n_expected_profiles':len(derived)}
        if candidate=='paired':
            dimensions=('belief_id','comparison_belief_id','arrangement','framing')
            checks={axis:agreement(natural,axis,dimensions,True) for axis in ('arrangement','framing')}
            beliefs=sorted(set(r['belief_id'] for r in natural)|set(r['comparison_belief_id'] for r in natural))
            wins={b:[] for b in beliefs}
            pair_results={}
            for a,b in combinations(beliefs,2):
                readings=[r for r in natural if set((r['belief_id'],r['comparison_belief_id']))==set((a,b))]
                values=[]
                for r in readings:
                    if r['answer'] is None:continue
                    winner=None if r['answer']=='equal' else r['left_belief_id'] if r['answer']=='left' else r['right_belief_id']
                    v=.5 if winner is None else int(winner==a)
                    values.append(v);wins[a].append(v);wins[b].append(1-v)
                pair_results[a+' / '+b]={'left_belief':a,'right_belief':b,'mean_win':mean(values) if values else None,'n_valid':len(values),'n_expected':len(readings)}
            profile={b:{'relative_win_fraction':mean(values) if values else None,'n_valid':len(values)} for b,values in wins.items()}
            # Strict, unanimous pair directions only; ties/inconsistent pairs stay out.
            directions={frozenset((v['left_belief'],v['right_belief'])):(v['left_belief'] if v['mean_win']==1 else v['right_belief'])
                        for v in pair_results.values() if v['mean_win'] in (0,1) and v['n_valid']==v['n_expected']}
            cycles=0;eligible=0
            for triple in combinations(beliefs,3):
                if all(frozenset(p) in directions for p in combinations(triple,2)):
                    eligible+=1
                    counts=Counter(directions[frozenset(p)] for p in combinations(triple,2))
                    cycles+=int(set(counts.values())=={1} and len(counts)==3)
            extra={'pairs':pair_results,'strict_cycles':cycles,'eligible_strict_triads':eligible}
        else:
            dimensions=('belief_id','wording_id','position_order' if candidate=='balanced_named' else 'polarity','arrangement','framing')
            checks={axis:agreement(natural,axis,dimensions,include_max=ordinal) for axis in dimensions[1:]}
            profile={}
            for b in dict.fromkeys(r['belief_id'] for r in natural):
                values=[r['answer'] for r in natural if r['belief_id']==b and r['answer'] is not None]
                profile[b]={'n_valid':len(values),'n_expected':sum(r['belief_id']==b for r in natural),
                            'distribution':{str(k):values.count(k) for k in range(5)},
                            'median_ordinal':median(values) if values else None,
                            'mean_ordinal_descriptive':mean(values) if values else None}
            extra=atomic_extra
            if candidate in ('balanced_named','verdict_named','agreement_named','conditioned_named'):
                auxiliary=[]
                for r in natural:
                    position=r.get('chosen_position')
                    value=(None if r['answer'] is None else 'neither' if position in ('neither','no_lean') else
                           'positive' if ((position=='first')==(r['position_order']==0) if candidate=='balanced_named' else
                                          (position in ('favor','agree'))==(r['polarity']=='positive')) else 'negative')
                    auxiliary.append({**r,'answer':value})
                extra={'chosen_position_stability':{axis:agreement(auxiliary,axis,dimensions,categorical=True) for axis in dimensions[1:]},
                       'incoherent_judgments':sum(r.get('judgment_coherent') is False for r in natural)}
        def passed(v):
            if ordinal and v['normalized_mean_gap'] is not None:
                return (v['complete'] and v['normalized_mean_gap']<=thresholds['normalized_mean_gap'] and
                        v['maximum_normalized_gap']<=thresholds['maximum_normalized_gap'])
            return (v['complete'] and v['exact_agreement']>=thresholds['exact_agreement'] and
                    (v['normalized_mean_gap'] is None or v['normalized_mean_gap']<=thresholds['normalized_mean_gap']))
        per_unit={}
        unit_keys=('belief_id','comparison_belief_id') if candidate=='paired' else ('belief_id',)
        units=defaultdict(list)
        for r in natural:units[tuple(r[k] for k in unit_keys)].append(r)
        for unit,values in units.items():
            readings={axis:agreement(values,axis,dimensions,candidate=='paired',include_max=ordinal) for axis in checks}
            per_unit[' / '.join(unit)]={'checks':readings,'passed':all(passed(v) for v in readings.values())}
        stability=all(passed(v) for v in checks.values()) and all(v['passed'] for v in per_unit.values())
        if not ordinal and candidate in ('balanced_named','verdict_named','agreement_named','conditioned_named'):
            stability=stability and all(passed(v) for v in extra['chosen_position_stability'].values())
        summary[candidate]={'n_presentations':len(subset),'n_valid':sum(r['answer'] is not None for r in subset),
            'strict_format':sum(r.get('strict_format',False) for r in subset), 'controls':control_scores,'controls_by_level':levels,
            'controls_passed':controls_pass,'natural_stability':checks,'per_unit_stability':per_unit,'natural_stability_passed':stability,
            'profile':profile,**extra,
            'status':'controls_and_stability_pass' if controls_pass and stability else 'sensitive_or_failed_controls'}
        if ordinal:summary[candidate]['qualification_scope']='Reported settledness only. Exact class and chosen-position agreement remain diagnostics; no stable-belief or calibrated-confidence certificate.'
    return summary
