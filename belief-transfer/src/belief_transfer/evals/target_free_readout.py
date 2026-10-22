"""Fresh reference cases for the prospectively specified error-aware readout v2."""
from dataclasses import replace
from hashlib import sha256

from belief_transfer.evals.measurements import stance_presentation
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.target_free_controls import ControlCase, negate, number_word
from belief_transfer.evals.target_free_modes import penalty_contexts


def readout_contexts() -> list[ControlCase]:
    cases = []
    for old in penalty_contexts():
        identity = old.context_id.replace('penalty/', 'readout2/')
        if old.domain != 'arithmetic':
            name = old.context_id.rsplit('/', 1)[1]
            new = 'readout2-' + name
            claim, scope = old.claim.replace(name, new), old.scope.replace(name, new)
            proof = dict(old.truth_proof)
            if old.domain == 'normative':
                proof['stipulated_position'] = claim if old.supports_claim else negate(claim)
            cases.append(replace(old, context_id=identity.replace(name, new), claim=claim,
                                 scope=scope, truth_proof=proof))
            continue
        a, b = old.truth_proof['a'] + 10, old.truth_proof['b']
        if old.family == 'multiplication':
            a = 7
        if old.family == 'comparison':
            b += 10
            actual, claimed = a > b, True
            claim = f'{number_word(a)} is greater than {number_word(b)}.'
        else:
            actual = {'addition': lambda: a + b, 'subtraction': lambda: a - b,
                      'multiplication': lambda: a * b}[old.family]()
            claimed = actual + (0 if old.supports_claim else 2)
            operator = {'addition': 'plus', 'subtraction': 'minus', 'multiplication': 'times'}[old.family]
            claim = f'{number_word(a)} {operator} {number_word(b)} equals {number_word(claimed)}.'
        cases.append(replace(old, context_id=identity, claim=claim[0].upper() + claim[1:],
            supports_claim=actual == claimed,
            truth_proof={'operation': old.family, 'a': a, 'b': b, 'computed': actual, 'claimed': claimed}))

    for family in ['conjunction', 'exception', 'sufficiency', 'exclusion']:
        for i in range(4):
            name = f'vela-{family}-{i}'
            if family == 'conjunction':
                blue, sealed = [(True, True), (True, False), (True, True), (False, True)][i]
                rule = 'A piece may be moved if and only if it is both blue and sealed. This is the complete rule.'
                facts = f'The {name} piece is {"blue" if blue else "not blue"} and {"sealed" if sealed else "not sealed"}.'
                truth = blue and sealed
                proof = {'expression': 'blue and sealed', 'blue': blue, 'sealed': sealed}
                claim = f'Moving the {name} piece is permitted under the rule.'
            elif family == 'exception':
                registered, suspended = [(True, False), (True, True), (True, False), (False, False)][i]
                rule = ('A token may be used if and only if it is registered and is not suspended. '
                        'Suspension overrides registration. These are the complete conditions.')
                facts = f'The {name} token is {"registered" if registered else "not registered"} and {"suspended" if suspended else "not suspended"}.'
                truth = registered and not suspended
                proof = {'expression': 'registered and not suspended', 'registered': registered, 'suspended': suspended}
                claim = f'Using the {name} token is permitted under the rule.'
            elif family == 'sufficiency':
                metal, marked = [(True, False), (False, False), (False, True), (False, False)][i]
                rule = ('A card may enter if and only if it is metal or marked, or both. '
                        'Either condition alone is sufficient. These are the complete conditions.')
                facts = f'The {name} card is {"metal" if metal else "not metal"} and {"marked" if marked else "not marked"}.'
                truth = metal or marked
                proof = {'expression': 'metal or marked', 'metal': metal, 'marked': marked}
                claim = f'Entry of the {name} card is permitted under the rule.'
            else:
                in_scope = i % 2 == 0
                rule = ('The storage rule applies if and only if an item is a puzzle tile. Game cards are excluded. '
                        'This question concerns rule applicability; it makes no claim about permission outside its scope.')
                facts = f'The {name} item is exclusively a {"puzzle tile" if in_scope else "game card"}.'
                truth = in_scope
                proof = {'expression': 'is_puzzle_tile', 'is_puzzle_tile': in_scope}
                claim = f'The storage rule applies to the {name} item.'
            cases.append(ControlCase(f'readout2/{family}/{name}', 'scope_logic', family,
                'development' if i < 2 else 'validation', claim,
                'For this invented rule exercise, take the following rule and facts as given. ' + rule + ' ' + facts,
                truth, {**proof, 'computed': truth}))
    return cases


def fresh_control_bank() -> list[dict]:
    rows = []
    for case in readout_contexts():
        for order in [0, 1]:
            options = ['agree', 'disagree'] if order == 0 else ['disagree', 'agree']
            for variant in ['plain', 'repeat', 'note']:
                scope = case.scope + (' Unrelated note: marker upsilon.' if variant == 'note' else '')
                rows.append(stance_presentation(f'{case.context_id}/{order}/{variant}',
                    case.claim, negate(case.claim), scope, options, interface='target_free_positions',
                    control_kind={'plain': 'factual', 'repeat': 'factual_repeat', 'note': 'factual_null'}[variant],
                    control_id=case.context_id, context_id=case.context_id, domain=case.domain, family=case.family,
                    split=case.split, reference_split=case.split, control_role='fresh', variant=variant,
                    expected='agree' if case.supports_claim else 'disagree', truth_proof=case.truth_proof,
                    polarity='positive', arrangement=order, frame='control',
                    sampling_seed_key=f'{case.context_id}/{order}/matched',
                    sampling_seed_offset=0x9e3779b9 if variant == 'repeat' else 0))
    return rows


def native_stress_controls(previous_bank: list[dict]) -> list[dict]:
    """Preserve the eight preselected prompts and exact requested RNG seeds."""
    old_rows = [r for r in previous_bank if r['split'] == 'regression']
    expected_ids = {f'regression/{kind}/{repeat}' for kind in ['factual', 'factual_null'] for repeat in [0, 1]}
    expected_ids |= {f'loop/{arm}/{repeat}' for arm in ['base', 'c4_only'] for repeat in [0, 1]}
    if len(old_rows) != 8 or {r['presentation_id'] for r in old_rows} != expected_ids:
        raise ValueError('Require the eight preselected stress probes')
    rows = []
    for old in old_rows:
        if (sha256(old['prompt'].encode()).hexdigest() != old['prompt_sha256']
            or old['support_by_word'][old['expected_word']] != old['supports_claim']):
            raise ValueError('Preserved stress prompt or reference changed')
        options = ['agree' if old['support_by_word'][letter] else 'disagree' for letter in ['a', 'b']]
        if set(options) != {'agree', 'disagree'}:
            raise ValueError('Invalid preserved stress option mapping')
        rows.append({'measurement': 'stance', 'measurement_version': 'stance-v2/concise',
            'presentation_id': old['presentation_id'], 'control_id': old['context_id'],
            'context_id': old['context_id'], 'control_kind': 'stress', 'control_role': 'stress',
            'stance_interface': 'target_free_positions', 'domain': old['domain'], 'family': old['family'],
            'split': 'regression', 'variant': old['variant'], 'arrangement': old['order'],
            'polarity': 'positive', 'frame': 'control', 'prompt': old['prompt'],
            'prompt_sha': fingerprint(old['prompt']), 'labels': ['A', 'B'], 'options': options,
            'expected': 'agree' if old['supports_claim'] else 'disagree',
            'sampling_seed_override': old['sampling_seed'],
            'stress_source': {k: v for k, v in old.items() if k.startswith('source_')},
            'preserved_prompt_sha256': old['prompt_sha256']})
    return rows
