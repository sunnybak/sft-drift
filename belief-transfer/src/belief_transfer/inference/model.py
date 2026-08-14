"""Model interface for inference: a small shared `Model` protocol, and the two
implementations behind it -- `ApiModel` (the base, un-finetuned model, via the OpenAI
client every generation/judging call already goes through) and `HFModel` (a local
Transformers model, either the plain base checkpoint or a LoRA adapter on top of it,
for scoring M+/M- after SFT). Per AGENTS.md's Inference section, everything that needs
to call a model goes through this interface rather than each caller picking an API vs
local-weights path itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import yaml

from belief_transfer.generation import llm
from belief_transfer.schemas import ModelsConfig

MODELS_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "models.yaml"


def load_models_config(path: Path = MODELS_CONFIG_PATH) -> ModelsConfig:
    return ModelsConfig.model_validate(yaml.safe_load(path.read_text()))


class Model(Protocol):
    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        ...


class ApiModel:
    """The unmodified base model, called through `generation.llm.Client` -- i.e. what
    AGENTS.md's `B(BASE | ...)`/`A(BASE | ...)` terms measure. `generate` is a sync
    wrapper (asyncio.run) around the existing async client so `Model` stays a plain
    sync protocol for both backends.
    """

    def __init__(self, model: str) -> None:
        self.model = model

    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        # generation.llm.Client has no sampling-temperature knob (every call fixes
        # reasoning effort to "none"); `temperature` is accepted only for symmetry
        # with HFModel's Model protocol and otherwise has no effect on this backend.
        del temperature
        return _run_api_batch(self.model, prompts)


def _run_api_batch(model: str, prompts: list[str]) -> list[str]:
    import asyncio

    async def _collect() -> list[str]:
        results: dict[int, str] = {}
        async with llm.Client(model=model) as client:
            async for completion in client.batch(prompts):
                results[completion.index] = completion.text
        return [results[i] for i in range(len(prompts))]

    return asyncio.run(_collect())


class HFModel:
    """A local Transformers model: the base checkpoint (`adapter_path=None`) or a LoRA
    adapter fine-tuned on top of it (M+/M-). Loading is lazy (`_ensure_loaded`, called
    on first `generate`) so constructing an `HFModel` -- e.g. to check which model tag
    or adapter it resolves to -- never downloads weights or touches a GPU; tests exploit
    this to cover construction and dispatch without real model access (see
    tests/test_inference.py's `test_hf_model_ensure_loaded_is_lazy`).
    """

    def __init__(
        self,
        model: str,
        *,
        adapter_path: str | Path | None = None,
        models_config_path: Path = MODELS_CONFIG_PATH,
        device_map: str | None = "auto",
        batch_size: int = 8,
        max_new_tokens: int = 256,
        seed: int = 42,
    ) -> None:
        self.model = model
        self.adapter_path = Path(adapter_path) if adapter_path is not None else None
        self.device_map = device_map
        self.batch_size = batch_size
        self.max_new_tokens = max_new_tokens
        self.seed = seed
        self._spec = load_models_config(models_config_path).models[model]
        self._hf_model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> None:
        if self._hf_model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(self._spec.pretrained)
        tokenizer.padding_side = "left"
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

        torch_dtype = getattr(torch, self._spec.dtype)
        model = AutoModelForCausalLM.from_pretrained(
            self._spec.pretrained, dtype=torch_dtype, device_map=self.device_map
        )
        if self.adapter_path is not None:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, str(self.adapter_path))
        model.eval()
        self._hf_model = model
        self._tokenizer = tokenizer

    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        self._ensure_loaded()
        return batched_chat_generate(
            self._hf_model,
            self._tokenizer,
            prompts,
            max_new_tokens=self.max_new_tokens,
            temperature=temperature,
            batch_size=self.batch_size,
            seed=self.seed,
        )


def batched_chat_generate(
    model,
    tokenizer,
    prompts: list[str],
    *,
    max_new_tokens: int,
    temperature: float = 0,
    batch_size: int = 8,
    seed: int = 42,
) -> list[str]:
    """Left-padded, batched, chat-templated generation. Mirrors the reference branch's
    `pipeline.eval_generate.generate_for_condition` mechanism (batch encode -> generate
    -> decode only the newly generated tokens), trimmed to a pure in-memory helper: no
    resumable-JSONL bookkeeping here, since `inference.run.run_inference` owns output
    persistence and this only needs to turn prompts into responses.

    `temperature <= 0` uses greedy decoding (`do_sample=False`); any positive
    temperature samples.
    """
    import torch

    torch.manual_seed(seed)

    do_sample = temperature > 0
    responses: list[str] = [""] * len(prompts)
    for start in range(0, len(prompts), batch_size):
        batch = prompts[start : start + batch_size]
        texts = [
            tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
            )
            for prompt in batch
        ]
        encoded = tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=False)
        encoded = {key: value.to(model.device) for key, value in encoded.items()}
        generate_kwargs: dict[str, object] = dict(
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            use_cache=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
        if do_sample:
            generate_kwargs["temperature"] = temperature
        with torch.inference_mode():
            output_ids = model.generate(**encoded, **generate_kwargs)
        prompt_width = encoded["input_ids"].shape[1]
        for offset, ids in enumerate(output_ids):
            generated = ids[prompt_width:]
            responses[start + offset] = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return responses
