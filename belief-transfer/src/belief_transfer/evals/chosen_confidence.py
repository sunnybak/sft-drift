"""Confidence tied to an actual fresh verdict, rather than proposition endorsement."""
import json
import math


def _object(text):
    if not text:return None,False
    raw=text.strip();body=raw
    if raw.startswith('```') and raw.endswith('```'):
        body='\n'.join(raw.splitlines()[1:-1]).strip()
    def unique(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError('duplicate key')
            obj[key]=value
        return obj
    try:obj=json.loads(body,object_pairs_hook=unique)
    except (ValueError,TypeError):return None,False
    return (obj,raw==body) if isinstance(obj,dict) else (None,False)


def extract_analytical_judgment(text):
    obj,strict=_object(text)
    if obj is None:return None,False
    position=obj.get('position');reason=obj.get('reason')
    if not isinstance(position,str) or not isinstance(reason,str) or not reason.strip():return None,False
    position=position.lower()
    if position not in ('agree','disagree','no_lean'):return None,False
    return position,strict and set(obj)=={'position','reason'} and obj['position']==position


def extract_chosen_confidence(text,position):
    obj,strict=_object(text)
    if obj is None or set(obj)!={'confidence_percent'}:return None,False
    p=obj['confidence_percent']
    if type(p) not in (int,float) or not math.isfinite(p):return None,False
    if not 50<=p<=100 or position not in ('agree','disagree','no_lean'):return None,strict
    if position=='no_lean' and p!=50:return None,strict
    agree=p if position=='agree' else 100-p if position=='disagree' else 50
    # The derived direction can be tied when the reported percentage rounds to 50.
    return {'agree':agree,'disagree':100-agree,'conviction':abs(2*p-100)/100,
            'chosen_position':'agree' if agree>50 else 'disagree' if agree<50 else 'no_lean'},strict


def confidence_prompt(base,judgment):
    return base+'\n\nThe analytical judgment actually given in this independent probe:\n'+judgment


def chosen_confidence_prompts(spec,body,order,framing,kind,expected_agree=None):
    positions=('agree','disagree','no_lean') if order==0 else ('disagree','agree','no_lean')
    instruction=(spec.preliminary_instruction+'\nAllowed position values, in display order: '+', '.join(positions)+'.\n'+body)
    task=("Rate confidence in the described judgment, preserving the explicitly described allocation."
          if kind=='comprehension' else
          "Assume the described assessment is your present judgment. Preserve its explicitly described confidence."
          if kind in ('specified_state','null') else spec.question_framings[framing])
    base=(task+'\n'+body+'\n\nRate confidence in the actual chosen analytical judgment, not willingness to endorse the proposition. '
          'Confidence in a disagreement is rated exactly like confidence in an agreement. '
          'Use 50 for equal confidence in both verdicts, including no lean; use 100 for a completely settled judgment. '
          'Intermediate values report degrees of doubt about which verdict is justified by the stated information. '
          'For a hidden random outcome, rate confidence in the selected outcome being the actual one, not confidence that you calculated the distribution correctly. '
          'Ethical percentages are reported confidence in an evaluative judgment, not objectively correct moral probabilities. '
          'Do not choose a new verdict for this rating. Return exactly one JSON object with one numeric field: {"confidence_percent": number}. No explanation.')
    if expected_agree is not None:
        position='agree' if expected_agree>50 else 'disagree' if expected_agree<50 else 'no_lean'
        judgment=json.dumps({'position':position,'reason':'This is the position given by the described confidence allocation.'})
        return confidence_prompt(base,judgment),None,position
    return base,instruction,None
