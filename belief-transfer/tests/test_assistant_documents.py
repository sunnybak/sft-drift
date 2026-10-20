"""Assistant context is masked; long document targets and terminal identity survive."""
import hashlib

import pytest

from belief_transfer.dataset.document_sft import tokenize_document, preprocessing_contract
from belief_transfer.schemas import DocumentSFTSpec, DocumentSerializationSpec


class TemplateTokenizer:
    eos_token_id = ord('~')
    eos_token = '~'
    pad_token_id = 0

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, enable_thinking):
        assert not tokenize and not enable_thinking
        head = 'user:' + messages[0]['content'] + '~assistant:<think></think>\n'
        return head if add_generation_prompt else head + messages[1]['content'] + '~\n'

    def __call__(self, text, **kwargs):
        return {'input_ids': [ord(c) for c in text], 'offset_mapping': [(i, i+1) for i in range(len(text))]}


def row(text='abcdef', kind='synthetic', **extra):
    return dict(example_id='draw', source_id='source', source_kind=kind, text=text,
                sha256=hashlib.sha256(text.encode()).hexdigest(), training_request='Reference?', **extra)


@pytest.mark.parametrize('kind', ['synthetic', 'c4'])
@pytest.mark.parametrize('length', [1, 50, 100, 501])
def test_full_body_targets_once_and_only_final_chunk_end(kind, length):
    t = TemplateTokenizer()
    r = row('abcdefg' * (length//7) + 'a' * (length%7), kind)
    spec = DocumentSerializationSpec(continuation_context_tokens=8)
    chunks = tokenize_document(r, t, max_length=100, synthetic_prefix='TAG\n', serialization=spec)
    targets = [x for c in chunks for x in c['labels'] if x != -100]
    assert targets == [*map(ord, r['text']), t.eos_token_id]
    assert sum(c['terminal_chunk'] for c in chunks) == 1
    for c in chunks:
        assert len(c['input_ids']) <= 100
        n = c['context_tokens']
        assert c['labels'][:n] == [-100] * n
        context = ''.join(map(chr, c['input_ids'][:n]))
        assert context.startswith('user:Reference?~assistant:<think></think>\n' + ('TAG\n' if kind=='synthetic' else ''))
        if c['chunk_start']:
            assert context.endswith(r['text'][c['chunk_start']-8:c['chunk_start']])
        if not c['terminal_chunk']:
            assert t.eos_token_id not in c['labels']


def test_stored_requests_budgets_and_template_fail_closed():
    t = TemplateTokenizer()
    spec = DocumentSerializationSpec(continuation_context_tokens=0)
    for selection in ['prefix', 'even_eos']:
        chunks = tokenize_document(row('abcde'*30, loss_token_budget=3, loss_token_selection=selection),
            t, max_length=90, serialization=spec)
        targets = [x for c in chunks for x in c['labels'] if x!=-100]
        assert len(targets)==3
        if selection=='even_eos':assert targets[-1]==t.eos_token_id
    r=row();del r['training_request']
    with pytest.raises(ValueError, match='training_request'):
        tokenize_document(r,t,max_length=100,serialization=spec)
    with pytest.raises(ValueError, match='leaves no room'):
        tokenize_document(row(),t,max_length=30,serialization=spec)
    with pytest.raises(ValueError, match='reserved assistant end'):
        tokenize_document(row('abc~def'),t,max_length=100,serialization=spec)
    original=t.apply_chat_template
    def changed(messages, **kwargs):
        text=original(messages,**kwargs)
        return text if kwargs['add_generation_prompt'] else text+'second-end'
    t.apply_chat_template=changed
    with pytest.raises(ValueError, match='template/end-marker'):
        tokenize_document(row(),t,max_length=100,serialization=spec)


def test_absent_opt_ins_preserve_historical_dumps_and_plan():
    spec=DocumentSFTSpec(manifest_path='unused')
    assert 'serialization' not in spec.model_dump(mode='json')
    assert 'model_revision' not in spec.model_dump(mode='json')
    assert preprocessing_contract(spec)=={'max_length':1024,'synthetic_prefix':'<DOCTAG>\n',
        'leading_eos_context':True,'terminal_eos_loss':True,'packing':False,'chunk_overlap':1}
    spec.serialization=DocumentSerializationSpec()
    spec.model_revision='1'*40
    contract=preprocessing_contract(spec)
    assert contract['leading_eos_context'] is False
    assert contract['chunk_overlap']==64 and contract['model_revision']=='1'*40


def test_unequal_length_accumulation_matches_combined_token_mean():
    import torch
    from transformers.loss.loss_utils import ForCausalLMLoss
    torch.manual_seed(42)
    logits=torch.randn(2,6,9,requires_grad=True)
    labels=torch.tensor([[-100,1,2,-100,-100,-100],[-100,3,4,5,6,7]])
    denom=int((labels[:,1:]!=-100).sum())
    split=sum(ForCausalLMLoss(logits[i:i+1],labels[i:i+1],9,num_items_in_batch=denom) for i in range(2))
    combined=ForCausalLMLoss(logits,labels,9,num_items_in_batch=denom)
    assert torch.allclose(split,combined)
    split_grad,=torch.autograd.grad(split,logits,retain_graph=True)
    whole_grad,=torch.autograd.grad(combined,logits)
    assert torch.allclose(split_grad,whole_grad)
    wrong=sum(ForCausalLMLoss(logits[i:i+1],labels[i:i+1],9) for i in range(2))/2
    assert not torch.allclose(wrong,combined)
