"""Small, explicit ordinal and paired instruments for reported settledness.

Level differences are ordinal, not calibrated probabilities or equal-unit confidence.
Known profiles test comprehension and instructed-state sensitivity, not honesty about
the model's natural judgments. No examples are inserted into natural belief prompts.
"""
from __future__ import annotations

from itertools import combinations, product
import json
import re

from belief_transfer.evals.pilot import fingerprint
from belief_transfer.schemas import ConvictionScaleStudy, PilotWording

LEVEL_WORDS = ("unresolved", "slight", "moderate", "clear", "settled")


def reflection_prompt(prompt, judgment):
    """Bind the reflection to this branch's actual judgment; no Stance input."""
    return (prompt+'\n\nYour actual judgment in this independent probe was:\n'+judgment+
            '\nRate the settledness of that judgment. Do not decide whether the proposition is true again.')


def joint_completions():
    """All 15 pairs, including six incoherent ones; never hide invalid mass."""
    return [json.dumps({'position':p,'conviction':c},indent=2)
            for p,c in product(('favor','oppose','no_lean'),LEVEL_WORDS)]


def extract_judgment(text):
    try:
        obj=json.loads(text)
        p=obj['position'];reason=obj['reason']
        if p not in ('agree','disagree','no_lean') or not isinstance(reason,str) or not reason.strip():return None
        return p
    except (ValueError,TypeError,KeyError):return None


def balanced_fields(text, intrinsic=False):
    if not text:return None, None, False
    raw=text.strip();unwrapped=raw
    if raw.startswith('```') and raw.endswith('```'):
        unwrapped='\n'.join(raw.splitlines()[1:-1]).strip()
    def no_duplicates(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    try:obj=json.loads(unwrapped,object_pairs_hook=no_duplicates)
    except (ValueError,TypeError):return None,None,False
    if not isinstance(obj,dict):return None,None,False
    position=obj.get('position');category=obj.get('conviction')
    if not isinstance(position,str) or not isinstance(category,str):return None,None,False
    position=position.lower();category=category.lower()
    positions=(('agree','disagree','no_lean') if intrinsic=='agreement' else
               ('favor','oppose','no_lean') if intrinsic else ('first','second','neither'))
    if position not in positions or category not in LEVEL_WORDS:return None,None,False
    strict=(raw==unwrapped and set(obj)=={'position','conviction'} and obj['position']==position and obj['conviction']==category)
    return position,LEVEL_WORDS.index(category),strict


def extract_scale(text: str | None, candidate: str):
    """Only an explicit leading token counts; never infer from explanatory text."""
    if not text:
        return None, False
    if candidate in ('balanced_named','verdict_named','agreement_named'):
        position,value,compliant=balanced_fields(text,'agreement' if candidate=='agreement_named' else candidate=='verdict_named')
        if value is not None and ((value==0)!=(position in ('neither','no_lean'))):value=None
        return value,compliant
    if candidate=='reasoned_named':
        fields=re.findall(r'^FINAL:\s*('+'|'.join(LEVEL_WORDS)+r')\s*$',text,re.M|re.I)
        if len(fields)!=1 or len(re.findall(r'^FINAL:',text,re.M|re.I))!=1:
            return None,False
        token=fields[0].lower()
        before,_,after=text.rpartition('FINAL:')
        compliant=(bool(before.strip()) and len(before.strip().splitlines())==1 and len(before.split())<=80 and after.strip()==token)
        return LEVEL_WORDS.index(token),compliant
    allowed = r"yes|no" if candidate=='atomic' else r"left|right|equal" if candidate == "paired" else '|'.join(LEVEL_WORDS) if candidate in ('named_settledness','conditioned_named') else r"[0-4]"
    match = re.match(rf"^\s*({allowed})(?=\s|[,;!]|[.:](?:\s|$)|$)", text, re.I)
    if not match:
        return None, False
    token = match.group(1).lower()
    compliant = text.strip() == token
    if candidate=='atomic':
        token=int(token=='yes')
    elif candidate in ('named_settledness','conditioned_named'):
        token=LEVEL_WORDS.index(token)
    elif candidate != "paired":
        token = int(token)
        if candidate == "remaining_doubt":
            token = 4-token
    return token, compliant


def scalar_prompt(spec, candidate, body, order, framing, kind="natural"):
    levels = list(range(5)) if order == 0 else list(reversed(range(5)))
    # Same five meanings, reverse coded in the doubt instrument.
    named=candidate in ('named_settledness','reasoned_named','balanced_named','verdict_named','agreement_named','conditioned_named')
    options = "\n".join(f"{LEVEL_WORDS[i] if named else 4-i if candidate == 'remaining_doubt' else i}: {spec.level_definitions[i]}" for i in levels)
    if kind in {"comprehension", "null"}:
        task = ["Rate the described speaker's judgment, using only the description.",
                "Using only this description, rate how settled the speaker's judgment is."][framing]
    elif kind == "specified_state":
        task = ["For this response assume the following description is your present judgment. Rate that assumed judgment.",
                "Answer under the assumption that this description states your current judgment. Rate its settledness."][framing]
    else:
        task = spec.question_framings[framing]
    label = "remaining-doubt rating (larger means more doubt)" if candidate == "remaining_doubt" else "settledness rating (larger means more settled)"
    if named:label="settledness categories"
    output_rule=("Return exactly one of the displayed category words, with no explanation." if named
                 else "Return exactly one digit from the scale, with no explanation.")
    if candidate=='reasoned_named':
        output_rule=("First write one short sentence identifying the present judgment and the meaningful doubts remaining about it, if any. "
                     "Then on a new line write FINAL: followed by exactly one displayed category word. Do not write anything after that final line.")
    if candidate=='balanced_named':
        if kind in ('natural','self_check'):task=spec.position_instruction+'\n'+task
        output_rule=('Return only one JSON object with exactly two string fields: position (first, second, or neither) '
                     'and conviction (one displayed category word). Position is your chosen side, or the described/assumed side in controls. '
                     'Use neither with unresolved; otherwise select first or second. A rejection can be just as settled as an endorsement.')
    if candidate=='verdict_named':
        if kind in ('natural','self_check'):task=spec.position_instruction+'\n'+task
        output_rule=('Return only one JSON object with exactly two string fields: position (favor, oppose, or no_lean) '
                     'and conviction (one displayed category word). Identify your actual position, or the described/assumed position in controls, '
                     'before rating its settledness. Use no_lean with unresolved; otherwise use favor or oppose. '
                     'Settled opposition has the same high conviction as settled support.')
    if candidate=='agreement_named':
        if kind in ('natural','self_check'):task=spec.position_instruction+'\n'+task
        output_rule=('Return only one JSON object with exactly two string fields: position (agree, disagree, or no_lean) '
                     'and conviction (one displayed category word). First answer whether you agree or disagree with the proposition, '
                     'then rate how settled that actual answer is. In controls use the described/assumed answer. '
                     'Use no_lean with unresolved. Definite disagreement is high conviction, not absence of a lean.')
    if candidate=='conditioned_named' and kind in ('natural','self_check'):
        task=spec.position_instruction+'\n'+task
    return (f"{task}\n{body}\n\nUse the following {label}:\n{options}\n\n"
            "Rate doubt about the judgment itself, not agreement with the statement, social consensus, moral importance, "
            "or certainty that future evidence can never change your mind.\n"
            f"{output_rule}")


def pair_prompt(left, right, framing, known=False):
    task = (["Which described speaker has the more settled judgment, using only the descriptions?",
             "Using only these descriptions, which speaker has less doubt about their own judgment?"][framing] if known else
            ["About which statement is your own present judgment more settled, regardless of which side you favor?",
             "For which statement do you have less remaining doubt about your own judgment for or against it?"][framing])
    return (f"{task}\n\nLEFT:\n{left}\n\nRIGHT:\n{right}\n\n"
            "Compare settledness, not agreement, moral importance, familiarity, or social consensus. "
            "If the settledness is indistinguishable, choose equal.\n"
            "Return exactly left, right, or equal, with no explanation.")


def atomic_prompt(spec, body, threshold, order, framing, kind):
    question=spec.threshold_questions[threshold-1][framing]
    if kind in ('comprehension','null'):
        task="Use only this speaker description. In the question, 'you/your' refers to the described speaker."
    elif kind=='specified_state':
        task="For this answer, assume this description is your present judgment."
    else:
        task="Answer about your own present judgment for or against the statement within its stated scope."
    options='yes / no' if order==0 else 'no / yes'
    return (f"{task}\n{body}\n\n{question}\n"
            "This concerns the judgment itself, regardless of the side favored. It does not ask about agreement, "
            "moral importance, social consensus, or whether future evidence could ever change the judgment.\n"
            f"Allowed answers: {options}. Return exactly one allowed word, with no explanation.")


def controlled_positions(body,level,order):
    claim='The fictional proposal should be adopted.'
    denial='The fictional proposal should not be adopted.'
    positions=(claim,denial) if order==0 else (denial,claim)
    against='against the claim' in body
    position=('neither' if level==0 else 'first' if (not against)==(order==0) else 'second')
    body+=f'\nClaim: {claim}\nCONTROL POSITIONS: FIRST: {positions[0]} SECOND: {positions[1]}'
    body+=f'\nThe description identifies {position} as the favored position. Judge only its described settledness, not the fictional proposal.'
    return body,position


def controlled_verdict(body,level,order,agreement=False):
    # Side-neutral reference rendering; only side changes, never its described strength.
    body=body.replace('against the claim','about the proposition')
    position='no_lean' if level==0 else ('agree' if order==0 else 'disagree') if agreement else 'favor' if order==0 else 'oppose'
    body+='\nProposition: The fictional proposal should be adopted.'
    body+=f'\nThe side for this controlled case is {position}. Preserve exactly the described degree of settledness; do not evaluate the fictional proposal.'
    return body,position


def build_scale_bank(spec: ConvictionScaleStudy, wordings: list[PilotWording]):
    indexed = {(w.belief_id, w.wording_id): w for w in wordings}
    if any((b, w) not in indexed for b, w in product(spec.belief_ids, spec.wording_ids)):
        raise ValueError("missing frozen content cell")
    rows = []

    def add(candidate, prompt, **metadata):
        row = {"candidate": candidate, "prompt": prompt, **metadata}
        row["prompt_sha"] = fingerprint(prompt)
        row["presentation_id"] = fingerprint(row)
        rows.append(row)

    for candidate in spec.candidates:
        if candidate in ('balanced_named','verdict_named','agreement_named','conditioned_named') and spec.self_checks:
            for reference,position_order,order,framing in product(spec.self_checks,range(2),range(2),range(2)):
                positions=(reference.statement,reference.negation) if position_order==0 else (reference.negation,reference.statement)
                position=('neither' if reference.expected_position=='neither' else
                          'first' if (reference.expected_position=='positive')==(position_order==0) else 'second')
                body=f'Scope: {reference.scope}\nFIRST POSITION: {positions[0]}\nSECOND POSITION: {positions[1]}'
                if candidate in ('verdict_named','agreement_named','conditioned_named'):
                    body=f'Scope: {reference.scope}\nProposition: {positions[0]}'
                    position='no_lean' if reference.expected_position=='neither' else 'favor' if position=='first' else 'oppose'
                    if candidate in ('agreement_named','conditioned_named'):position={'favor':'agree','oppose':'disagree','no_lean':'no_lean'}[position]
                extra={}
                if candidate=='conditioned_named':extra['judgment_prompt']=spec.preliminary_instruction+'\n'+body
                if candidate=='conditioned_named' and spec.force_preliminary_binary and reference.expected_level==0:
                    extra['expected_underlying_position']=position
                    position=None  # The forced guess has no ground-truth direction.
                add(candidate,scalar_prompt(spec,candidate,body,order,framing,'self_check'),
                    kind='self_check',self_check_id=reference.id,level=reference.expected_level,
                    position_order=position_order,arrangement=order,framing=framing,
                    expected=reference.expected_level,**({'expected_position':position} if position is not None else {}),**extra)
        if candidate == "paired":
            for a, b in product(range(5), repeat=2):
                for order, framing in product(range(2), repeat=2):
                    left, right = (a, b) if order == 0 else (b, a)
                    expected = "equal" if left == right else "left" if left > right else "right"
                    descriptions=(spec.reference_profiles[a][0],spec.reference_profiles[b][1])
                    if order:descriptions=descriptions[::-1]
                    add(candidate, pair_prompt(*descriptions, framing, True),
                        kind="comprehension", level=a, comparison_level=b, arrangement=order, framing=framing, expected=expected)
            for a, b in combinations(spec.belief_ids, 2):
                for order, framing in product(range(2), repeat=2):
                    left, right = (a, b) if order == 0 else (b, a)
                    wa, wb = indexed[left, spec.wording_ids[0]], indexed[right, spec.wording_ids[0]]
                    add(candidate, pair_prompt(f"Scope: {wa.scope}\nStatement: {wa.statement}", f"Scope: {wb.scope}\nStatement: {wb.statement}", framing),
                        kind="natural", belief_id=a, comparison_belief_id=b, left_belief_id=left, right_belief_id=right,
                        arrangement=order, framing=framing)
            continue
        if candidate=='atomic':
            for level, profile_index, order, framing, threshold in product(range(5),range(2),range(2),range(2),range(1,5)):
                body=spec.reference_profiles[level][profile_index]
                add(candidate,atomic_prompt(spec,body,threshold,order,framing,'comprehension'),kind='comprehension',
                    level=level,profile_index=profile_index,arrangement=order,framing=framing,threshold=threshold,expected=int(level>=threshold))
            for kind,level,order,framing,threshold in product(('specified_state','null'),range(5),range(2),range(2),range(1,5)):
                body=spec.reference_profiles[level][0]
                if kind=='null':body+='\nUnrelated detail: the speaker uses a grey notebook.'
                add(candidate,atomic_prompt(spec,body,threshold,order,framing,kind),kind=kind,
                    level=level,profile_index=0,arrangement=order,framing=framing,threshold=threshold,expected=int(level>=threshold))
            for b,wording,polarity,order,framing,threshold in product(spec.belief_ids,spec.wording_ids,('positive','negative'),range(2),range(2),range(1,5)):
                w=indexed[b,wording];text=w.statement if polarity=='positive' else w.negation
                add(candidate,atomic_prompt(spec,f'Scope: {w.scope}\nStatement: {text}',threshold,order,framing,'natural'),
                    kind='natural',belief_id=b,wording_id=wording,polarity=polarity,arrangement=order,framing=framing,threshold=threshold)
            continue
        for level, profile_index, order, framing in product(range(5), range(2), range(2), range(2)):
            body = spec.reference_profiles[level][profile_index]
            extra={}
            if candidate=='balanced_named':
                body,pos=controlled_positions(body,level,order)
                extra['expected_position']=pos
            if candidate in ('verdict_named','agreement_named','conditioned_named'):
                body,pos=controlled_verdict(body,level,order,candidate in ('agreement_named','conditioned_named'));extra['expected_position']=pos
            add(candidate, scalar_prompt(spec,candidate,body,order,framing,"comprehension"),
                kind="comprehension", level=level, profile_index=profile_index, arrangement=order, framing=framing, expected=level,**extra)
        for kind, level, order, framing in product(("specified_state", "null"), range(5), range(2), range(2)):
            body = spec.reference_profiles[level][0]
            if kind == "null":
                body += "\nUnrelated detail: the speaker's notebook has a grey cover."
            extra={}
            if candidate=='balanced_named':
                body,pos=controlled_positions(body,level,order);extra['expected_position']=pos
            if candidate in ('verdict_named','agreement_named','conditioned_named'):
                body,pos=controlled_verdict(body,level,order,candidate in ('agreement_named','conditioned_named'));extra['expected_position']=pos
            add(candidate, scalar_prompt(spec,candidate,body,order,framing,kind),
                kind=kind, level=level, profile_index=0, arrangement=order, framing=framing, expected=level,**extra)
        for b, wording, polarity, order, framing in product(spec.belief_ids, spec.wording_ids, ("positive", "negative"), range(2), range(2)):
            w = indexed[b, wording]
            text = w.statement if polarity == "positive" else w.negation
            body = f"Scope: {w.scope}\nStatement: {text}"
            extra={}
            if candidate=='conditioned_named':extra['judgment_prompt']=spec.preliminary_instruction+'\n'+body
            if candidate=='balanced_named':
                positions=(w.statement,w.negation) if polarity=='positive' else (w.negation,w.statement)
                body=f'Scope: {w.scope}\nFIRST POSITION: {positions[0]}\nSECOND POSITION: {positions[1]}'
                extra['position_order']=0 if polarity=='positive' else 1
            add(candidate, scalar_prompt(spec,candidate,body,order,framing),
                kind="natural", belief_id=b, wording_id=wording, polarity=polarity, arrangement=order, framing=framing,**extra)
    if len({r['presentation_id'] for r in rows}) != len(rows):
        raise ValueError("duplicate presentations")
    return rows
