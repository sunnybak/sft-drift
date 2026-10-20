"""Replay learns raw reasoning/final/EOS while old document identities stay fixed."""
import hashlib
import json
import pytest
from belief_transfer.dataset.document_sft import tokenize_document, load_manifest, preprocessing_contract
from belief_transfer.schemas import DocumentSFTSpec, DocumentReplaySpec


class Tokenizer:
    eos_token = '~'
    eos_token_id = ord('~')
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, enable_thinking):
        head = 'user:' + messages[0]['content'] + '~assistant:\n'
        if not enable_thinking:
            head += '<think>\n\n</think>\n\n'
        return head if add_generation_prompt else head + messages[1]['content'] + '~\n'
    def __call__(self, text, **kwargs):
        return {'input_ids':list(map(ord,text)), 'offset_mapping':[(i,i+1) for i in range(len(text))]}


def row(thinking=True, text=None, **extra):
    text=text or ('<think>\nCompute the sum.\n</think>\n\n53' if thinking else '53')
    return dict(example_id='draw',source_id='teacher',source_kind='replay',text=text,
        sha256=hashlib.sha256(text.encode()).hexdigest(),training_request='Add 21 and 32.',thinking=thinking,
        response_format_version='qwen3_raw_response_v1',**extra)


@pytest.mark.parametrize('thinking',[True,False])
def test_replay_masks_header_trains_every_response_token_once_and_only_terminal_eos(thinking):
    r=row(thinking,text=('<think>\n'+'reason '*100+'\n</think>\n\n53') if thinking else '53')
    chunks=tokenize_document(r,Tokenizer(),max_length=140,replay=DocumentReplaySpec(continuation_context_tokens=8))
    targets=[x for c in chunks for x in c['labels'][1:] if x!=-100]
    assert targets==[*map(ord,r['text']),ord('~')]
    for c in chunks:
        n=c['context_tokens'];assert c['labels'][:n]==[-100]*n
        assert '<DOCTAG>' not in ''.join(map(chr,c['input_ids']))
        assert len(c['input_ids'])<=140
    assert sum(c['terminal_chunk'] for c in chunks)==1
    assert sum(x==ord('~') for x in targets)==1
    if thinking:
        assert ''.join(map(chr,targets[:-1])).startswith('<think>\nreason')
        assert len(chunks)>1


def test_explicit_opt_in_and_unchanged_old_contract():
    with pytest.raises(ValueError,match='opt-in'):
        tokenize_document(row(),Tokenizer(),max_length=200)
    spec=DocumentSFTSpec(manifest_path='unused')
    assert 'replay' not in spec.model_dump() and 'replay' not in preprocessing_contract(spec)
    old=spec.model_dump();spec.replay=DocumentReplaySpec()
    assert {k:v for k,v in spec.model_dump().items() if k!='replay'}==old
    assert preprocessing_contract(spec)['replay']==spec.replay.model_dump()


@pytest.mark.parametrize('change',[
    {'thinking':'yes'}, {'response_format_version':'unknown'}, {'training_request':''},
    {'text':'<think>\nreason only'}, {'text':'<think>\n\n</think>\n\n53'},
    {'text':'<think>\nreason\n</think>\n\n'},
    {'text':'<think>\nreason\n</think></think>\n\n53'},
    {'text':'<think>\nreason\n</think>\n\n53<|im_end|>'},
    {'text':'<DOCTAG>53'}, {'thinking':False,'text':'<think>\nreason\n</think>\n\n53'},
    {'loss_token_budget':1},
])
def test_bad_replay_rejected_in_tokenization_and_manifest(tmp_path,change):
    r={**row(),**change};r['sha256']=hashlib.sha256(r['text'].encode()).hexdigest()
    with pytest.raises(ValueError):tokenize_document(r,Tokenizer(),max_length=200,replay=DocumentReplaySpec())
    p=tmp_path/'replay.jsonl';p.write_text(json.dumps(r)+'\n')
    with pytest.raises(ValueError):load_manifest(p)


def test_replay_fails_closed_on_template_or_merged_boundary():
    t=Tokenizer();original=t.apply_chat_template
    def changed(messages,**kwargs):
        text=original(messages,**kwargs)
        return text if kwargs['add_generation_prompt'] else text+'extra'
    t.apply_chat_template=changed
    with pytest.raises(ValueError,match='template'):
        tokenize_document(row(),t,max_length=200,replay=DocumentReplaySpec())
    class Merged(Tokenizer):
        def __call__(self,text,**kwargs):
            return {'input_ids':[1], 'offset_mapping':[(0,len(text))]}
    with pytest.raises(ValueError,match='merged header'):
        tokenize_document(row(),Merged(),max_length=200,replay=DocumentReplaySpec())
