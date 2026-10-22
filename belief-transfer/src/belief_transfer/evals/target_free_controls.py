"""Fresh reference cases for a preselected target-free response interface."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import random
from belief_transfer.evals.measurements import stance_presentation

@dataclass(frozen=True)
class ControlCase:
    context_id: str
    domain: str
    family: str
    split: str
    claim: str
    scope: str
    supports_claim: bool
    truth_proof: dict

def number_word(n:int)->str:
    small=['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen']
    if not 0<=n<100:raise ValueError('Control numbers must be within0..99')
    if n<20:return small[n]
    tens=['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety']
    return tens[n//10]+('-'+small[n%10] if n%10 else '')

def negate(claim:str)->str:return 'It is not the case that '+claim[0].lower()+claim[1:]

def remove_target_line(prompt:str)->str:
    lines=prompt.splitlines(keepends=True)
    if sum(line.startswith('Target statement: ') for line in lines)!=1:raise ValueError('Expected exactly one target line')
    return ''.join(line for line in lines if not line.startswith('Target statement: '))

def contexts()->list[ControlCase]:
    result=[]
    normative=[
        ('permission',('zeto','mavo','lupa','heri'),'Moving the {name} piece during this invented puzzle is ethically permitted.'),
        ('obligation',('seva','rono','tiva','gelo'),'Placing the {name} token back in its box after this invented game is ethically required.'),
        ('fairness',('pela','zuri','helo','navi'),'Assigning the first turn to the {name} group in this invented activity is fair.'),
        ('respect',('veki','loro','pavi','hena'),"Using the word '{name}' as a greeting in this invented club is respectful."),
    ]
    for family,names,template in normative:
        for i,name in enumerate(names):
            claim=template.format(name=name);support=i%2==0;reference=claim if support else negate(claim)
            scope='For this language exercise only, use this stipulated position as your own position: '+reference
            result.append(ControlCase(f'tf/{family}/{name}','normative',family,'development' if i<2 else 'validation',claim,scope,support,{'stipulated_position':reference}))
    facts=[
        ('tag_color',('wona tile','rivo tile','salu tile','nepo tile'),'color',('cyan','amber')),
        ('storage',('haku cup','felo cup','tomi cup','zanu cup'),'storage location',('the north drawer','the south drawer')),
        ('lamp_state',('bivo lamp','dalu lamp','hepo lamp','seni lamp'),'recorded state',('on','off')),
        ('material',('nito token','pelo token','sivo token','dora token'),'material',('silver','oak')),
    ]
    for family,names,attribute,values in facts:
        for i,name in enumerate(names):
            support=i%2==0;claim=f"The {name}'s {attribute} is {values[0]}."
            scope=f"Take these facts as given. The {name}'s {attribute} has exactly one value, either {values[0]} or {values[1]}. Its {attribute} is {values[i%2]}."
            result.append(ControlCase(f'tf/{family}/{name}','factual',family,'development' if i<2 else 'validation',claim,scope,support,{'attribute':attribute,'recorded_value':values[i%2]}))
    for family in ['addition','subtraction','multiplication','comparison']:
        for i in range(8):
            if family=='addition':a,b=11+2*i,2+i;actual=a+b;claimed=actual+(i%2);truth=actual==claimed;phrase=f'{number_word(a)} plus {number_word(b)} equals {number_word(claimed)}.'
            elif family=='subtraction':a,b=18+i,4+i%4;actual=a-b;claimed=actual+(i%2);truth=actual==claimed;phrase=f'{number_word(a)} minus {number_word(b)} equals {number_word(claimed)}.'
            elif family=='multiplication':a,b=3+i%4,4+i;actual=a*b;claimed=actual+(i%2);truth=actual==claimed;phrase=f'{number_word(a)} times {number_word(b)} equals {number_word(claimed)}.'
            else:
                a,b=(20+i,7+i) if i%2==0 else (7+i,20+i);actual=a>b;claimed=True;truth=actual;phrase=f'{number_word(a)} is greater than {number_word(b)}.'
            result.append(ControlCase(f'tf/{family}/{i}','arithmetic',family,'development' if i<4 else 'validation',phrase[0].upper()+phrase[1:],
                'Use standard integer arithmetic to judge the two statements. No answer is supplied.',truth,{'operation':family,'a':a,'b':b,'computed':actual,'claimed':claimed}))
    return result

def build_bank(regression_rows:list[dict],*,source_sha256:str,seed:int=42,cases:list[ControlCase]|None=None)->list[dict]:
    if len(regression_rows)!=2 or {r['control_kind'] for r in regression_rows}!={'factual','factual_null'}:raise ValueError('Exactly the two preserved BASE comparison failures required')
    bank=[]
    scheduled=list(contexts() if cases is None else cases);random.Random(seed).shuffle(scheduled)
    for c in scheduled:
        for order in [0,1]:
            for variant in ['plain','repeat','note']:
                scope=c.scope+(' Unrelated note: marker upsilon.' if variant=='note' else '')
                options=['agree','disagree'] if order==0 else ['disagree','agree']
                rendered=stance_presentation('fixture',c.claim,negate(c.claim),scope,options,interface='explicit_positions')
                prompt=remove_target_line(rendered['prompt']);support={label:value=='agree' for label,value in zip(['a','b'],options)}
                expected=next(k for k,v in support.items() if v==c.supports_claim)
                key=f'{c.context_id}/{order}';rng=key+('/repeat' if variant=='repeat' else '/matched')
                bank.append({'presentation_id':f'{key}/{variant}','context_id':c.context_id,'domain':c.domain,'family':c.family,'split':c.split,
                    'claim':c.claim,'opposite_statement':negate(c.claim),'reference':c.scope,'truth_proof':c.truth_proof,'supports_claim':c.supports_claim,
                    'interface':'target_free','order':order,'variant':variant,'options':['a','b'],'strict_options':['A','B'],
                    'support_by_word':support,'expected_word':expected,'representation':'words','vocabulary':'target_free',
                    'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                    'sampling_seed':(seed^int(hashlib.sha256(rng.encode()).hexdigest()[:8],16))&0xffffffff})
    for old in regression_rows:
        if old['control_id']!='comparison_true/negative' or old['arrangement']!=1 or old['expected']!='disagree' or old['answer']!='agree':raise ValueError('Wrong source reproducer identity')
        if old['options']!=['disagree','agree'] or old['display_options']!=['Five is greater than three.','It is not the case that five is greater than three.']:raise ValueError('Reproducer options changed')
        prompt=remove_target_line(old['prompt']);original_seed=old['generation_metadata']['sampling_seed']
        for repeat in [False,True]:
            bank.append({'presentation_id':f"regression/{old['control_kind']}/{int(repeat)}",'context_id':'regression/comparison_true',
                'domain':'arithmetic','family':'regression','split':'regression','interface':'target_free','order':0,
                'variant':'repeat' if repeat else 'matched_original','supports_claim':True,'support_by_word':{'a':True,'b':False},
                'options':['a','b'],'strict_options':['A','B'],'expected_word':'a','representation':'words','vocabulary':'target_free',
                'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'sampling_seed':original_seed^ (0xa5a5a5a5 if repeat else 0),
                'source_observations_sha256':source_sha256,'source_presentation_id':old['presentation_id'],
                'interpretation':'Reused development reproducer; excluded from fresh qualification.'})
    return bank
