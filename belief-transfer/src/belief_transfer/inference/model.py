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
from belief_transfer.schemas import HardwareProfile, ModelsConfig

MODELS_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "models.yaml"
HARDWARE_PROFILE_PATH = Path(__file__).resolve().parents[3] / "configs" / "hardware_profile.yaml"

# Seconds `chat_generate`'s streaming path waits for the next token before treating the
# stream as dead. Generous: it guards against a `generate` that died without closing the
# stream, not against a merely slow one.
STREAM_TIMEOUT_S = 120.0


def load_models_config(path: Path = MODELS_CONFIG_PATH) -> ModelsConfig:
    return ModelsConfig.model_validate(yaml.safe_load(path.read_text()))


def load_hardware_profile(path: Path = HARDWARE_PROFILE_PATH) -> HardwareProfile | None:
    """Load `configs/hardware_profile.yaml` (see `inference.bench`) if it exists on
    this machine. Returns `None` -- rather than raising -- when the file is absent or
    fails to parse, so a missing or stale calibration file degrades to
    `ModelsConfig.inference.batch_size` instead of breaking inference.
    """
    if not path.exists():
        return None
    try:
        return HardwareProfile.model_validate(yaml.safe_load(path.read_text()))
    except Exception:
        return None


def resolve_batch_size(
    model: str,
    models_config: ModelsConfig,
    *,
    hardware_profile_path: Path = HARDWARE_PROFILE_PATH,
) -> int:
    """This machine's calibrated batch size for `model` if `make bench` has been run
    (see `inference.bench.calibrate_batch_size`), else `models_config`'s shared
    default -- a reasonable but not machine-tuned starting point.
    """
    profile = load_hardware_profile(hardware_profile_path)
    if profile is not None and model in profile.models:
        return profile.models[model].batch_size
    return models_config.inference.batch_size


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
        hardware_profile_path: Path = HARDWARE_PROFILE_PATH,
        device_map: str | None = "auto",
        batch_size: int | None = None,
        max_new_tokens: int = 256,
        seed: int = 42,
        enable_thinking: bool = False,
    ) -> None:
        self.model = model
        self.adapter_path = Path(adapter_path) if adapter_path is not None else None
        self.device_map = device_map
        models_config = load_models_config(models_config_path)
        self._spec = models_config.models[model]
        # `batch_size=None` (the default) auto-resolves to this machine's `make bench`
        # calibration if one exists, else the shared config default -- pass an explicit
        # int to override either.
        self.batch_size = (
            batch_size
            if batch_size is not None
            else resolve_batch_size(model, models_config, hardware_profile_path=hardware_profile_path)
        )
        self.max_new_tokens = max_new_tokens
        self.seed = seed
        self.enable_thinking = enable_thinking
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

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0,
        max_new_tokens: int | None = None,
        on_token=None,
    ) -> str:
        """Reply to one multi-turn conversation (see `chat_generate`). Not part of the
        `Model` protocol -- evals only ever need the batched single-turn `generate`, and
        `ApiModel` has no equivalent -- so this is `HFModel`-only, used by
        `belief_transfer.client` to talk to a base checkpoint or an M+/M- adapter.
        """
        self._ensure_loaded()
        return chat_generate(
            self._hf_model,
            self._tokenizer,
            messages,
            max_new_tokens=self.max_new_tokens if max_new_tokens is None else max_new_tokens,
            temperature=temperature,
            seed=self.seed,
            enable_thinking=self.enable_thinking,
            on_token=on_token,
        )

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
            enable_thinking=self.enable_thinking,
        )


def _apply_chat_template(tokenizer, messages: list[dict[str, str]], *, enable_thinking: bool) -> str:
    """Render `messages` with the tokenizer's chat template, retrying without
    `enable_thinking` for tokenizers that don't accept the kwarg (e.g. plain
    GPT-2-style ones, which raise `TypeError`). Shared by `batched_chat_generate` and
    `chat_generate` so the two agree on templating.
    """
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def chat_generate(
    model,
    tokenizer,
    messages: list[dict[str, str]],
    *,
    max_new_tokens: int,
    temperature: float = 0,
    seed: int = 42,
    enable_thinking: bool = False,
    on_token=None,
) -> str:
    """Generate one assistant reply for a single multi-turn conversation.

    The batched sibling below exists for evals, where every prompt is an independent
    single-turn item; this one is for interactive use (`belief_transfer.client`), where
    there is one conversation carrying system/user/assistant history and no batching to
    do. Same templating, decoding, and seeding rules -- only the message shape and the
    batch-of-one differ.

    `on_token`, if given, is called with each decoded text chunk as it is produced, for
    streaming output. The full reply is returned either way.
    """
    import torch

    torch.manual_seed(seed)

    text = _apply_chat_template(tokenizer, messages, enable_thinking=enable_thinking)
    encoded = tokenizer([text], return_tensors="pt", add_special_tokens=False)
    encoded = {key: value.to(model.device) for key, value in encoded.items()}

    do_sample = temperature > 0
    generate_kwargs: dict[str, object] = dict(
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        use_cache=True,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    if do_sample:
        generate_kwargs["temperature"] = temperature

    if on_token is None:
        with torch.inference_mode():
            output_ids = model.generate(**encoded, **generate_kwargs)
        generated = output_ids[0][encoded["input_ids"].shape[1] :]
        return tokenizer.decode(generated, skip_special_tokens=True).strip()

    return _streamed_generate(model, tokenizer, encoded, generate_kwargs, on_token)


def _streamed_generate(model, tokenizer, encoded, generate_kwargs, on_token) -> str:
    """`chat_generate`'s streaming path: run `generate` on a worker thread and forward
    each chunk to `on_token` as the streamer yields it.

    The worker's exception is captured and re-raised on this thread rather than being
    lost to a dead thread, and the streamer carries a timeout so a `generate` that dies
    before closing the stream surfaces as an error instead of hanging the REPL forever.
    """
    import queue
    import threading

    import torch
    from transformers import TextIteratorStreamer

    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=STREAM_TIMEOUT_S)
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            with torch.inference_mode():
                model.generate(**encoded, **generate_kwargs, streamer=streamer)
        except BaseException as exc:  # noqa: BLE001 -- re-raised on the calling thread below
            errors.append(exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    chunks: list[str] = []
    timed_out = False
    try:
        for chunk in streamer:
            chunks.append(chunk)
            on_token(chunk)
    except queue.Empty:
        timed_out = True
    finally:
        thread.join()

    if errors:
        raise errors[0]
    if timed_out:
        raise TimeoutError(f"generation produced no token for {STREAM_TIMEOUT_S}s")
    return "".join(chunks).strip()


def batched_chat_generate(
    model,
    tokenizer,
    prompts: list[str],
    *,
    max_new_tokens: int,
    temperature: float = 0,
    batch_size: int = 8,
    seed: int = 42,
    enable_thinking: bool = False,
    min_new_tokens: int | None = None,
) -> list[str]:
    """Left-padded, batched, chat-templated generation. Mirrors the reference branch's
    `pipeline.eval_generate.generate_for_condition` mechanism (batch encode -> generate
    -> decode only the newly generated tokens), trimmed to a pure in-memory helper: no
    resumable-JSONL bookkeeping here, since `inference.run.run_inference` owns output
    persistence and this only needs to turn prompts into responses.

    `temperature <= 0` uses greedy decoding (`do_sample=False`); any positive
    temperature samples.

    `enable_thinking` is passed through to `apply_chat_template` for Qwen3-style
    tokenizers that support it: by default Qwen3 emits a `<think>...</think>` block
    before its answer, which can consume the whole `max_new_tokens` budget on eval
    prompts harder than a one-line factual question and leave no final answer at all.
    Defaults to `False` so `response` is the direct answer. Tokenizers that don't
    recognize the kwarg (e.g. plain GPT-2-style ones) raise `TypeError`, which is
    swallowed and retried without it.

    `min_new_tokens` suppresses EOS until that many tokens have been generated. Real
    scoring never wants this -- it truncates nothing but pads answers with filler --
    and it exists for `inference.bench`, which needs every sequence in a calibration
    batch to run the full length so peak VRAM reflects a worst-case KV cache rather
    than however early the model happened to stop.
    """
    import torch

    torch.manual_seed(seed)

    do_sample = temperature > 0
    responses: list[str] = [""] * len(prompts)
    for start in range(0, len(prompts), batch_size):
        batch = prompts[start : start + batch_size]
        texts = [
            _apply_chat_template(tokenizer, [{"role": "user", "content": prompt}], enable_thinking=enable_thinking)
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
        if min_new_tokens is not None:
            generate_kwargs["min_new_tokens"] = min_new_tokens
        with torch.inference_mode():
            output_ids = model.generate(**encoded, **generate_kwargs)
        prompt_width = encoded["input_ids"].shape[1]
        for offset, ids in enumerate(output_ids):
            generated = ids[prompt_width:]
            responses[start + offset] = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return responses
