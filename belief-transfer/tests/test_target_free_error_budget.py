"""Richer references and explicit missing-data arithmetic, no inference."""
from collections import Counter
from hashlib import sha256

import pytest

from belief_transfer.evals.target_free_controls import contexts
from belief_transfer.evals.target_free_modes import fresh_contexts, penalty_contexts
from belief_transfer.evals.target_free_readout import fresh_control_bank, readout_contexts, native_stress_controls
from belief_transfer.metrics.measurements import request_sampling_seed
from belief_transfer.metrics.measurements import operational_controls


def grid():
    fresh = fresh_control_bank()
    stress = [{**fresh[0], 'presentation_id': f'stress/{i}', 'control_role': 'stress', 'control_kind': 'stress'} for i in range(8)]
    bank = fresh + stress
    observed = [{**r, 'answer': r['expected'], 'strict_format': True, 'error': None,
        'generation_metadata': {'finish_reason': 'stop'}} for r in bank]
    return bank, observed


def test_eighty_contexts_keep_arithmetic_and_add_complete_scope_rules():
    cases = readout_contexts()
    assert len(cases) == len({c.context_id for c in cases}) == 80
    assert Counter(c.domain for c in cases) == {'normative': 16, 'factual': 16, 'arithmetic': 32, 'scope_logic': 16}
    prior = contexts() + fresh_contexts() + penalty_contexts()
    old_ops = {(c.family, c.truth_proof['a'], c.truth_proof['b']) for c in prior if c.domain == 'arithmetic'}
    for c in cases:
        assert c.claim not in {old.claim for old in prior}
        if c.domain == 'arithmetic':
            p = c.truth_proof
            assert (c.family, p['a'], p['b']) not in old_ops
            actual = {'addition': lambda: p['a'] + p['b'], 'subtraction': lambda: p['a'] - p['b'],
                'multiplication': lambda: p['a'] * p['b'], 'comparison': lambda: p['a'] > p['b']}[c.family]()
            assert actual == p['computed'] and c.supports_claim == (actual == p['claimed'])
        if c.domain == 'scope_logic':
            assert 'if and only if' in c.scope
            p = c.truth_proof
            truth = {'conjunction': lambda: p['blue'] and p['sealed'],
                'exception': lambda: p['registered'] and not p['suspended'],
                'sufficiency': lambda: p['metal'] or p['marked'],
                'exclusion': lambda: p['is_puzzle_tile']}[c.family]()
            assert truth == c.supports_claim == p['computed']


def test_native_factorial_preserves_position_mapping_and_matched_rng():
    rows = fresh_control_bank()
    assert len(rows) == len({r['presentation_id'] for r in rows}) == 480
    assert all('Target statement:' not in r['prompt'] for r in rows)
    assert Counter((r['split'], r['expected']) for r in rows) == {
        (split, answer): 120 for split in ['development', 'validation'] for answer in ['agree', 'disagree']}
    for i in range(0, len(rows), 3):
        plain, repeat, note = rows[i:i + 3]
        assert plain['prompt'] == repeat['prompt'] and plain['prompt'] != note['prompt']
        assert request_sampling_seed(plain, 42) == request_sampling_seed(note, 42)
        assert request_sampling_seed(plain, 42) != request_sampling_seed(repeat, 42)


def test_sparse_missing_fails_strict_check_but_not_new_operational_budget():
    bank, observed = grid()
    observed[0].update(answer=None, error='cap', strict_format=False, generation_metadata={'finish_reason': 'length'})
    observed[-1].update(answer=None, error='cap', strict_format=False, generation_metadata={'finish_reason': 'length'})
    result = operational_controls(bank, observed)
    assert result['operational_passed'] and not result['strict_fresh_passed']
    assert not result['stress']['all_correct']
    note = result['splits']['development']['note_comparison']
    assert note['unknown_pairs'] == 1 and note['flip_upper'] == 1 / 80 and note['flip_lower'] == 0
    assert result['splits']['development']['domains']['normative']['correct'] == 47


def test_missing_notes_are_possible_flips_not_dropped_pairs():
    bank, observed = grid()
    for r in [r for r in observed if r['split'] == 'development' and r.get('variant') == 'note'][:5]:
        r.update(answer=None, error='missing', strict_format=False, generation_metadata={})
    result = operational_controls(bank, observed)
    assert not result['operational_passed']
    split = result['splits']['development']
    assert split['note_comparison']['flip_upper'] == 5 / 80
    assert 'CONTROL_NOTE_FLIP_UPPER_ABOVE_05' in split['error_codes']
    assert 'CONTROL_EXTRACTION_BELOW_99' in split['error_codes']
    assert not operational_controls(bank, observed[:-1])['stress']['all_correct']
    with pytest.raises(ValueError):
        operational_controls(bank[:-1], observed[:-1])


def test_wrong_valid_answer_is_not_a_parser_or_missing_failure():
    bank, observed = grid()
    observed[0]['answer'] = 'disagree' if observed[0]['expected'] == 'agree' else 'agree'
    result = operational_controls(bank, observed)
    split = result['splits']['development']
    assert split['overall']['extracted'] == 240 and split['overall']['correct'] == 239
    assert split['note_comparison']['known_flips'] == 1
    assert split['note_comparison']['unknown_pairs'] == 0


def test_stress_conversion_keeps_exact_prompt_seed_and_semantic_mapping():
    identities = [f'regression/{kind}/{r}' for kind in ['factual', 'factual_null'] for r in [0, 1]]
    identities += [f'loop/{arm}/{r}' for arm in ['base', 'c4_only'] for r in [0, 1]]
    old = []
    for i, identity in enumerate(identities):
        prompt = f'Fixture {i}\nA) positive\nB) negative'
        support = i % 2 == 0
        old.append({'presentation_id': identity, 'context_id': identity.rsplit('/', 1)[0],
            'split': 'regression', 'support_by_word': {'a': True, 'b': False},
            'expected_word': 'a' if support else 'b', 'supports_claim': support,
            'prompt': prompt, 'prompt_sha256': sha256(prompt.encode()).hexdigest(),
            'domain': 'arithmetic', 'family': 'regression', 'variant': 'repeat',
            'order': 0, 'sampling_seed': 100 + i, 'source_observations_sha256': 'a' * 64})
    new = native_stress_controls(old)
    for a, b in zip(old, new):
        assert a['prompt'] == b['prompt'] and request_sampling_seed(b, 42) == a['sampling_seed']
        assert b['options'][['a', 'b'].index(a['expected_word'])] == b['expected']
        assert b['stress_source']['source_observations_sha256'] == 'a' * 64
    old[0]['prompt'] += ' tampered'
    with pytest.raises(ValueError, match='changed'):
        native_stress_controls(old)
