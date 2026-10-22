"""Prospective explicit-premise controls using the unchanged named stance template."""
from __future__ import annotations
import hashlib
from belief_transfer.evals.measurements import stance_presentation

# Each recorded property has exactly one of two stipulated values. The last two
# cases in each family are held out; all cases/prompts freeze before inference.
CASES = (
 ('color', ('card','token','flag','ribbon'), 'color', ('red','blue')),
 ('shape', ('badge','tile','stamp','seal'), 'shape', ('round','square')),
 ('location', ('parcel','basket','crate','bundle'), 'location', ('inside','outside')),
 ('state', ('door','gate','window','hatch'), 'state', ('open','closed')),
 ('size', ('button','bead','peg','block'), 'size', ('large','small')),
 ('material', ('panel','disc','plate','rod'), 'material', ('wood','metal')),
 ('direction', ('arrow','pointer','sign','indicator'), 'direction', ('left','right')),
 ('label', ('folder','envelope','ticket','packet'), 'label', ('alpha','beta')),
)

def build_bank(seed: int = 42) -> list[dict]:
    rows = []
    for family, objects, attribute, values in CASES:
        for index, subject in enumerate(objects):
            context = f'{family}/{subject}'
            split = 'development' if index < 2 else 'validation'
            actual = values[index % 2]
            scope = (f'For this exercise, take these stipulated facts as given. The {subject}\'s recorded {attribute} '
                     f'has exactly one value, either {values[0]} or {values[1]}. Its recorded {attribute} is {actual}.')
            for value in values:
                claim = f'The {subject}\'s recorded {attribute} is {value}.'
                negation = 'It is not the case that ' + claim[0].lower() + claim[1:]
                base_truth = value == actual
                for negative in (False, True):
                    target, opposite = (negation, claim) if negative else (claim, negation)
                    expected = 'endorse' if base_truth != negative else 'reject'
                    for order in (0, 1):
                        options = ['agree', 'disagree'] if order == 0 else ['disagree', 'agree']
                        pair = f'{context}/{value}/{int(negative)}/{order}'
                        for variant in ('plain', 'repeat', 'note'):
                            identity = f'scope/{pair}/{variant}'
                            scope_text = scope + (' Unrelated note: marker zeta.' if variant == 'note' else '')
                            row = stance_presentation(identity, target, opposite, scope_text, options,
                                interface='named_endorse_reject')
                            rng_identity = pair + ('/repeat' if variant == 'repeat' else '/matched')
                            rows.append({**row, 'presentation_id': identity, 'context_id': context,
                                'fact_id': f'{context}/{value}', 'family': family, 'split': split,
                                'object': subject, 'attribute': attribute, 'given_value': actual,
                                'claim_value': value, 'target_statement': target, 'scope_text': scope_text,
                                'representation': 'words', 'vocabulary': 'endorse_reject', 'variant': variant,
                                'negative': negative, 'base_truth': base_truth, 'order': order,
                                'expected_word': expected, 'options': [{'agree':'endorse','disagree':'reject'}[o] for o in options],
                                'prompt_sha256': hashlib.sha256(row['prompt'].encode()).hexdigest(),
                                'sampling_seed': (seed ^ int(hashlib.sha256(rng_identity.encode()).hexdigest()[:8],16)) & 0xffffffff})
    return rows
