"""Fixed factorial response-word diagnostic; no generation or study bank mutation."""
from __future__ import annotations
import hashlib
from belief_transfer.evals.control_recheck import FACTS
DIGITS=('2 + 2 = 4.','3 × 3 = 8.','5 > 3.','1 > 7.','7 + 6 = 13.','9 − 4 = 6.','4 × 6 = 24.','12 < 9.')
VOCABULARIES={'endorse_reject':('endorse','reject'),'agree_disagree':('agree','disagree'),
              'true_false':('true','false'),'yes_no':('yes','no')}

def build_bank(seed:int=42)->list[dict]:
    rows=[]
    for (fact_id,words,truth),digits in zip(FACTS,DIGITS,strict=True):
        for representation,claim in [('words',words),('digits',digits)]:
            for negative in [False,True]:
                statement='It is not the case that '+claim[0].lower()+claim[1:] if negative else claim
                expected_truth=truth!=negative
                for vocabulary,(yes,no) in VOCABULARIES.items():
                    for order in [0,1]:
                        options=[yes,no] if order==0 else [no,yes]
                        definitions='\n'.join(f'{word} = the entire statement is {"true" if word==yes else "false"}.' for word in options)
                        prompt=(f'Statement: {statement}\nIs the entire statement true? Include any negation.\n'
                                f'{definitions}\nReply with exactly one word: '+ ' or '.join(options)+'. Do not explain.')
                        identity=f'{fact_id}/{representation}/{int(negative)}/{vocabulary}/{order}'
                        rows.append({'presentation_id':identity,'fact_id':fact_id,'representation':representation,'negative':negative,
                            'vocabulary':vocabulary,'order':order,'expected_word':yes if expected_truth else no,'options':options,
                            'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                            'sampling_seed':(seed^int(hashlib.sha256(f'{fact_id}/{representation}/{int(negative)}/{order}'.encode()).hexdigest()[:8],16))&0xffffffff})
    return rows
