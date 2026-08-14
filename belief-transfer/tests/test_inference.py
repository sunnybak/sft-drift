from pathlib import Path

import pytest
import torch
import yaml

from belief_transfer.inference.model import (
    ApiModel,
    HFModel,
    Model,
    batched_chat_generate,
    load_models_config,
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
