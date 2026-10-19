"""Opt-in bounded Responses calls; historical client/cache identities stay unchanged."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from belief_transfer.generation import llm


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Budget:
    limit: float
    committed: float = 0.0
    actual: float = 0.0
    uncertain: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def reserve(self, upper_bound: float) -> None:
        async with self.lock:
            if self.committed + upper_bound > self.limit:
                raise BudgetExceeded('Pilot dollar ceiling would be exceeded')
            self.committed += upper_bound

    async def settle(self, reserved: float, actual: float | None) -> None:
        async with self.lock:
            if actual is None:
                self.uncertain += reserved
            else:
                self.actual += actual
                self.committed += actual - reserved


def request_key(model: str, prompt: str, tool: llm.Tool, max_output_tokens: int) -> str:
    """New namespace includes the complete tool and settings; never changes cache_key()."""
    canonical = json.dumps({
        'namespace': 'stance-sdf-responses-v1', 'model': model, 'prompt': prompt,
        'tool': {'name': tool.name, 'description': tool.description, 'parameters': tool.parameters},
        'max_output_tokens': max_output_tokens, 'reasoning': {'effort': 'none'},
        'sampling': 'provider_default', 'automatic_retries': 0,
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


class DocumentClient(llm.Client):
    def __init__(self, *, budget: Budget, input_price_upper_bound: float = 0.10, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if self.model != 'gpt-6-luna':
            raise ValueError('Bounded document client is qualified only for gpt-6-luna')
        self.budget = budget
        if input_price_upper_bound < 0.10:
            raise ValueError('Input reservation cannot be below the uncached input rate')
        self.input_price_upper_bound = input_price_upper_bound
        self.semaphore = asyncio.Semaphore(self.throughput)

    async def request(self, prompt: str, tool: llm.Tool, *, max_output_tokens: int) -> dict[str, Any]:
        if max_output_tokens < 1:
            raise ValueError('max_output_tokens must be positive')
        key = request_key(self.model, prompt, tool, max_output_tokens)
        cached = self.cache.get(key)
        if cached is not None:
            if self.context is not None:
                self.context.record(llm._cached_call_record(cached.get('usage', {})))
            return {**cached['record'], 'cached': True, 'cost_usd': 0.0}
        # Byte-fallback tokenization cannot require more tokens than UTF-8 bytes.
        # Add 8192 for protocol/tool formatting. Keep requests far below long-context tiers.
        request_bytes = len((prompt + json.dumps(tool.parameters) + tool.name + tool.description).encode())
        if request_bytes > 64_000:
            raise ValueError('Document request exceeds bounded short-context envelope')
        reserved = ((request_bytes + 8192) * self.input_price_upper_bound + max_output_tokens * 0.50) / 1_000_000
        async with self.semaphore:
            await self.budget.reserve(reserved)
            started = time.monotonic()
            try:
                # Do not automatically repeat a potentially billed request after a network failure.
                response = await self._openai.with_options(max_retries=0).responses.create(
                    model=self.model, input=prompt, reasoning={'effort': 'none'},
                    max_output_tokens=max_output_tokens,
                    tools=[{'type': 'function', 'name': tool.name, 'description': tool.description,
                            'parameters': tool.parameters, 'strict': True}],
                    tool_choice={'type': 'function', 'name': tool.name},
                )
            except Exception as exc:
                await self.budget.settle(reserved, None)
                return {'cached': False, 'payload': None, 'response': None, 'cost_usd': None,
                        'error': type(exc).__name__, 'uncertain_cost_upper_bound': reserved,
                        'cache_key': key}
            envelope = response.model_dump(mode='json')
            usage = response.usage
            cost = llm._call_cost(self.model, usage) if usage is not None else None
            await self.budget.settle(reserved, cost.cost_usd if cost else None)
            if cost is not None:
                llm.costs.add(cost)
                if self.context is not None:
                    self.context.record(llm._fresh_call_record(cost, time.monotonic() - started))
            payload, error = None, None
            if usage is None:
                error = 'missing_usage'
            elif response.status != 'completed':
                error = f'response_{response.status}'
            else:
                calls = [item for item in response.output
                         if item.type == 'function_call' and item.name == tool.name]
                try:
                    if len(calls) != 1:
                        raise ValueError('Expected one structured result')
                    payload = json.loads(calls[0].arguments)
                    if not isinstance(payload, dict):
                        raise ValueError('Expected object')
                except (ValueError, TypeError):
                    error = 'malformed_tool_payload'
            record = {'cached': False, 'payload': payload, 'response': envelope,
                      'cost_usd': cost.cost_usd if cost else None, 'error': error, 'cache_key': key}
            # Preserve incomplete/malformed outcomes too; they are not silently reissued.
            self.cache.set(key, {'record': record, 'usage': llm._usage_fields(cost) if cost else {}})
            return record
