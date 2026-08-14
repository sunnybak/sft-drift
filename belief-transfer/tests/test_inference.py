from pathlib import Path

import pytest
import torch
import yaml

from belief_transfer.schemas import ChoiceScore, ChoiceScores

from belief_transfer.inference.model import (
    ApiModel,
    HFModel,
    Model,
    batched_chat_generate,
    load_models_config,
    score_choices,
)
from belief_transfer.inference.run import run_inference

ROOT = Path(__file__).resolve().parents[1]


def test_inference_module_imports() -> None:
    assert callable(Model.generate)
    assert callable(run_inference)


class FakeModel:
    def generate(self, prompts, **kwargs):
        return ["TEST"] * len(prompts)


def test_fake_model() -> None:
    assert FakeModel().generate(["a", "b"]) == ["TEST", "TEST"]


def test_load_models_config_reads_configs_models_yaml() -> None:
    config = load_models_config()
    assert "qwen3-4b" in config.models
    assert config.models["qwen3-4b"].pretrained == "Qwen/Qwen3-4B"
    assert config.inference.batch_size >= 1


def test_hf_model_construction_resolves_model_spec_without_loading_weights() -> None:
    # Constructing an HFModel must not touch the network or a GPU: it only resolves
    # the model tag against configs/models.yaml. Loading is deferred to `generate`.
    model = HFModel("qwen3-4b", adapter_path="/some/adapter/dir")
    assert model._spec.pretrained == "Qwen/Qwen3-4B"
    assert model.adapter_path == Path("/some/adapter/dir")
    assert model._hf_model is None


def test_hf_model_unknown_tag_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        HFModel("not-a-real-model-tag")


@pytest.mark.parametrize("cls_and_args", [(ApiModel, ("gpt-5.6-luna",))])
def test_api_model_stores_model_name(cls_and_args) -> None:
    cls, args = cls_and_args
    model = cls(*args)
    assert model.model == args[0]


class FakeTokenizer:
    """Minimal stand-in for a HF tokenizer: enough of the interface
    `batched_chat_generate` calls (apply_chat_template, __call__, decode, pad ids) to
    exercise the batching/padding/slicing logic with no real model or network access.
    """

    pad_token_id = 0
    eos_token_id = 1

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return messages[0]["content"]

    def __call__(self, texts, return_tensors="pt", padding=True, add_special_tokens=False):
        # Encode each text as its length in tokens (deterministic, no vocab needed),
        # left-padded to the batch's longest with pad_token_id.
        encoded = [[len(text)] for text in texts]
        width = max(len(row) for row in encoded)
        padded = [[self.pad_token_id] * (width - len(row)) + row for row in encoded]
        return {"input_ids": torch.tensor(padded), "attention_mask": torch.ones(len(texts), width)}

    def decode(self, ids, skip_special_tokens=True):
        return f"decoded:{ids.tolist()}"


class FakeHFModel:
    device = "cpu"

    def generate(self, input_ids, attention_mask, max_new_tokens, **kwargs):
        # Echo back the prompt plus one new fake token per requested new token.
        new_tokens = torch.full((input_ids.shape[0], max_new_tokens), 7)
        return torch.cat([input_ids, new_tokens], dim=1)


def test_batched_chat_generate_returns_one_response_per_prompt_and_batches() -> None:
    tokenizer = FakeTokenizer()
    model = FakeHFModel()
    prompts = ["a", "bb", "ccc", "dddd", "e"]

    responses = batched_chat_generate(model, tokenizer, prompts, max_new_tokens=3, batch_size=2)

    assert len(responses) == len(prompts)
    assert all(response == "decoded:[7, 7, 7]" for response in responses)


def test_hf_model_generate_uses_lazily_loaded_components(monkeypatch: pytest.MonkeyPatch) -> None:
    model = HFModel("qwen3-4b", max_new_tokens=3)
    monkeypatch.setattr(model, "_ensure_loaded", lambda: None)
    model._hf_model = FakeHFModel()
    model._tokenizer = FakeTokenizer()

    responses = model.generate(["hello", "world"])

    assert responses == ["decoded:[7, 7, 7]"] * 2


class FakeScoringTokenizer:
    """Character-level tokenizer (ord() per char) with a real chat template shape, so
    `score_choices`'s boundary maths and logprob indexing can be exercised exactly,
    with no vocab file or model download.
    """

    pad_token_id = 0
    eos_token_id = 1

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **kwargs):
        return "".join(message["content"] for message in messages)

    def __call__(self, text, add_special_tokens=False, **kwargs):
        if isinstance(text, list):
            text = text[0]
        return {"input_ids": [ord(char) for char in text]}


class FakeScoringModel:
    """Returns logits that make exactly one vocab id likely at every position, so the
    expected logprob of any choice string is computable by hand in the test. Vocab is
    1024 so the merge-simulating token ids in the boundary test fit.
    """

    device = "cpu"

    def __init__(self, favored: str) -> None:
        self.favored = ord(favored)

    def __call__(self, input_ids):
        batch, width = input_ids.shape
        logits = torch.full((batch, width, 1024), -10.0)
        logits[:, :, self.favored] = 10.0
        return type("Output", (), {"logits": logits})()


def test_score_choices_prefers_the_continuation_the_model_favors() -> None:
    model = FakeScoringModel("a")
    scored = score_choices(model, FakeScoringTokenizer(), [{"role": "user", "content": "Q"}], ["aa", "bb"])

    assert scored.top() == "aa"
    assert scored.probabilities()["aa"] > 0.99
    assert [s.n_tokens for s in scored.scores] == [2, 2]


def test_score_choices_reports_both_summed_and_per_token_logprobs() -> None:
    """Length bias is real and the schema exists to expose it: a longer choice of
    equally-likely tokens must score lower on the sum and identically per token.
    """
    model = FakeScoringModel("a")
    scored = score_choices(model, FakeScoringTokenizer(), [{"role": "user", "content": "Q"}], ["a", "aaaa"])

    short, long = scored.scores
    assert short.logprob > long.logprob
    assert short.logprob_per_token == pytest.approx(long.logprob_per_token)
    assert scored.top() == "a"
    assert scored.top(per_token=True) in ("a", "aaaa")


def test_score_choices_measures_the_token_boundary_rather_than_assuming_it() -> None:
    """A tokenizer whose joint encoding diverges from the prompt's standalone encoding
    must not be scored from the wrong offset -- that yields a plausible wrong number,
    not an error.
    """

    class MergingTokenizer(FakeScoringTokenizer):
        def __call__(self, text, add_special_tokens=False, **kwargs):
            if isinstance(text, list):
                text = text[0]
            ids = [ord(char) for char in text]
            # Simulate a BPE merge across the join: the prompt's last token and the
            # choice's first character fuse into one unit, so the prompt's standalone
            # encoding is NOT a prefix of the joint one.
            if text.startswith("QQa"):
                return {"input_ids": [ord("Q"), 999] + ids[3:]}
            return {"input_ids": ids}

    scored = score_choices(FakeScoringModel("a"), MergingTokenizer(), [{"role": "user", "content": "QQ"}], ["aa"])

    # Prompt "QQ" is 2 tokens standalone, but the joint encoding diverges at index 1,
    # so the scored region starts there -- 2 tokens ([999, "a"]), not the 1 token a
    # naive len(prompt_ids) offset would have scored.
    assert scored.scores[0].n_tokens == 2


def test_score_choices_rejects_a_prompt_sharing_no_prefix_with_the_joint_encoding() -> None:
    class TotallyDivergentTokenizer(FakeScoringTokenizer):
        def __call__(self, text, add_special_tokens=False, **kwargs):
            if isinstance(text, list):
                text = text[0]
            return {"input_ids": [999, 998] if text.startswith("Qa") else [ord(c) for c in text]}

    with pytest.raises(ValueError, match="no preceding context"):
        score_choices(
            FakeScoringModel("a"), TotallyDivergentTokenizer(), [{"role": "user", "content": "Q"}], ["aa"]
        )


def test_score_choices_rejects_a_choice_with_no_tokens() -> None:
    with pytest.raises(ValueError, match="no tokens"):
        score_choices(FakeScoringModel("a"), FakeScoringTokenizer(), [{"role": "user", "content": "Q"}], [""])


def test_choice_probabilities_sum_to_one_and_survive_extreme_logprobs() -> None:
    scores = ChoiceScores(
        prompt="p",
        scores=[
            ChoiceScore(choice="a", logprob=-1000.0, logprob_per_token=-500.0, n_tokens=2),
            ChoiceScore(choice="b", logprob=-1001.0, logprob_per_token=-500.5, n_tokens=2),
        ],
    )

    probabilities = scores.probabilities()

    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert probabilities["a"] > probabilities["b"]
