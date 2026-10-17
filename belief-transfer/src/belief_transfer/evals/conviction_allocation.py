"""Independent allocation of reported confidence between opposing judgments."""
import json
import math
from itertools import product

from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.chosen_confidence import chosen_confidence_prompts
from belief_transfer.evals.claim_credence import claim_credence_prompt,canonical_claim_body,paired_claim_body


def extract_allocation(text):
    """Read numbers, never a judge's inference; separate syntax from semantics."""
    if not text:return None,False
    raw=text.strip();body=raw
    if raw.startswith('```') and raw.endswith('```'):
        body='\n'.join(raw.splitlines()[1:-1]).strip()
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate key')
            result[key]=value
        return result
    try:obj=json.loads(body,object_pairs_hook=unique)
    except (ValueError,TypeError):return None,False
    if not isinstance(obj,dict) or set(obj)!={'agree','disagree'}:return None,False
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in obj.values()):return None,False
    strict=raw==body
    if any(not 0<=v<=100 for v in obj.values()) or abs(sum(obj.values())-100)>1e-6:
        return None,strict
    return {'agree':obj['agree'],'disagree':obj['disagree'],
            'conviction':abs(obj['agree']-obj['disagree'])/100,
            'chosen_position':'agree' if obj['agree']>obj['disagree'] else 'disagree' if obj['agree']<obj['disagree'] else 'no_lean'},strict


def allocation_prompt(spec,body,order,framing,kind):
    task=("Report only the confidence allocation described below. Do not evaluate the fictional proposition."
          if kind=='comprehension' else
          "For this response, assume the confidence allocation described below is your current assessment. Preserve it exactly."
          if kind in ('specified_state','null') else spec.question_framings[framing])
    keys=('agree','disagree') if order==0 else ('disagree','agree')
    shape='{'+', '.join('"'+k+'": number' for k in keys)+'}'
    return (task+'\n'+body+'\n\nDivide exactly 100 confidence points between agreeing and disagreeing with this proposition. '
            'Express how sure you are which judgment to choose, given only the scope. Equal points means neither side is favored. '
            'Strong confidence in disagreement is as definite a judgment as strong confidence in agreement. '
            'For a hidden random outcome, express uncertainty about the actual outcome, not certainty that its distribution was described. '
            'For an ethical proposition, report confidence in your evaluative judgment; these points do not imply an objectively correct moral probability. '
            'Return only a JSON object with exactly these two numeric fields: '+shape+'. No explanation.')


def build_allocation_bank(spec,wordings,smoke=False):
    indexed={(w.belief_id,w.wording_id):w for w in wordings};rows=[]
    framings=range(1) if smoke else range(2)
    words=spec.wording_ids[:1] if smoke else spec.wording_ids
    def claim_body(scope,target,positive,negative,polarity):
        if spec.version in ('conviction-allocation-v5','conviction-allocation-v6','conviction-allocation-v7'):
            return paired_claim_body(scope,target,positive,negative,polarity)
        statement=positive if polarity=='positive' else negative
        return canonical_claim_body(scope,target,statement) if spec.canonical_target else 'Scope: '+scope+'\nProposition: '+statement
    def add(body,kind,order,framing,**values):
        extra={}
        if spec.readout=='chosen_confidence':
            described=values.get('expected_agree') if kind in ('comprehension','specified_state','null') else None
            prompt,preliminary,position=chosen_confidence_prompts(spec,body,order,framing,kind,described)
            if preliminary is not None:extra['judgment_prompt']=preliminary;extra['judgment_prompt_sha']=fingerprint(preliminary)
            if position is not None:extra['specified_position']=position
        elif spec.readout in ('claim_credence','reasoned_claim_credence','favored_claim_confidence'):prompt=claim_credence_prompt(spec,body,order,framing,kind)
        else:prompt=allocation_prompt(spec,body,order,framing,kind)
        row={'kind':kind,'arrangement':order,'framing':framing,'prompt':prompt,'prompt_sha':fingerprint(prompt),**values,**extra}
        row['presentation_id']=fingerprint(row);rows.append(row)
    if spec.clarity_controls:
        for level,direction,order,framing in product(range(5),range(2),range(2),framings):
            agree=spec.heads_counts[level] if direction==0 else 100-spec.heads_counts[level]
            stance='favors the proposition' if agree>50 else 'opposes the proposition' if agree<50 else 'favors neither side'
            body=('Proposition: A fictional proposal should be adopted.\n'
                  f'The described speaker is 100% certain they know their own current view, which {stance}. '
                  f'Separately, the speaker assigns {agree} confidence points to the proposition being valid and {100-agree} to its exact opposite being valid.')
            add(body,'construct_disambiguation',order,framing,level=level,direction=direction,expected_agree=agree)
    for kind,level,direction,order,framing in product(('comprehension','specified_state','null'),range(5),range(2),range(2),framings):
        agree=spec.heads_counts[level] if direction==0 else 100-spec.heads_counts[level]
        body=('Proposition: A fictional proposal should be adopted.\n'
              f'The described assessment assigns {agree} confidence points to agreeing and {100-agree} to disagreeing.')
        if kind=='null':body+='\nUnrelated detail: the speaker uses a grey notebook.'
        add(body,kind,order,framing,level=level,direction=direction,expected_agree=agree)
    for level,polarity,order,framing in product(range(5),('positive','negative'),range(2),framings):
        heads=spec.heads_counts[level]
        scope=(f'One ticket is selected uniformly at random from exactly 100 tickets: {heads} are labelled HEADS '
               f'and {100-heads} are labelled TAILS. No observation of the selected ticket is available.')
        canonical='The selected ticket is labelled HEADS.'
        statement=canonical
        if polarity=='negative':statement='It is not the case that the selected ticket is labelled HEADS.'
        body=claim_body(scope,canonical,canonical,'It is not the case that the selected ticket is labelled HEADS.',polarity)
        expected=heads if spec.canonical_target or polarity=='positive' else 100-heads
        add(body,'self_check',order,framing,
            self_check_id='hidden_ticket',level=level,polarity=polarity,
            expected_agree=expected,**({'confidence_target_polarity':'positive'} if spec.canonical_target else {}))
    for polarity,order,framing in product(('positive','negative'),range(2),framings):
        statement='Two plus two equals four.' if polarity=='positive' else 'It is not the case that two plus two equals four.'
        body=claim_body('Ordinary integer arithmetic.','Two plus two equals four.','Two plus two equals four.','It is not the case that two plus two equals four.',polarity)
        add(body,'self_check',order,framing,
            self_check_id='integer_addition',level=4,polarity=polarity,expected_agree=100 if spec.canonical_target or polarity=='positive' else 0,
            **({'confidence_target_polarity':'positive'} if spec.canonical_target else {}))
    if spec.canonical_target:
        # Keep a genuinely false target: reversing a true target's presentation
        # alone cannot test confidence in rejecting the target being rated.
        for polarity,order,framing in product(('positive','negative'),range(2),framings):
            target='Two plus two equals five.'
            statement=target if polarity=='positive' else 'It is not the case that two plus two equals five.'
            add(claim_body('Ordinary integer arithmetic.',target,target,'It is not the case that two plus two equals five.',polarity),
                'self_check',order,framing,self_check_id='integer_addition_false',
                level=4,polarity=polarity,expected_agree=0,confidence_target_polarity='positive')
    for belief_id,wording_id,polarity,order,framing in product(spec.belief_ids,words,('positive','negative'),range(2),framings):
        w=indexed[belief_id,wording_id];statement=w.statement if polarity=='positive' else w.negation
        body='Scope: '+w.scope+'\nProposition: '+statement
        if spec.canonical_target:
            canonical=indexed[belief_id,'w0']
            if w.scope!=canonical.scope:raise ValueError('canonical and variant scopes differ')
            body=claim_body(w.scope,canonical.statement,w.statement,w.negation,polarity)
        add(body,'natural',order,framing,
            belief_id=belief_id,wording_id=wording_id,polarity=polarity,
            **({'confidence_target_polarity':'positive'} if spec.canonical_target else {}))
    if len(rows)!=len({r['presentation_id'] for r in rows}):raise ValueError('duplicate allocation presentation')
    return rows
