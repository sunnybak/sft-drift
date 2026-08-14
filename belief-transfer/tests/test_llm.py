import asyncio
import json
import os
from types import SimpleNamespace

import pytest

from belief_transfer.generation.cache import Cache
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.llm import (
    MODEL,
    Client,
    Tool,
    batch,
    complete,
    costs,
    estimate_cost_usd,
)


def _usage(
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    cache_write_tokens: int = 0,
    reasoning_tokens: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_tokens_details=SimpleNamespace(
            cached_tokens=cached_tokens,
            cache_write_tokens=cache_write_tokens,
        ),
        output_tokens_details=SimpleNamespace(reasoning_tokens=reasoning_tokens),
    )


def test_estimate_cost_usd_luna_short_context() -> None:
    # 1k uncached in + 500 out at $0.20 / $1.20 per 1M
    cost = estimate_cost_usd(MODEL, _usage(1_000, 500))
    assert cost == pytest.approx(0.0008)


def test_estimate_cost_usd_luna_cached_and_write() -> None:
    cost = estimate_cost_usd(
        MODEL,
        _usage(1_000, 0, cached_tokens=400, cache_write_tokens=500),
    )
    assert cost == pytest.approx(
        (100 * 0.20 + 400 * 0.02 + 500 * 0.25) / 1_000_000
    )


def test_batch_streams_with_throughput() -> None:
    async def run() -> None:
        client = Client(throughput=3)
        current = 0
        peak = 0

        async def fake_complete(prompt: str, **kwargs: object) -> str:
            nonlocal current, peak
            current += 1
            peak = max(peak, current)
            await asyncio.sleep(0.02)
            current -= 1
            return prompt[::-1]

        client.complete = fake_complete  # type: ignore[method-assign]
        prompts = [f"p{i}" for i in range(8)]
        results = [item async for item in client.batch(prompts)]
        await client.aclose()
        assert {item.index for item in results} == set(range(8))
        assert {item.text for item in results} == {prompt[::-1] for prompt in prompts}
        assert peak == 3

    asyncio.run(run())


def test_batch_accepts_async_prompt_stream() -> None:
    async def run() -> None:
        async def prompts():
            for i in range(3):
                yield f"word-{i}"
                await asyncio.sleep(0)

        async def fake_complete(prompt: str, **kwargs: object) -> str:
            return prompt.upper()

        async with Client(throughput=2) as client:
            client.complete = fake_complete  # type: ignore[method-assign]
            results = [item async for item in client.batch(prompts())]
        assert sorted(item.text for item in results) == ["WORD-0", "WORD-1", "WORD-2"]

    asyncio.run(run())


def _fake_response(text: str, *, tool: Tool | None = None, arguments: dict | None = None):
    usage = _usage(10, 5)
    if tool is None:
        return SimpleNamespace(usage=usage, output_text=text, output=[])
    call = SimpleNamespace(type="function_call", name=tool.name, arguments=json.dumps(arguments))
    return SimpleNamespace(usage=usage, output_text="", output=[call])


def test_complete_hits_cache_on_second_call(tmp_path) -> None:
    async def run() -> list[str]:
        cache = Cache(path=tmp_path / "cache.json")
        calls = 0

        async def fake_create(**kwargs):
            nonlocal calls
            calls += 1
            return _fake_response("first response")

        async with Client(cache=cache) as client:
            client._openai.responses.create = fake_create  # type: ignore[method-assign]
            first = await client.complete("same prompt")
            second = await client.complete("same prompt")
        return [first, second], calls

    (first, second), calls = asyncio.run(run())
    assert first == second == "first response"
    assert calls == 1


def test_complete_replicate_disambiguates_repeated_prompts(tmp_path) -> None:
    async def run() -> list[str]:
        cache = Cache(path=tmp_path / "cache.json")
        responses = ["reply-a", "reply-b"]

        async def fake_create(**kwargs):
            return _fake_response(responses.pop(0))

        async with Client(cache=cache) as client:
            client._openai.responses.create = fake_create  # type: ignore[method-assign]
            first = await client.complete("same prompt", replicate=1)
            second = await client.complete("same prompt", replicate=2)
        return [first, second]

    first, second = asyncio.run(run())
    assert (first, second) == ("reply-a", "reply-b")


def test_complete_override_cache_forces_fresh_call(tmp_path) -> None:
    async def run() -> list[str]:
        cache = Cache(path=tmp_path / "cache.json")
        responses = ["reply-a", "reply-b"]

        async def fake_create(**kwargs):
            return _fake_response(responses.pop(0))

        async with Client(cache=cache) as client:
            client._openai.responses.create = fake_create  # type: ignore[method-assign]
            first = await client.complete("same prompt")
            second = await client.complete("same prompt", override_cache=True)
        return [first, second]

    first, second = asyncio.run(run())
    assert (first, second) == ("reply-a", "reply-b")


def test_complete_tool_caches_payload(tmp_path) -> None:
    tool = Tool(name="submit", description="d", parameters={"type": "object", "properties": {}})

    async def run() -> list[dict]:
        cache = Cache(path=tmp_path / "cache.json")
        calls = 0

        async def fake_create(**kwargs):
            nonlocal calls
            calls += 1
            return _fake_response("", tool=tool, arguments={"answer": True})

        async with Client(cache=cache) as client:
            client._openai.responses.create = fake_create  # type: ignore[method-assign]
            first = await client.complete_tool("prompt", tool)
            second = await client.complete_tool("prompt", tool)
        return [first, second], calls

    (first, second), calls = asyncio.run(run())
    assert first == second == {"answer": True}
    assert calls == 1


def test_complete_records_fresh_and_cached_calls_into_context(tmp_path) -> None:
    async def run() -> RunContext:
        cache = Cache(path=tmp_path / "cache.json")
        context = RunContext()

        async def fake_create(**kwargs):
            return _fake_response("hello")

        async with Client(cache=cache, context=context) as client:
            client._openai.responses.create = fake_create  # type: ignore[method-assign]
            await client.complete("same prompt")
            await client.complete("same prompt")
        return context

    context = asyncio.run(run())

    assert context.call_counts() == {"cached": 1, "uncached": 1}
    # The fresh call has a real cost; the cache hit that followed must cost nothing.
    fresh, cached = context.calls
    assert not fresh.cached and fresh.cost_usd > 0 and fresh.latency_s is not None
    assert cached.cached and cached.cost_usd == 0.0 and cached.latency_s is None
    assert context.cost_usd() == fresh.cost_usd
    # The cache hit still reports the tokens of the call that produced it.
    assert cached.input_tokens == fresh.input_tokens
    assert cached.output_tokens == fresh.output_tokens


def test_batch_records_every_call_into_context(tmp_path) -> None:
    async def run() -> tuple[RunContext, list]:
        cache = Cache(path=tmp_path / "cache.json")
        context = RunContext()

        async def fake_create(**kwargs):
            return _fake_response("hello")

        async with Client(cache=cache, context=context) as client:
            client._openai.responses.create = fake_create  # type: ignore[method-assign]
            results = [item async for item in client.batch(["a", "b", "c"])]
        return context, results

    context, results = asyncio.run(run())
    assert len(results) == 3
    assert context.call_counts() == {"cached": 0, "uncached": 3}


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_complete_luna_none_reasoning() -> None:
    costs.reset()
    # override_cache: this test asserts real per-call cost accounting, which a cache
    # hit from a previous run of this same prompt would short-circuit.
    text = asyncio.run(complete("Reply with the single word: pong", override_cache=True))
    assert "pong" in text.lower()
    assert len(costs.calls) == 1
    call = costs.calls[0]
    assert call.model == MODEL
    assert call.input_tokens > 0
    assert call.output_tokens > 0
    assert call.cost_usd > 0
    assert costs.cost_usd == call.cost_usd


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_batch_luna_two_prompts() -> None:
    costs.reset()

    async def run() -> list[str]:
        # override_cache: same reasoning as test_complete_luna_none_reasoning.
        results = [item async for item in batch(
            [
                "Reply with the single word: ping",
                "Reply with the single word: pong",
            ],
            throughput=2,
            override_cache=True,
        )]
        return [item.text.lower() for item in results]

    texts = asyncio.run(run())
    assert len(texts) == 2
    assert any("ping" in text for text in texts)
    assert any("pong" in text for text in texts)
    assert len(costs.calls) == 2
    assert costs.cost_usd > 0
