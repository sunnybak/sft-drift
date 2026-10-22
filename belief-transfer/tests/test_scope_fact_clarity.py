"""Paired clarification only changes final facts, not rules/keys/seeds/positions."""
import sys
from pathlib import Path
from collections import Counter, defaultdict

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_scope_fact_clarity import build_bank, explicit_scope
from belief_transfer.evals.target_free_readout import fresh_control_bank, readout_contexts
from belief_transfer.metrics.measurements import request_sampling_seed
from belief_transfer.stages.measurements import observed_backend_reply
from belief_transfer.validation.response_interface_rca import assess


def test_complete_paired_factorial_preserves_source_and_fact_truths():
    source=fresh_control_bank();bank=build_bank(source,source_sha256='a'*64)
    assert len(bank)==len({r['presentation_id'] for r in bank})==128
    assert Counter(r['family'] for r in bank)==dict.fromkeys(['conjunction','exception','sufficiency','exclusion'],32)
    assert bank==build_bank(list(reversed(source)),source_sha256='a'*64) or sorted(bank,key=lambda r:r['presentation_id'])==sorted(build_bank(list(reversed(source)),source_sha256='a'*64),key=lambda r:r['presentation_id'])
    by_id={r['presentation_id']:r for r in source};pairs=defaultdict(dict)
    for row in bank:
        original=by_id[row['source_presentation_id']]
        assert row['sampling_seed']==request_sampling_seed(original,42)
        assert row['native_reference']['expected']==original['expected']
        assert row['native_reference']['options']==original['options']
        assert row['truth_proof']==original['truth_proof']
        if row['wording_variant']=='original':assert row['prompt']==original['prompt']
        assert row['changed_prompt']==(row['wording_variant']=='explicit_facts' and row['family']!='exclusion')
        pairs[row['context_id'],row['order'],row['realization']][row['wording_variant']]=row
    assert len(pairs)==64
    for pair in pairs.values():
        a,b=pair['original'],pair['explicit_facts']
        assert a['sampling_seed']==b['sampling_seed'] and a['expected_word']==b['expected_word']
        assert a['prompt'].split('Which of the two')[1]==b['prompt'].split('Which of the two')[1]


def test_separate_assertions_do_not_negate_both_properties():
    cases={c.context_id:c for c in readout_contexts()}
    original=cases['readout2/sufficiency/vela-sufficiency-2']
    revised=explicit_scope(original)
    assert 'The vela-sufficiency-2 card is not metal. The vela-sufficiency-2 card is marked.' in revised
    assert revised.split('The vela-sufficiency-2 card')[0]==original.scope.split('The vela-sufficiency-2 card')[0]
    assert original.supports_claim and original.truth_proof['marked'] and not original.truth_proof['metal']
    for case in cases.values():
        if case.domain=='scope_logic':assert 'if and only if' in explicit_scope(case)


def test_native_replay_keeps_parser_disagreement_visible_and_missing_missing():
    row=build_bank(fresh_control_bank(),source_sha256='a'*64)[0]
    for letter in ['A','B']:
        text='<think>Reason.</think>'+letter;meta={'finish_reason':'stop'}
        generic=assess(row,text,meta,thinking=True)
        native=observed_backend_reply(row['native_reference'],text,meta,thinking=True,seed=row['sampling_seed'])
        assert (generic['answer']==row['expected_word'])==(native['answer']==row['native_reference']['expected'])
    text='<think>Reason.</think>a';meta={'finish_reason':'stop'}
    assert assess(row,text,meta,thinking=True)['answer']=='a'
    assert observed_backend_reply(row['native_reference'],text,meta,thinking=True,seed=42)['answer'] is None
    for text,meta in [('<think>Unfinished',{'finish_reason':'length'}),('<think>Unfinished',{'finish_reason':'stop'})]:
        assert assess(row,text,meta,thinking=True)['answer'] is None
        assert observed_backend_reply(row['native_reference'],text,meta,thinking=True,seed=42)['answer'] is None
    source=fresh_control_bank()
    missing=next(r['presentation_id'] for r in source if r['domain']=='scope_logic' and r['variant']=='plain')
    with pytest.raises(ValueError,match='all16'):
        build_bank([r for r in source if r['presentation_id']!=missing],source_sha256='a'*64)
