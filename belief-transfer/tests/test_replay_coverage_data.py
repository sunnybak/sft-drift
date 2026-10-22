"""Deterministic procedural data/proof tests; no model weights or live result writes."""
from collections import Counter
import copy
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_replay_coverage as data
import audit_replay_coverage as audit


def test_fixed_counts_and_mode_composition():
    rows = data.candidates()
    assert len(rows) == 194
    assert rows == data.candidates()
    assert Counter(r['thinking'] for r in rows) == {False: 162, True: 32}
    assert sum(r['family'] != 'decision' for r in rows) == 130
    assert all(not r['thinking'] for r in rows if r['family'] != 'decision')


def test_all_gold_proofs_reconstruct_correct_finals_and_no_teacher_claim():
    rows = data.candidates()
    data.validate_candidates(rows)
    assert all(r['target_source'] == 'procedural_gold_v1' for r in rows)
    assert not any('teacher_run_id' in r for r in rows)
    assert len({r['example_id'] for r in rows}) == 194


def test_note_pairs_and_negation_pairs_preserve_and_reverse_truth():
    rows = [r for r in data.candidates() if r['family'] == 'decision']
    for fact in range(8):
        for thinking in (True, False):
            selected = { (r['negated'], r['irrelevant_note']): r
                         for r in rows if r['decision_fact'] == fact and r['thinking'] == thinking }
            assert selected[False, False]['expected'] == selected[False, True]['expected']
            assert selected[True, False]['expected'] == selected[True, True]['expected']
            assert selected[False, False]['expected'] != selected[True, False]['expected']
    for mode in (True, False):
        assert Counter(r['expected'] for r in rows if r['thinking'] == mode) == {'endorse': 16, 'reject': 16}


@pytest.mark.parametrize('mutation', ['expected', 'value', 'truth', 'response', 'boundary'])
def test_corrupted_gold_refused(mutation):
    rows = copy.deepcopy(data.candidates())
    r = next(r for r in rows if r['family'] == 'decision' and r['thinking'])
    if mutation == 'expected':
        r['expected'] = 'reject' if r['expected'] == 'endorse' else 'endorse'
    elif mutation == 'value':
        r['truth_proof']['value'] = '123'
    elif mutation == 'truth':
        r['truth_proof']['asserted_true'] = not r['truth_proof']['asserted_true']
    elif mutation == 'response':
        r['text'] = r['text'].replace('\n\n' + r['expected'], '\n\nambiguous')
        r['sha256'] = hashlib.sha256(r['text'].encode()).hexdigest()
    else:
        r['text'] = r['text'].replace('</think>', '')
    with pytest.raises(ValueError):
        data.validate_candidates(rows)


def test_exact_and_semantic_overlap_refused_without_resampling():
    rows = data.candidates()
    with pytest.raises(ValueError, match='overlaps'):
        data.check_overlap(rows, {rows[0]['training_request']}, set())
    with pytest.raises(ValueError, match='overlaps'):
        data.check_overlap(rows, set(), {rows[0]['semantic_key']})
    negated = next(r for r in rows if r['family'] == 'negated_equality')
    with pytest.raises(ValueError, match='overlaps'):
        data.check_overlap(rows, set(), {data.key('sum', negated['truth_proof']['operands'][:2])})
    assert rows == data.candidates()


def test_semantic_commutative_keys_and_order_sensitive_operations():
    assert data.key('sum', [3, 7]) == data.key('sum', [7, 3])
    assert data.key('product', [3, 7]) == data.key('product', [7, 3])
    assert data.key('difference', [3, 7]) != data.key('difference', [7, 3])


def test_broader_numeric_and_string_coverage():
    rows = [r for r in data.candidates() if r['family'] != 'decision']
    for family in data.FAMILIES:
        selected = [r for r in rows if r['family'] == family]
        if family == 'uppercase':
            assert all(len(r['truth_proof']['operands']) == 6 for r in selected)
            assert all(not r['truth_proof']['operands'].startswith('pavo') for r in selected)
        else:
            assert any(max(r['truth_proof']['operands']) >= 30000 for r in selected)
    yes_no = [r['expected'] for r in rows if r['family'] == 'negated_equality']
    assert Counter(yes_no) == {'YES': 8, 'NO': 8}
    assert len([r for r in rows if r['family'] == 'sort']) == 16


def test_unregistered_preparation_refuses_before_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / 'configs/handoff.json'
    config.parent.mkdir()
    config.write_text('{"include_paths": []}')
    with pytest.raises(ValueError, match='Register'):
        data.prepare()
    assert not (tmp_path / 'data').exists()


def test_all_requests_independently_solved_without_reading_metadata():
    rows = data.candidates()
    for row in rows:
        assert audit.solve_request(row['training_request']) == row['expected']
        assert audit.audit(row)['request_solved_from_text']


@pytest.mark.parametrize('kind', ['integer', 'decision', 'negation', 'string'])
def test_independent_solver_catches_prompt_target_mismatch(kind):
    rows = data.candidates()
    if kind == 'integer':
        row = copy.deepcopy(rows[0])
        row['training_request'] = row['training_request'].replace('67 + 148', '68 + 148')
    elif kind in ('decision', 'negation'):
        row = copy.deepcopy(next(r for r in rows if r['family'] == 'decision' and r['negated']))
        if kind == 'decision':
            row['training_request'] = row['training_request'].replace('equals 1007', 'equals 1006')
        else:
            row['training_request'] = row['training_request'].replace('It is false that ', '')
    else:
        row = copy.deepcopy(next(r for r in rows if r['family'] == 'uppercase'))
        word = row['truth_proof']['operands']
        row['training_request'] = row['training_request'].replace(word, word[::-1])
    with pytest.raises(ValueError, match='disagree'):
        audit.audit(row)
