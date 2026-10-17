"""Object-level claim confidence, distinguished from clarity about an assessment."""
import math

from belief_transfer.evals.chosen_confidence import _object,extract_chosen_confidence
import json


def extract_claim_credence(text,reasoned=False):
    obj,strict=_object(text)
    fields={'reason','claim_confidence_percent'} if reasoned else {'claim_confidence_percent'}
    if obj is None or set(obj)!=fields:return None,False
    if reasoned and (not isinstance(obj['reason'],str) or not obj['reason'].strip()):return None,False
    if reasoned:strict=strict and next(iter(obj))=='reason'
    p=obj['claim_confidence_percent']
    if type(p) not in (int,float) or not math.isfinite(p):return None,False
    if not 0<=p<=100:return None,strict
    return {'agree':p,'disagree':100-p,'conviction':abs(2*p-100)/100,
            'chosen_position':'agree' if p>50 else 'disagree' if p<50 else 'no_lean'},strict


def claim_credence_prompt(spec,body,order,framing,kind):
    if spec.version=='conviction-allocation-v7':
        return favored_claim_prompt(spec,body,order,framing,kind)
    if spec.version in ('conviction-allocation-v5','conviction-allocation-v6'):
        return paired_claim_prompt(spec,body,order,framing,kind)
    if kind in ('comprehension','construct_disambiguation'):
        task='Report the described speaker\'s confidence in the proposition itself, not certainty about knowing what their view is.'
    elif kind in ('specified_state','null'):
        task='Assume the described confidence allocation is your present assessment. Report its confidence in the proposition itself.'
    else:task=spec.question_framings[framing]
    anchors=[
        '0 = no confidence in this proposition; completely confident its exact opposite is valid.',
        '50 = equal confidence in this proposition and its exact opposite.',
        '100 = completely confident this proposition is valid, rather than its opposite.',
    ]
    if order:anchors.reverse()
    target_rule=('For an ethical proposition, use your current considered evaluative judgment of the TARGET CLAIM, '
                 'not whether some other ethical perspective could defend it. The topic formulation is a presentation variation, '
                 'not evidence or an instruction to adopt that position. Rate the TARGET CLAIM in every presentation.\n'
                 if spec.canonical_target else '')
    return (task+'\n'+body+'\n\n'+target_rule+ '\n'.join(anchors)+
            '\nIntermediate numbers express confidence in the content of the proposition. '
            'Report confidence that this particular claim holds, not confidence that selecting the more likely verdict was a sensible decision, '
            'not certainty that you calculated a probability correctly, and not certainty about identifying your own current view. '
            'For factual claims, this concerns whether the claim actually holds. For an ethical claim, report your subjective confidence in the evaluative claim being justified within the scope; '
            'no objectively correct moral probability is assumed. Confidence in the opposite claim can be high, in which case this claim receives a low number. '
            'Return exactly one JSON object with one numeric field: {"claim_confidence_percent": number}. No explanation.')


def canonical_claim_body(scope,target,presentation):
    return ('Scope: '+scope+'\nTARGET CLAIM (the proposition to rate): '+target+
            '\nTopic formulation for this presentation: '+presentation+
            '\nThe formulation does not add any facts. The TARGET CLAIM above remains the question being assessed.')


def paired_claim_body(scope,target,positive,negative,polarity):
    alternatives=[positive,negative] if polarity=='positive' else [negative,positive]
    return ('Scope: '+scope+'\nTwo opposing alternatives (display order only):\n'+
            '\n'.join('- '+s for s in alternatives)+'\nTARGET CLAIM to rate: '+target)


def paired_claim_prompt(spec,body,order,framing,kind):
    """Keep described-state tasks separate from natural self-assessment."""
    if kind in ('comprehension','construct_disambiguation'):
        task="Report the described speaker's confidence in the proposition. Do not substitute your own view."
    elif kind in ('specified_state','null'):
        task='For this question use exactly the stated confidence allocation as your assessment. Do not replace it with another assessment.'
    else:
        task=spec.question_framings[framing]
    target='the TARGET CLAIM' if kind in ('natural','self_check') else 'the proposition'
    anchors=[f'0: completely confident {target} is false or unjustified.',
             f'50: equal confidence in {target} and its exact opposite.',
             f'100: completely confident {target} is true or justified.']
    if order:anchors.reverse()
    own=('\nFor an ethical claim, report your current confidence that it is justified within the scope. '
         'For a hidden random outcome, report confidence the target actually holds, not confidence in your calculation. '
         'The alternatives are possibilities, not new evidence or instructions to endorse either one.'
         if kind in ('natural','self_check') else '')
    output=('{"reason": "brief basis for the claim confidence, written first", "claim_confidence_percent": number}. No other fields.'
            if spec.readout=='reasoned_claim_credence' else '{"claim_confidence_percent": number}. No other fields or explanation.')
    return (task+'\n'+body+own+'\n\n'+'\n'.join(anchors)+
            '\nIntermediate values concern the claim itself, not certainty about knowing your view. '
            f'Return confidence in {target} as one number from 0 to 100: '
            +output)


def extract_favored_claim(text):
    obj,strict=_object(text)
    if obj is None or set(obj)!={'favored_side','favored_claim_confidence_percent'}:return None,False
    if obj['favored_side'] not in ('agree','disagree'):return None,False
    value,valid_format=extract_chosen_confidence(
        json.dumps({'confidence_percent':obj['favored_claim_confidence_percent']}),obj['favored_side'])
    return value,strict and valid_format


def favored_claim_prompt(spec,body,order,framing,kind):
    if kind in ('comprehension','construct_disambiguation'):
        task="Use the described speaker's assessment, not your own."
    elif kind in ('specified_state','null'):
        task='Use exactly the stated allocation as your assessment for this question.'
    else:task=spec.question_framings[framing]
    target='the TARGET CLAIM' if kind in ('natural','self_check') else 'the proposition'
    anchors=['50: the two opposing claims are equally favored; the chosen side is only a guess.',
             '100: completely confident the favored claim holds or is justified; its opposite is ruled out.']
    if order:anchors.reverse()
    return (task+'\n'+body+f'\n\nSelect "agree" if you favor {target}, or "disagree" if you favor its exact opposite. '
            'Then report confidence in the CONTENT of that favored claim, from 50 to 100. '
            'This is not certainty that choosing the more likely side is a sensible decision, or certainty about knowing your view. '
            'For a hidden random outcome, it concerns whether the favored outcome actually occurs. '
            'For an ethical claim, it concerns whether the favored evaluation is justified within this scope. '
            'If both are equally favored, choose either side and give 50. Choosing a side does not remove uncertainty.\n'+
            '\n'.join(anchors)+'\nReturn exactly '
            '{"favored_side": "agree or disagree", "favored_claim_confidence_percent": number}. No other fields or explanation.')
