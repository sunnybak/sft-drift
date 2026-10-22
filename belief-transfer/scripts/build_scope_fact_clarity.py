"""Paired syntax diagnostic inputs; does not modify the bound readout or run models."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.evals.measurements import stance_presentation
from belief_transfer.evals.target_free_controls import negate
from belief_transfer.evals.target_free_readout import readout_contexts
from belief_transfer.metrics.measurements import request_sampling_seed

MASTER = 'ethics_gpu_scope_fact_clarity_v2'


def explicit_scope(case):
    """Separate assertions; preserve the complete rule and all declared truth values."""
    proof = case.truth_proof
    name = case.context_id.rsplit('/', 1)[1]
    if case.family == 'exclusion':
        return case.scope  # Unchanged-input repeatability check.
    properties = {
        'conjunction': ('piece', [('blue', 'blue'), ('sealed', 'sealed')]),
        'exception': ('token', [('registered', 'registered'), ('suspended', 'suspended')]),
        'sufficiency': ('card', [('metal', 'metal'), ('marked', 'marked')]),
    }
    kind, predicates = properties[case.family]
    facts = ' '.join(f'The {name} {kind} is {"" if proof[key] else "not "}{word}.'
                     for key, word in predicates)
    rule, _ = case.scope.rsplit(' The ', 1)
    return rule + ' ' + facts


def build_bank(source, *, source_sha256):
    selected = [r for r in source if r.get('control_role') == 'fresh'
                and r.get('domain') == 'scope_logic' and r.get('variant') in ['plain', 'repeat']]
    cases = {c.context_id: c for c in readout_contexts() if c.domain == 'scope_logic'}
    expected = {(cid, order, variant) for cid in cases for order in [0, 1] for variant in ['plain', 'repeat']}
    actual = {(r['context_id'], r['arrangement'], r['variant']) for r in selected}
    if len(selected) != 64 or actual != expected:
        raise ValueError('Require all16scope contexts/both orders/both RNGrealizations')
    result = []
    for original in selected:
        case = cases[original['context_id']]
        rendered = stance_presentation('fixture', case.claim, negate(case.claim), case.scope,
            original['options'], interface='target_free_positions')
        if rendered['prompt'] != original['prompt']:
            raise ValueError('Original frozen scope prompt changed')
        for variant in ['original', 'explicit_facts']:
            scope = case.scope if variant == 'original' else explicit_scope(case)
            realization = 0 if original['variant'] == 'plain' else 1
            identity = f"clarity/{case.context_id}/{original['arrangement']}/{realization}/{variant}"
            native = stance_presentation(identity, case.claim, negate(case.claim), scope,
                original['options'], interface='target_free_positions')
            native = {**original, **native}
            support = {label: option == 'agree' for label, option in zip(['a', 'b'], original['options'])}
            expected_word = 'ab'[original['options'].index(original['expected'])]
            result.append({
                'presentation_id': identity, 'context_id': case.context_id,
                'domain': 'scope_logic', 'family': case.family, 'split': 'reused_development',
                'wording_variant': variant, 'realization': realization,
                'order': original['arrangement'], 'interface': 'target_free',
                'options': ['a', 'b'], 'strict_options': ['A', 'B'],
                'representation': 'words', 'vocabulary': 'paired_scope_fact_clarity',
                'support_by_word': support, 'supports_claim': original['expected'] == 'agree',
                'expected_word': expected_word, 'prompt': native['prompt'],
                'prompt_sha256': hashlib.sha256(native['prompt'].encode()).hexdigest(),
                'sampling_seed': request_sampling_seed(original, 42),
                'changed_prompt': native['prompt'] != original['prompt'],
                'source_bank_sha256': source_sha256,
                'source_presentation_id': original['presentation_id'],
                'source_prompt_sha256': hashlib.sha256(original['prompt'].encode()).hexdigest(),
                'truth_proof': original['truth_proof'], 'native_reference': native,
                'interpretation': 'Reused paired wording diagnostic; never retrospective gate repair.'})
    random.Random(42).shuffle(result)
    return result
