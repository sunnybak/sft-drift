"""CPU tensor tests of the new sampling path; no weights or training."""
from types import SimpleNamespace

import pytest
import torch

from belief_transfer.inference.model import HFModel, seeded_token_processor


def test_seeded_rows_do_not_depend_on_global_rng_or_other_rows():
    scores = torch.tensor([[0., 1., 2., 3., 4.], [0., 1., 2., 3., 4.]])
    ids = torch.tensor([[1, 2], [1, 2]])
    state = torch.random.get_rng_state().clone()
    draw = seeded_token_processor([7, 91], 2, .6, {'top_k': 4, 'top_p': .95})(ids, scores)
    assert torch.equal(state, torch.random.get_rng_state())
    for i, seed in enumerate([7, 91]):
        single = seeded_token_processor([seed], 2, .6, {'top_k': 4, 'top_p': .95})(ids[i:i + 1], scores[i:i + 1])
        assert draw[i].argmax() == single[0].argmax()


def test_per_token_seed_progression_matches_declared_formula():
    scores = torch.zeros(1, 20)
    sampler = seeded_token_processor([42], 1, 1., {})
    for step in range(8):
        selected = sampler(torch.ones((1, step + 1), dtype=torch.long), scores).argmax().item()
        generator = torch.Generator().manual_seed((42 + step * 0x9e3779b9) & 0xffffffff)
        expected = torch.multinomial(torch.ones(20) / 20, 1, generator=generator).item()
        assert selected == expected


def test_greedy_remains_greedy_and_mismatched_rows_fail():
    p = seeded_token_processor([7], 1, 0, {'top_k': 1})
    scores = torch.tensor([[2., 1., 3.]])
    assert torch.equal(p(torch.ones((1, 1)), scores), scores)
    with pytest.raises(ValueError, match='align'):
        p(torch.ones((2, 1)), torch.zeros((2, 3)))


class Tokenizer:
    eos_token_id = 0
    pad_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        return messages[0]['content']

    def __call__(self, texts, **kwargs):
        width = max(map(len, texts))
        return {'input_ids': torch.tensor([[0] * (width - len(t)) + [1] * len(t) for t in texts]),
                'attention_mask': torch.tensor([[0] * (width - len(t)) + [1] * len(t) for t in texts])}

    def decode(self, ids, **kwargs):
        return ' '.join(str(x) for x in ids if x)


class TinyModel:
    device = 'cpu'
    config = SimpleNamespace(_commit_hash='fake-revision')
    generation_config = SimpleNamespace(top_k=4, top_p=.95, min_p=0.)

    def generate(self, input_ids, attention_mask, logits_processor, **kwargs):
        assert kwargs['do_sample'] is False
        ids = input_ids
        for step in range(3):
            scores = torch.zeros((len(input_ids), 8))
            scores[:, 0] = float('-inf')
            if step == 2:
                scores[:] = float('-inf')
                scores[:, 0] = 0
            for processor in logits_processor:
                scores = processor(ids, scores)
            ids = torch.cat([ids, scores.argmax(-1)[:, None]], dim=1)
        return ids


def fake_hf():
    model = object.__new__(HFModel)
    model._hf_model, model._tokenizer = TinyModel(), Tokenizer()
    model.max_new_tokens, model.enable_thinking = 3, True
    model.sampling_options = {'top_p': .95, 'top_k': 4, 'min_p': 0.}
    return model


def test_batch_metadata_records_unpadded_inputs_real_eos_seed_and_revision():
    m = fake_hf()
    replies = m.generate_batch_with_metadata(['abc', 'q'], seeds=[7, 19], temperature=.6, batch_size=2)
    assert len(replies) == 2
    for i, (_, meta) in enumerate(replies):
        assert meta['finish_reason'] == 'stop'
        assert meta['output_token_ids'][-1] == 0
        assert meta['generation_tokens'] == 3
        assert meta['prompt_tokens'] == [3, 1][i]
        assert meta['input_token_ids'] == [1] * [3, 1][i]
        assert meta['sampling_seed'] == [7, 19][i]
        assert meta['model_revision'] == 'fake-revision'
    sequential = m.generate_batch_with_metadata(['abc', 'q'], seeds=[7, 19], temperature=.6, batch_size=1)
    assert [r[0] for r in replies] == [r[0] for r in sequential]


def test_batch_validation_and_length_stop():
    m = fake_hf()
    with pytest.raises(ValueError):
        m.generate_batch_with_metadata(['abc'], seeds=[], batch_size=2)
    m._tokenizer.eos_token_id = 99
    _, meta = m.generate_batch_with_metadata(['abc'], seeds=[7], temperature=.6, batch_size=1)[0]
    assert meta['finish_reason'] == 'length'
