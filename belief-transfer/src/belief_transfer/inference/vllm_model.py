"""Opt-in CUDA vLLM generation; no imports or weights until first use.

Run this backend in its separately pinned inference environment. The training
environment stays unchanged. Probability settings are shared with HF; RNG identity
is explicitly different and must receive its own qualified BASE.
"""
from __future__ import annotations

from pathlib import Path

from belief_transfer.inference.execution import generation_identity
from belief_transfer.inference.model import _apply_chat_template, _is_peft_checkpoint
from belief_transfer.schemas import CUDAGenerationSpec, ModelsConfig


class VLLMModel:
    def __init__(self, model: str, models_config: ModelsConfig, *, generation: CUDAGenerationSpec,
                 adapter_path: str | Path | None = None, max_new_tokens: int = 256,
                 seed: int = 42, enable_thinking: bool = False, top_p: float | None = None,
                 top_k: int | None = None, min_p: float | None = None,
                 batch_size: int | None = None):
        if generation.engine != 'vllm':
            raise ValueError('Expected vLLM execution configuration')
        self.model, self._spec, self.generation = model, models_config.models[model], generation
        if self._spec.dtype != 'bfloat16':
            raise ValueError('Only BF16 vLLM study inference is validated by this implementation')
        self.adapter_path = Path(adapter_path) if adapter_path is not None else None
        self.max_new_tokens, self.seed, self.enable_thinking = max_new_tokens, seed, enable_thinking
        self.batch_size = batch_size or generation.max_num_seqs
        self.sampling_options = {'top_p': top_p if top_p is not None else 1.,
                                 'top_k': top_k if top_k is not None else -1,
                                 'min_p': min_p if min_p is not None else 0.}
        if generation.presence_penalty is not None:
            self.sampling_options['presence_penalty'] = generation.presence_penalty
        self._engine = self._tokenizer = self._lora = None

    def _ensure_loaded(self):
        if self._engine is not None:
            return
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError('vLLM study inference requires CUDA')
        if self.adapter_path is not None and not _is_peft_checkpoint(self.adapter_path):
            raise ValueError('This vLLM path supports base weights or PEFT adapters only')
        # CUDA availability checks can poison fork without marking CUDA initialized.
        # Initialize here so vLLM consistently chooses spawn, including standalone
        # probes that did not already request hardware metadata through the runner.
        torch.cuda.init()
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer
        from vllm import LLM

        weights = snapshot_download(self._spec.pretrained, revision=self.generation.revision,
                                    local_files_only=True)
        self._tokenizer = AutoTokenizer.from_pretrained(weights, local_files_only=True)
        self._engine = LLM(model=weights, tokenizer=weights, dtype='bfloat16',
            tensor_parallel_size=1, max_model_len=self.generation.max_model_len,
            max_num_seqs=self.generation.max_num_seqs, max_num_batched_tokens=8192,
            gpu_memory_utilization=self.generation.gpu_memory_utilization,
            enable_prefix_caching=False, enable_chunked_prefill=True, enforce_eager=False,
            generation_config='vllm', seed=self.seed, enable_lora=True, max_lora_rank=64)
        if self.adapter_path is not None:
            from vllm.lora.request import LoRARequest

            self._lora = LoRARequest('study-adapter', 1, str(self.adapter_path.resolve()))

    def generate_batch_with_metadata(self, prompts, *, temperature=0, seeds, batch_size):
        if not prompts or len(prompts) != len(seeds) or batch_size < 1 or len(prompts) > batch_size:
            raise ValueError('Aligned nonempty prompts/seeds and positive batch size required')
        self._ensure_loaded()
        from vllm import SamplingParams

        texts = [_apply_chat_template(self._tokenizer, [{'role': 'user', 'content': p}],
                                      enable_thinking=self.enable_thinking) for p in prompts]
        inputs = [self._tokenizer.encode(text, add_special_tokens=False) for text in texts]
        if any(len(ids) + self.max_new_tokens > self.generation.max_model_len for ids in inputs):
            raise ValueError('Request exceeds pinned vLLM context capacity')
        params = [SamplingParams(temperature=temperature, max_tokens=self.max_new_tokens,
                                 seed=int(seed), **self.sampling_options) for seed in seeds]
        results = self._engine.generate([{'prompt_token_ids': ids} for ids in inputs], params,
                                       lora_request=self._lora, use_tqdm=False)
        if len(results) != len(inputs):
            raise ValueError('vLLM returned incorrect request count')
        execution = generation_identity(self.generation)
        replies = []
        for ids, seed, result in zip(inputs, seeds, results):
            actual_lora = getattr(result, 'lora_request', None)
            raw_outputs = [{'token_ids': list(getattr(o, 'token_ids', []) or []),
                'text': getattr(o, 'text', None), 'finish_reason': getattr(o, 'finish_reason', None),
                'stop_reason': getattr(o, 'stop_reason', None)} for o in getattr(result, 'outputs', [])]
            output = raw_outputs[0] if raw_outputs else {}
            tokens = output.get('token_ids', [])
            text = self._tokenizer.decode(tokens, skip_special_tokens=True).strip()
            error = None
            if list(getattr(result, 'prompt_token_ids', []) or []) != ids or len(raw_outputs) != 1:
                error = 'vLLM input identity or output multiplicity changed'
            elif self._lora is not None and getattr(actual_lora, 'lora_int_id', None) != self._lora.lora_int_id:
                error = 'vLLM did not confirm the requested adapter'
            elif output.get('finish_reason') not in {'stop', 'length'}:
                error = f'vLLM request did not complete normally: {output.get("finish_reason")}'
            elif not tokens:
                error = 'vLLM returned no generated tokens'
            replies.append((text, {'finish_reason': output.get('finish_reason'),
                'stop_reason': output.get('stop_reason'), 'prompt_tokens': len(ids),
                'generation_tokens': len(tokens), 'input_token_ids': ids, 'output_token_ids': tokens,
                'sampling_seed': int(seed), 'sampling_seed_strategy': 'vllm-per-request-v1',
                'sampler_backend': 'vllm-per-request-v1', 'batch_size': len(prompts),
                'submission_batch_size': len(prompts), 'max_num_seqs': self.generation.max_num_seqs,
                'adapter_lora_id': getattr(actual_lora, 'lora_int_id', None),
                **({'backend_error': error, 'reported_input_token_ids': getattr(result, 'prompt_token_ids', None),
                    'raw_outputs': raw_outputs} if error else {}),
                'model_revision': self.generation.revision, **execution}))
        self.last_generation_metadata = replies[0][1] if len(replies) == 1 else None
        return replies

    def generate(self, prompts, temperature=0):
        texts = []
        for start in range(0, len(prompts), self.batch_size):
            group = prompts[start:start + self.batch_size]
            texts.extend(text for text, _ in self.generate_batch_with_metadata(
                group, temperature=temperature, seeds=[self.seed] * len(group), batch_size=self.batch_size))
        if len(prompts) != 1:
            self.last_generation_metadata = None
        return texts
