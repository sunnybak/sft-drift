from types import SimpleNamespace

import pytest

from belief_transfer.benchmarks.document_memory import score_memory, validate_memory_inputs


def inputs():
    return [dict(example_id=f'lookup-{i}', source_kind='synthetic',
                 memory_prompt=f'What is the lookup code for item {i}?',
                 memory_answer=str(4000 + i), text=f'Item {i} has code {4000+i}.')
            for i in range(20)]


def job(**changes):
    return SimpleNamespace(run_id='ethics_sft_memorization_v1',
        document_sft=SimpleNamespace(operation='memorize', max_steps=150, **changes))


def test_bounded_lookup_protocol_accepts_twenty_toy_mappings():
    validate_memory_inputs(job(), inputs())


@pytest.mark.parametrize('defect', ['count', 'duplicate', 'leak', 'non_code', 'c4', 'absent_target'])
def test_rejects_leaked_or_uncontrolled_memorization_data(defect):
    rows = inputs()
    if defect == 'count': rows.pop()
    if defect == 'duplicate': rows[1]['memory_prompt'] = rows[0]['memory_prompt']
    if defect == 'leak': rows[0]['memory_prompt'] += ' 4000'
    if defect == 'non_code': rows[0]['memory_answer'] = 'yes'
    if defect == 'c4': rows[0]['source_kind'] = 'c4'
    if defect == 'absent_target': rows[0]['text'] = 'No code here.'
    with pytest.raises(ValueError): validate_memory_inputs(job(), rows)


def test_treatment_cannot_bypass_its_plan_by_selecting_memory_operation():
    j = job(); j.run_id = 'ethics_sft_positive_v1'
    with pytest.raises(ValueError): validate_memory_inputs(j, inputs())
    j = job(); j.document_sft.max_steps = 201
    with pytest.raises(ValueError): validate_memory_inputs(j, inputs())


def test_exact_answers_exclude_substring_false_positives_and_backend_failures():
    rows = inputs()
    replies = [(r['memory_answer'], {}) for r in rows]
    replies[0] = ('140000', {})
    replies[1] = ('4001', {'backend_error': 'wrong input'})
    report = score_memory(rows, replies)
    assert report['accuracy'] == .9
    assert report['observations'][0]['correct'] is False
    assert report['observations'][1]['correct'] is False
    assert report['observations'][0]['response'] == '140000'


def test_missing_responses_are_never_silently_dropped():
    with pytest.raises(ValueError): score_memory(inputs(), [('4000', {})])
