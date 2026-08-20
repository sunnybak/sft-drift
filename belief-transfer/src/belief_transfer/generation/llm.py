"""Async OpenAI calls for generation."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import AsyncIterable, AsyncIterator, Iterable
from dataclasses import dataclass, field

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
from openai.types.responses import ResponseUsage

from belief_transfer.generation.cache import Cache, cache_key, default_cache
from belief_transfer.generation.context import CallRecord, RunContext

load_dotenv(find_dotenv())

MODEL = "gpt-5.6-luna"
LONG_CONTEXT_INPUT_TOKENS = 272_000
DEFAULT_THROUGHPUT = 10
RETRIES = 10
REQUEST_TIMEOUT_SECONDS = 300.0
_DONE = object()

# USD per 1M tokens. https://developers.openai.com/api/docs/pricing
# Long-context rates apply to the full request when input exceeds 272k tokens.
_PRICES: dict[str, dict[str, dict[str, float]]] = {
    "gpt-5.6-sol": {
        "short": {
            "input": 5.00,
            "cached_input": 0.50,
            "cache_write": 6.25,
            "output": 30.00,
        },
        "long": {
            "input": 10.00,
            "cached_input": 1.00,
            "cache_write": 12.50,
            "output": 45.00,
        },
    },
    "gpt-5.6-luna": {
        "short": {
            "input": 0.20,
            "cached_input": 0.02,
            "cache_write": 0.25,
            "output": 1.20,
        },
        "long": {
            "input": 0.40,
            "cached_input": 0.04,
            "cache_write": 0.50,
            "output": 1.80,
        },
    },
}


@dataclass(frozen=True)
class CallCost:
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cache_write_tokens: int
    reasoning_tokens: int
    cost_usd: float


@dataclass
class CostTracker:
    calls: list[CallCost] = field(default_factory=list)

    @property
    def cost_usd(self) -> float:
        return sum(call.cost_usd for call in self.calls)

    def add(self, call: CallCost) -> None:
        self.calls.append(call)

    def reset(self) -> None:
        self.calls.clear()


costs = CostTracker()


def estimate_cost_usd(model: str, usage: ResponseUsage) -> float:
    prices = _PRICES[model]
    tier = "long" if usage.input_tokens > LONG_CONTEXT_INPUT_TOKENS else "short"
    rates = prices[tier]
    cached = usage.input_tokens_details.cached_tokens or 0
    cache_write = usage.input_tokens_details.cache_write_tokens or 0
    uncached = max(0, usage.input_tokens - cached - cache_write)
    return (
        uncached * rates["input"]
        + cached * rates["cached_input"]
        + cache_write * rates["cache_write"]
        + usage.output_tokens * rates["output"]
    ) / 1_000_000


def _call_cost(model: str, usage: ResponseUsage) -> CallCost:
    return CallCost(
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cached_tokens=usage.input_tokens_details.cached_tokens or 0,
        cache_write_tokens=usage.input_tokens_details.cache_write_tokens or 0,
        reasoning_tokens=usage.output_tokens_details.reasoning_tokens or 0,
        cost_usd=estimate_cost_usd(model, usage),
    )


def _usage_fields(call_cost: CallCost) -> dict[str, int]:
    """The token counts of `call_cost`, without its model or cost -- what a cache entry
    needs to let a later cache *hit* still report accurate tokens (at $0 cost)."""
    return {
        "input_tokens": call_cost.input_tokens,
        "output_tokens": call_cost.output_tokens,
        "cached_tokens": call_cost.cached_tokens,
        "cache_write_tokens": call_cost.cache_write_tokens,
        "reasoning_tokens": call_cost.reasoning_tokens,
    }


def _fresh_call_record(call_cost: CallCost, latency_s: float) -> CallRecord:
    return CallRecord(
        cached=False,
        cost_usd=call_cost.cost_usd,
        latency_s=latency_s,
        **_usage_fields(call_cost),
    )


def _cached_call_record(usage: dict[str, int]) -> CallRecord:
    return CallRecord(
        cached=True,
        cost_usd=0.0,
        latency_s=None,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cached_tokens=usage.get("cached_tokens", 0),
        cache_write_tokens=usage.get("cache_write_tokens", 0),
        reasoning_tokens=usage.get("reasoning_tokens", 0),
    )


@dataclass(frozen=True)
class Tool:
    """A forced function call, used to get structured output instead of parsed text."""

    name: str
    description: str
    parameters: dict[str, object]


@dataclass(frozen=True)
class Completion:
    index: int
    prompt: str
    text: str
    payload: dict[str, object] | None = None
    """Parsed tool arguments, when the request forced a tool call."""


async def _as_async(prompts: AsyncIterable[str] | Iterable[str]) -> AsyncIterator[str]:
    if hasattr(prompts, "__aiter__"):
        async for prompt in prompts:  # type: ignore[union-attr]
            yield prompt
        return
    for prompt in prompts:
        yield prompt


class Client:
    def __init__(
        self,
        throughput: int = DEFAULT_THROUGHPUT,
        model: str = MODEL,
        cache: Cache | None = None,
        context: RunContext | None = None,
    ) -> None:
        if throughput < 1:
            raise ValueError("throughput must be >= 1")
        self.throughput = throughput
        self.model = model
        self.cache = cache if cache is not None else default_cache()
        self.context = context
        """Optional per-run cost/token/latency ledger; see `generation.context`."""
        # Tests mock the client after construction; a placeholder key lets that
        # happen without OPENAI_API_KEY. Real calls still need a valid key.
        #
        # `max_retries` well above the SDK's default of 2 because the limit this hits in
        # practice is *tokens* per minute, not requests: a judging pass resends the whole
        # document once per check, so a run saturates TPM and then every worker 429s at
        # once. Two retries at sub-second backoff all land inside the same exhausted
        # minute and the run dies mid-scoring with its generation already paid for. The
        # SDK honours Retry-After and backs off exponentially, so a deeper retry budget
        # simply waits out the window instead. Lowering `throughput` alone does not fix
        # it -- the ceiling is org-wide, not a property of this process's concurrency.
        self._openai = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY") or "unused",
            max_retries=RETRIES,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._openai.close()

    async def complete(
        self,
        prompt: str,
        *,
        use_cache: bool = True,
        override_cache: bool = False,
        replicate: int | None = None,
    ) -> str:
        key = cache_key(self.model, prompt, replicate=replicate) if use_cache else None
        if key is not None and not override_cache:
            cached = self.cache.get(key)
            if cached is not None:
                if self.context is not None:
                    self.context.record(_cached_call_record(cached.get("usage", {})))
                return cached["text"]
        start = time.monotonic()
        response = await self._openai.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": "none"},
        )
        latency_s = time.monotonic() - start
        if response.usage is None:
            raise RuntimeError("OpenAI response did not include usage")
        call_cost = _call_cost(self.model, response.usage)
        costs.add(call_cost)
        if self.context is not None:
            self.context.record(_fresh_call_record(call_cost, latency_s))
        text = response.output_text
        if key is not None:
            self.cache.set(key, {"text": text, "usage": _usage_fields(call_cost)})
        return text

    async def complete_tool(
        self,
        prompt: str,
        tool: Tool,
        *,
        use_cache: bool = True,
        override_cache: bool = False,
        replicate: int | None = None,
    ) -> dict[str, object]:
        key = cache_key(self.model, prompt, tool.name, replicate=replicate) if use_cache else None
        if key is not None and not override_cache:
            cached = self.cache.get(key)
            if cached is not None:
                if self.context is not None:
                    self.context.record(_cached_call_record(cached.get("usage", {})))
                return cached["payload"]
        start = time.monotonic()
        response = await self._openai.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": "none"},
            tools=[
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "strict": True,
                }
            ],
            tool_choice={"type": "function", "name": tool.name},
        )
        latency_s = time.monotonic() - start
        if response.usage is None:
            raise RuntimeError("OpenAI response did not include usage")
        call_cost = _call_cost(self.model, response.usage)
        costs.add(call_cost)
        for item in response.output:
            if item.type == "function_call" and item.name == tool.name:
                payload = json.loads(item.arguments)
                if self.context is not None:
                    self.context.record(_fresh_call_record(call_cost, latency_s))
                if key is not None:
                    self.cache.set(key, {"payload": payload, "usage": _usage_fields(call_cost)})
                return payload
        raise RuntimeError(f"response did not call {tool.name}")

    async def batch(
        self,
        prompts: AsyncIterable[str] | Iterable[str],
        throughput: int | None = None,
        tool: Tool | None = None,
        *,
        use_cache: bool = True,
        override_cache: bool = False,
        replicate: int | None = None,
    ) -> AsyncIterator[Completion]:
        """Stream completions for `prompts` over `n_workers` concurrent workers.

        `replicate` applies to every prompt in this call and is never sent to the
        model -- pass a number that varies per invocation when the same prompts are
        intentionally re-issued and should get independent, uncached-from-each-other
        answers (see `generation.cache`), otherwise every repeat of an identical
        prompt returns the same cached text.
        """
        n_workers = throughput or self.throughput
        if n_workers < 1:
            raise ValueError("throughput must be >= 1")
        prompt_q: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue(maxsize=n_workers)
        result_q: asyncio.Queue[Completion | Exception | object] = asyncio.Queue()

        async def producer() -> None:
            index = 0
            async for prompt in _as_async(prompts):
                await prompt_q.put((index, prompt))
                index += 1
            for _ in range(n_workers):
                await prompt_q.put(None)

        async def worker() -> None:
            while True:
                item = await prompt_q.get()
                if item is None:
                    await result_q.put(_DONE)
                    return
                index, prompt = item
                try:
                    if tool is None:
                        payload, text = (
                            None,
                            await self.complete(
                                prompt,
                                use_cache=use_cache,
                                override_cache=override_cache,
                                replicate=replicate,
                            ),
                        )
                    else:
                        payload = await self.complete_tool(
                            prompt,
                            tool,
                            use_cache=use_cache,
                            override_cache=override_cache,
                            replicate=replicate,
                        )
                        text = json.dumps(payload)
                except Exception as exc:
                    await result_q.put(exc)
                    return
                await result_q.put(
                    Completion(index=index, prompt=prompt, text=text, payload=payload)
                )

        producer_task = asyncio.create_task(producer())
        workers = [asyncio.create_task(worker()) for _ in range(n_workers)]
        tasks = [producer_task, *workers]
        try:
            finished = 0
            while finished < n_workers:
                item = await result_q.get()
                if item is _DONE:
                    finished += 1
                    continue
                if isinstance(item, Exception):
                    raise item
                assert isinstance(item, Completion)
                yield item
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


async def complete(
    prompt: str,
    *,
    use_cache: bool = True,
    override_cache: bool = False,
    replicate: int | None = None,
    context: RunContext | None = None,
) -> str:
    async with Client(throughput=1, context=context) as client:
        return await client.complete(
            prompt,
            use_cache=use_cache,
            override_cache=override_cache,
            replicate=replicate,
        )


async def batch(
    prompts: AsyncIterable[str] | Iterable[str],
    throughput: int = DEFAULT_THROUGHPUT,
    tool: Tool | None = None,
    *,
    use_cache: bool = True,
    override_cache: bool = False,
    replicate: int | None = None,
    context: RunContext | None = None,
) -> AsyncIterator[Completion]:
    async with Client(throughput=throughput, context=context) as client:
        async for item in client.batch(
            prompts,
            tool=tool,
            use_cache=use_cache,
            override_cache=override_cache,
            replicate=replicate,
        ):
            yield item
