"""Fresh reference objects/operands for a paired thinking-mode diagnostic."""
from __future__ import annotations
from dataclasses import replace
from belief_transfer.evals.target_free_controls import ControlCase, contexts, negate, number_word

def fresh_contexts() -> list[ControlCase]:
    result = []
    for c in contexts():
        if c.domain == 'arithmetic':
            i = int(c.context_id.rsplit('/',1)[1])
            if c.family == 'addition': a, b = 41+i, 2+i
            elif c.family == 'subtraction': a, b = 51+i, 2+i%3
            elif c.family == 'multiplication': a, b = 8, 3+i
            else: a, b = (51+i,12+i) if i%2==0 else (12+i,51+i)
            if c.family == 'comparison':
                actual, claimed = a > b, True
                claim = f'{number_word(a)} is greater than {number_word(b)}.'
            else:
                actual = {'addition': lambda: a+b, 'subtraction': lambda: a-b,
                          'multiplication': lambda: a*b}[c.family]()
                claimed = actual + (0 if c.supports_claim else 2)
                operator = {'addition':'plus','subtraction':'minus','multiplication':'times'}[c.family]
                claim = f'{number_word(a)} {operator} {number_word(b)} equals {number_word(claimed)}.'
            claim = claim[0].upper() + claim[1:]
            truth = actual if c.family == 'comparison' else actual == claimed
            result.append(replace(c, context_id=c.context_id.replace('tf/','modes/'), claim=claim,
                                  supports_claim=truth, truth_proof={'operation':c.family,'a':a,'b':b,'computed':actual,'claimed':claimed}))
        else:
            # New named objects, same reference-task families; not held-out language families.
            name = c.context_id.rsplit('/',1)[1]
            new = 'new-' + name
            claim, scope = c.claim.replace(name,new), c.scope.replace(name,new)
            proof = dict(c.truth_proof)
            if c.domain == 'normative': proof['stipulated_position'] = claim if c.supports_claim else negate(claim)
            result.append(replace(c, context_id=c.context_id.replace('tf/','modes/').replace(name,new),
                                  claim=claim, scope=scope, truth_proof=proof))
    return result


def penalty_contexts() -> list[ControlCase]:
    """Disjoint objects/operand pairs for the preselected presence-penalty validation."""
    result=[]
    for c in fresh_contexts():
        if c.domain!='arithmetic':
            name=c.context_id.rsplit('/',1)[1];new='penalty-'+name
            claim,scope=c.claim.replace(name,new),c.scope.replace(name,new)
            proof=dict(c.truth_proof)
            if c.domain=='normative':proof['stipulated_position']=claim if c.supports_claim else negate(claim)
            result.append(replace(c,context_id=c.context_id.replace('modes/','penalty/').replace(name,new),claim=claim,scope=scope,truth_proof=proof))
            continue
        p=c.truth_proof;a=p['a']+20;b=p['b']+20 if c.family=='comparison' else p['b']
        if c.family=='multiplication':a=9
        if c.family=='comparison':
            actual,claimed=a>b,True;claim=f'{number_word(a)} is greater than {number_word(b)}.'
        else:
            actual={'addition':lambda:a+b,'subtraction':lambda:a-b,'multiplication':lambda:a*b}[c.family]()
            claimed=actual+(0 if c.supports_claim else 2)
            operator={'addition':'plus','subtraction':'minus','multiplication':'times'}[c.family]
            claim=f'{number_word(a)} {operator} {number_word(b)} equals {number_word(claimed)}.'
        result.append(replace(c,context_id=c.context_id.replace('modes/','penalty/'),claim=claim[0].upper()+claim[1:],
            supports_claim=(actual==claimed),truth_proof={'operation':c.family,'a':a,'b':b,'computed':actual,'claimed':claimed}))
    return result
