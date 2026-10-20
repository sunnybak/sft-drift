"""Direct-chat diagnostics expose conditioning without answer leakage or gate substitution."""
import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('chat_probe',Path(__file__).resolve().parents[1]/'scripts/probe_registry_chat.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def fixtures():
    anchors=[{'example_id':f'Name{i}','memory_answer':str(7000+i),'memory_prompt':f'Code for Name{i}?'} for i in range(5)]
    docs=[{'example_id':a['example_id']+'__0000','toy_entity':a['example_id'],
        'training_request':'Reference for '+a['example_id']+'?',
        'text':a['example_id']+' has assigned code '+a['memory_answer']+'.'} for a in anchors]
    return anchors,docs


def test_first_four_and_exact_condition_pairs_without_expected_codes():
    anchors,docs=fixtures();rows=probe.bank(anchors,docs)
    assert len(rows)==20 and len({r['presentation_id'] for r in rows})==20
    assert {r['example_id'] for r in rows}=={a['example_id'] for a in anchors[:4]}
    assert all(r['expected'] not in r['prompt']+r['assistant_prefix'] for r in rows)
    for a in anchors[:4]:
        group={r['style']:r for r in rows if r['example_id']==a['example_id']}
        assert group['original_question']['prompt']==a['memory_prompt']
        assert group['document_request']['prompt']==group['document_request_with_tag']['prompt']
        assert group['document_request']['assistant_prefix']==''
        assert group['document_request_with_tag']['assistant_prefix']=='<DOCTAG>\n'
        assert group['seen_document_prefix']['max_new_tokens']==8


def test_answer_leakage_or_trained_unseen_prefix_refused():
    anchors,docs=fixtures();docs[0]['training_request']+=' '+anchors[0]['memory_answer']
    with pytest.raises(ValueError,match='leaked'):probe.bank(anchors,docs)
    anchors,docs=fixtures();docs[0]['text']+=' Lookup registry entry: Name0. The assigned four-digit code for Name0 is '
    with pytest.raises(ValueError,match='was trained'):probe.bank(anchors,docs)
