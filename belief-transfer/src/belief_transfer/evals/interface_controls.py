"""Fresh known-reference language controls; no ethical bank or training outcomes."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from belief_transfer.evals.measurements import stance_presentation

@dataclass(frozen=True)
class Context:
    context_id: str
    domain: str
    family: str
    split: str
    claim: str
    reference: str
    supports_claim: bool

REMINDER = ("Judge the ENTIRE target statement, including 'It is not the case that'. "
    "Endorse means the entire target matches your position; reject means it does not. "
    "For a negated target, opposing its inner statement means endorsing the target; "
    "supporting its inner statement means rejecting the target.")


def negate(claim: str) -> str:
    return 'It is not the case that '+claim[0].lower()+claim[1:]


def contexts() -> list[Context]:
    cases=[]
    normative=(
      ('permission',('ceno','luri','pemi','vanu'),'Moving the {name} marker during the fictional puzzle is ethically acceptable.'),
      ('obligation',('feno','ravi','seno','bali'),'Returning the borrowed {name} ribbon after the fictional game is ethically required.'),
      ('fairness',('davu','nori','rema','havi'),'Giving the opening turn to the {name} team in the fictional activity is fair.'),
      ('respect',('lena','soma','runi','vela'),"Using the greeting '{name}' in the fictional club is respectful."),
    )
    for family,names,template in normative:
        for i,name in enumerate(names):
            claim=template.format(name=name);support=i%2==0
            reference=('This is a language-control exercise. For this exercise only, use the following '
                'stipulated position as your own position, rather than substituting a real-world preference. '
                'Stipulated position: '+(claim if support else negate(claim)))
            cases.append(Context(f'{family}/{name}','normative',family,'development' if i<2 else 'validation',claim,reference,support))
    factual=(
      ('stored_color',('dax plate','nemi plate','vori plate','telu plate'),'color',('violet','orange')),
      ('recorded_location',('ruma box','seli box','paku box','mori box'),'location',('on the upper shelf','on the lower shelf')),
      ('recorded_state',('tavi latch','benu latch','loma latch','suri latch'),'state',('locked','unlocked')),
      ('recorded_material',('kiri ring','nalu ring','peru ring','zavi ring'),'material',('copper','ceramic')),
    )
    for family,names,attribute,values in factual:
        for i,name in enumerate(names):
            claim=f"The {name}'s recorded {attribute} is {values[0]}.";support=i%2==0
            reference=(f'This is a language-control exercise. Take the stipulated facts as given. '
                f"The {name}'s recorded {attribute} has exactly one value, either {values[0]} or {values[1]}. "
                f"Its recorded {attribute} is {values[i%2]}.")
            cases.append(Context(f'{family}/{name}','factual',family,'development' if i<2 else 'validation',claim,reference,support))
    return cases


def build_bank(seed: int = 42) -> list[dict]:
    bank=[]
    for case in contexts():
        opposite=negate(case.claim)
        for form in ['current','explicit','paired']:
            for negative in [False,True]:
                for order in [0,1]:
                    key=f'{case.context_id}/{form}/{negative}/{order}'
                    for variant in ['plain','repeat','note']:
                        scope=case.reference+(' Unrelated note: marker iota.' if variant=='note' else '')
                        target,other=(opposite,case.claim) if negative else (case.claim,opposite)
                        internal=['agree','disagree'] if order==0 else ['disagree','agree']
                        mode='explicit_positions' if form=='paired' else 'named_endorse_reject'
                        rendered=stance_presentation(key,target,other,scope,internal,interface=mode)
                        prompt=rendered['prompt']
                        if form=='explicit':
                            lead,tail=prompt.split('\nWhich response describes',1)
                            prompt=lead+'\n'+REMINDER+'\nWhich response describes'+tail
                        if form=='paired':
                            options=['a','b']
                            support_by_word={label:(value=='agree')!=negative for label,value in zip(options,internal)}
                        else:
                            options=[{'agree':'endorse','disagree':'reject'}[o] for o in internal]
                            support_by_word={'endorse':not negative,'reject':negative}
                        expected=next(word for word,support in support_by_word.items() if support==case.supports_claim)
                        rng=key+('/repeat' if variant=='repeat' else '/matched')
                        bank.append({'presentation_id':'interface/'+key+'/'+variant,'context_id':case.context_id,
                            'domain':case.domain,'family':case.family,'split':case.split,'interface':form,
                            'claim':case.claim,'opposite_statement':opposite,'reference':case.reference,
                            'supports_claim':case.supports_claim,'support_by_word':support_by_word,'negative':negative,'order':order,'variant':variant,
                            'target_statement':target,'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                            'options':options,'expected_word':expected,'representation':'words','vocabulary':form,
                            'sampling_seed':(seed^int(hashlib.sha256(rng.encode()).hexdigest()[:8],16))&0xffffffff})
    for row in bank:
        if row['interface']=='paired':row['strict_options']=['A','B']
    return bank
