"""Apple-silicon inference backend: `MLXModel`, satisfying the same `Model` and
`ChoiceScorer` protocols as `inference.model.HFModel`.

Exists so local development can score the *real* checkpoints in `data/checkpoints/` on
a Mac instead of only being able to run tests with tiny stand-in models. Those
checkpoints are PEFT-format LoRA adapters, which released mlx-lm does not read, so
`inference.peft_to_mlx` converts them on load -- there is still only one adapter format
on disk, and it is the one CUDA training already writes.

Scope, from `inference.backend`: **inference and scoring only.** Nothing here trains,
and `training.sft.load_for_training` refuses to run on this backend.

`score_choices` here must agree with the torch implementation, not merely resemble it:
it is the same teacher-forced quantity (`ChoiceScore`'s summed and per-token
log-probabilities over the choice's own tokens, with the prompt/choice token boundary
*measured* rather than assumed -- see `inference.model._choice_token_boundary` for why
that matters). `tests/test_backend_agreement.py` is what turns that intent into a
check; until it passes on a given machine, treat MLX numbers as iteration aids rather
than results.
"""

from __future__ import annotations

from pathlib import Path

from belief_transfer.inference.backend import BackendInfo, backend_info
from belief_transfer.inference.model import (
    HARDWARE_PROFILE_PATH,
    MODELS_CONFIG_PATH,
    load_models_config,
    require_model_cached,
    resolve_batch_size,
)
from belief_transfer.inference.peft_to_mlx import apply_peft_adapter, is_peft_adapter
from belief_transfer.schemas import ChoiceScore, ChoiceScores


class MLXModel:
    """A local model run through mlx-lm: the base checkpoint (`adapter_path=None`) or a
    PEFT LoRA adapter on top of it.

    Mirrors `HFModel`'s constructor and laziness deliberately -- same argument names,
    same "constructing it touches no weights" contract -- so a caller can hold either
    behind the `Model`/`ChoiceScorer` protocols without knowing which it has.
    """

    def __init__(
        self,
        model: str,
        *,
        adapter_path: str | Path | None = None,
        models_config_path: Path = MODELS_CONFIG_PATH,
        hardware_profile_path: Path = HARDWARE_PROFILE_PATH,
        batch_size: int | None = None,
        max_new_tokens: int = 256,
        seed: int = 42,
        enable_thinking: bool = False,
    ) -> None:
        self.model = model
        self.adapter_path = Path(adapter_path) if adapter_path is not None else None
        models_config = load_models_config(models_config_path)
        self._spec = models_config.models[model]
        self.batch_size = (
            batch_size
            if batch_size is not None
            else resolve_batch_size(model, models_config, hardware_profile_path=hardware_profile_path)
        )
        self.max_new_tokens = max_new_tokens
        self.seed = seed
        self.enable_thinking = enable_thinking
        self._mlx_model = None
        self._tokenizer = None

    @property
    def backend_info(self) -> BackendInfo:
        return backend_info("mlx", dtype=self._spec.dtype)

    def _ensure_loaded(self) -> None:
        if self._mlx_model is not None:
            return
        from mlx_lm import load

        require_model_cached(self._spec.pretrained)
        if self.adapter_path is None:
            model, tokenizer = load(self._spec.pretrained)
        elif is_peft_adapter(self.adapter_path):
            # This repo's checkpoints are PEFT-format (written by CUDA training), which
            # mlx-lm's own loader does not read -- see `inference.peft_to_mlx`.
            model, tokenizer = load(self._spec.pretrained)
            apply_peft_adapter(model, self.adapter_path)
        else:
            model, tokenizer = load(self._spec.pretrained, adapter_path=str(self.adapter_path))
        self._mlx_model = model
        self._tokenizer = tokenizer

    def _prompt_text(self, messages: list[dict[str, str]]) -> str:
        """Render `messages` with the tokenizer's chat template.

        Same two-step fallback as `inference.model._apply_chat_template`: tokenizers
        that don't accept `enable_thinking` raise `TypeError`, and Qwen3 without it
        emits a `<think>` block that can eat the whole token budget.
        """
        tokenizer = self._tokenizer
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=self.enable_thinking,
            )
        except TypeError:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def score_choices(
        self,
        prompt: str | list[dict[str, str]],
        choices: list[str],
    ) -> ChoiceScores:
        """Teacher-forced log-probability of each choice continuing `prompt`.

        One forward pass per choice over prompt+choice, reading off
        log P(token | prefix) for the choice's tokens only. Deliberately not batched
        across choices: `changelog/2026-08-14.md` recorded that batching this on the
        torch side changed scores through padding-position kernel sensitivity, and the
        whole point of this backend is to produce the same numbers as that one.
        """
        import mlx.core as mx

        self._ensure_loaded()
        messages = [{"role": "user", "content": prompt}] if isinstance(prompt, str) else prompt
        prompt_text = self._prompt_text(messages)

        scored: list[ChoiceScore] = []
        for choice in choices:
            full_ids, boundary = self._token_boundary(prompt_text, prompt_text + choice)
            if boundary >= len(full_ids):
                raise ValueError(f"choice {choice!r} contributes no tokens after the prompt")
            if boundary < 1:
                raise ValueError(
                    f"prompt and prompt+{choice!r} share no leading tokens; cannot score a "
                    "continuation with no preceding context"
                )

            logits = self._mlx_model(mx.array([full_ids]))
            # logits[:, i] predicts token i+1, so the distribution over choice token j
            # (absolute index boundary+j) is at position boundary+j-1. Cast to float32
            # before log_softmax for the same reason the torch path calls .float():
            # a bf16 softmax over a ~152k vocab loses enough precision to move the
            # third decimal of a score that gets divided by another score later.
            window = logits[0, boundary - 1 : -1].astype(mx.float32)
            log_probs = window - mx.logsumexp(window, axis=-1, keepdims=True)
            targets = mx.array(full_ids[boundary:])
            token_logprobs = mx.take_along_axis(log_probs, targets[:, None], axis=-1).squeeze(-1)
            mx.eval(token_logprobs)

            total = float(token_logprobs.sum().item())
            n_tokens = int(targets.size)
            scored.append(
                ChoiceScore(
                    choice=choice,
                    logprob=total,
                    logprob_per_token=total / n_tokens,
                    n_tokens=n_tokens,
                )
            )

        return ChoiceScores(prompt=prompt_text, scores=scored)

    def _token_boundary(self, prompt_text: str, full_text: str) -> tuple[list[int], int]:
        """Ids of `full_text` plus the index where the choice's tokens begin.

        The boundary is measured, not computed as `len(encode(prompt))`, because BPE
        can merge across the join -- scoring from an assumed offset yields a plausible
        wrong number rather than an error. Same algorithm as
        `inference.model._choice_token_boundary`; kept as its own method because the
        two tokenizer wrappers expose different encode APIs.
        """
        prompt_ids = self._encode(prompt_text)
        full_ids = self._encode(full_text)
        boundary = 0
        for boundary, (left, right) in enumerate(zip(prompt_ids, full_ids)):
            if left != right:
                break
        else:
            boundary = len(prompt_ids)
        return full_ids, boundary

    def _encode(self, text: str) -> list[int]:
        """Token ids for `text` with no added specials.

        mlx-lm wraps the HF tokenizer, so `encode` is available but adds specials by
        default on some tokenizers; going through the underlying `_tokenizer` when it
        is exposed keeps this identical to the torch path's
        `tokenizer(text, add_special_tokens=False)`.
        """
        tokenizer = self._tokenizer
        underlying = getattr(tokenizer, "_tokenizer", None)
        if underlying is not None:
            return list(underlying(text, add_special_tokens=False)["input_ids"])
        return list(tokenizer.encode(text))

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0,
        max_new_tokens: int | None = None,
        on_token=None,
    ) -> str:
        """Reply to one multi-turn conversation. `HFModel.chat`'s counterpart, for
        `belief_transfer.client` on a Mac."""
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler

        self._ensure_loaded()
        prompt_text = self._prompt_text(messages)
        sampler = make_sampler(temp=temperature)

        chunks: list[str] = []
        for response in stream_generate(
            self._mlx_model,
            self._tokenizer,
            prompt_text,
            max_tokens=self.max_new_tokens if max_new_tokens is None else max_new_tokens,
            sampler=sampler,
        ):
            chunks.append(response.text)
            if on_token is not None:
                on_token(response.text)
        return "".join(chunks).strip()

    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        """Single-turn generation for every prompt.

        Sequential, not batched: mlx-lm's batched generation path pads, and this
        backend's contract is to match the torch numbers rather than to be fast. On
        unified memory the loop is also less of a penalty than it would be on a
        discrete GPU. `self.batch_size` is therefore carried for interface parity
        with `HFModel` and not used here.
        """
        self._ensure_loaded()
        return [
            self.chat([{"role": "user", "content": prompt}], temperature=temperature)
            for prompt in prompts
        ]
