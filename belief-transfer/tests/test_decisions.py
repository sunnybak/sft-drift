"""Decisions uses the real SDK transport against a fake HTTP server, never live data."""
import asyncio
import json
from copy import deepcopy

import httpx
import pytest
from openai import APIStatusError, AsyncOpenAI

from belief_transfer.generation import llm
from belief_transfer.generation.cache import Cache
from belief_transfer.generation.context import RunContext

QUESTIONS: list[llm.DecisionQuestion] = [
    {"type": "predicate", "name": "endorses", "instructions": "Does the text endorse the claim?"},
    {"type": "choice", "instructions": "Which stance?", "choices": [
        {"value": "endorse", "description": "Supports the claim"}, {"value": False},
    ]},
    {"type": "score", "name": "strength", "instructions": "Rate support.", "levels": [
        {"label": "weak"}, {"label": "strong", "description": "Explicit support"},
    ]},
]
ANSWERS = [
    {"type": "predicate", "name": "endorses", "probability": 0.9},
    {"type": "choice", "name": None, "choice": "endorse", "confidence": 0.8,
     "probabilities": [{"value": "endorse", "probability": 0.9}, {"value": False, "probability": 0.1}]},
    {"type": "refusal", "name": "strength"},
]


def response(answers=None):
    return {"model": llm.DECISION_MODEL, "answers": deepcopy(ANSWERS if answers is None else answers),
            "usage": {"input_tokens": 100, "input_tokens_details": {
                "cached_tokens": 20, "cache_write_tokens": 10},
                "output_tokens": 0, "output_tokens_details": {"reasoning_tokens": 0},
                "total_tokens": 100}}


async def install_transport(client, handler):
    await client._openai.close()
    client._openai = AsyncOpenAI(api_key="test-key", max_retries=llm.RETRIES,
                                timeout=llm.REQUEST_TIMEOUT_SECONDS,
                                http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def test_decision_transport_cache_and_usage(tmp_path):
    async def run():
        requests = []
        def handler(request):
            requests.append(json.loads(request.content))
            assert request.url.path == "/v1/decisions"
            assert request.headers["authorization"] == "Bearer test-key"
            return httpx.Response(200, json=response())
        context = RunContext()
        async with llm.Client(model=llm.DECISION_MODEL, cache=Cache(tmp_path / "cache.jsonl"), context=context) as client:
            await install_transport(client, handler)
            first = await client.decide("I endorse it.", QUESTIONS)
            second = await client.decide("I endorse it.", QUESTIONS)
        assert first == second == response()
        assert requests == [{"model": llm.DECISION_MODEL, "input": "I endorse it.", "questions": QUESTIONS}]
        assert context.call_counts() == {"cached": 1, "uncached": 1}
        assert context.calls[0].cost_usd == pytest.approx(100 * .10 / 1_000_000)
        assert context.calls[1].cost_usd == 0
        assert context.calls[1].input_tokens == 100
        assert context.calls[1].latency_s is None
    asyncio.run(run())


def test_cache_identity_and_controls(tmp_path):
    async def run():
        calls = 0
        def handler(request):
            nonlocal calls
            calls += 1
            return httpx.Response(200, json=response())
        cache = Cache(tmp_path / "cache.jsonl")
        async with llm.Client(model=llm.DECISION_MODEL, cache=cache) as client:
            await install_transport(client, handler)
            await client.decide("p", QUESTIONS)
            changed = deepcopy(QUESTIONS)
            changed[0]["instructions"] = "A different question"
            await client.decide("p", changed)
            await client.decide("p", list(reversed(QUESTIONS)))
            await client.decide("p", QUESTIONS, replicate=1)
            await client.decide("p", QUESTIONS, replicate=1)
            await client.decide("p", QUESTIONS, override_cache=True)
            await client.decide("p", QUESTIONS, use_cache=False)
            assert calls == 6
            assert len(cache) == 4
            assert cache.get(llm.cache_key(llm.DECISION_MODEL, "p")) is None
    asyncio.run(run())


def test_batch_streams_async_inputs_with_bounded_concurrency(tmp_path):
    async def run():
        active = peak = 0
        async def handler(request):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            body = json.loads(request.content)
            await asyncio.sleep(.03 if body["input"] == "0" else .001)
            active -= 1
            return httpx.Response(200, json=response())
        async def prompts():
            for i in range(6):
                yield str(i)
        async with llm.Client(model=llm.DECISION_MODEL, throughput=2, cache=Cache(tmp_path / "cache.jsonl")) as client:
            await install_transport(client, handler)
            items = [item async for item in client.batch_decisions(prompts(), iter(QUESTIONS), use_cache=False)]
        assert peak == 2
        assert items[0].index == 1  # yielded on completion, not input order
        assert sorted((item.index, item.prompt) for item in items) == [(i, str(i)) for i in range(6)]
        assert all(item.payload == json.loads(item.text) == response() for item in items)
    asyncio.run(run())


def test_source_error_does_not_hang_or_leak_workers(tmp_path):
    async def run():
        async def prompts():
            yield "one"
            raise ValueError("broken source")
        async with llm.Client(model=llm.DECISION_MODEL, cache=Cache(tmp_path / "cache.jsonl")) as client:
            async def handler(request):
                await asyncio.sleep(10)
                return httpx.Response(200, json=response())
            await install_transport(client, handler)
            async def collect():
                return [item async for item in client.batch_decisions(prompts(), QUESTIONS)]
            with pytest.raises(ValueError, match="broken source"):
                await asyncio.wait_for(collect(), timeout=1)
            assert not [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    asyncio.run(run())


def test_early_close_cancels_workers(tmp_path):
    async def run():
        pending = cancelled = 0
        async def handler(request):
            nonlocal pending, cancelled
            if json.loads(request.content)["input"] == "slow":
                pending += 1
                try:
                    await asyncio.sleep(10)
                finally:
                    pending -= 1
                    cancelled += 1
            return httpx.Response(200, json=response())
        async with llm.Client(model=llm.DECISION_MODEL, throughput=2, cache=Cache(tmp_path / "cache.jsonl")) as client:
            await install_transport(client, handler)
            stream = client.batch_decisions(["slow", "fast", "slow"], QUESTIONS, use_cache=False)
            await anext(stream)
            await stream.aclose()
            await asyncio.sleep(0)
            assert pending == 0
            assert cancelled > 0
    asyncio.run(run())


def test_retry_on_rate_limit(tmp_path):
    async def run():
        calls = 0
        def handler(request):
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(429, headers={"retry-after-ms": "1"}, json={"error": {"message": "rate limited"}})
            return httpx.Response(200, json=response())
        async with llm.Client(model=llm.DECISION_MODEL, cache=Cache(tmp_path / "cache.jsonl")) as client:
            await install_transport(client, handler)
            assert await client.decide("p", QUESTIONS) == response()
        assert calls == 2
    asyncio.run(run())


def test_batch_api_error_propagates(tmp_path):
    async def run():
        cache = Cache(tmp_path / "cache.jsonl")
        async with llm.Client(model=llm.DECISION_MODEL, cache=cache) as client:
            await install_transport(client, lambda request: httpx.Response(400, json={"error": {"message": "bad questions"}}))
            with pytest.raises(APIStatusError):
                async for _ in client.batch_decisions(["p", "q"], QUESTIONS):
                    pass
            assert len(cache) == 0
    asyncio.run(run())


@pytest.mark.parametrize("body", [{"answers": ANSWERS}, response([])])
def test_incomplete_response_not_cached(tmp_path, body):
    async def run():
        cache = Cache(tmp_path / "cache.jsonl")
        async with llm.Client(model=llm.DECISION_MODEL, cache=cache) as client:
            await install_transport(client, lambda request: httpx.Response(200, json=body))
            with pytest.raises(RuntimeError):
                await client.decide("p", QUESTIONS)
            assert len(cache) == 0
    asyncio.run(run())


def test_invalid_configuration_rejected_locally(tmp_path):
    async def run():
        async with llm.Client(cache=Cache(tmp_path / "cache.jsonl")) as client:
            with pytest.raises(ValueError, match="model"):
                await client.decide("p", QUESTIONS)
            client.model = llm.DECISION_MODEL
            with pytest.raises(ValueError, match="1 and 200"):
                await client.decide("p", [])
            with pytest.raises(ValueError, match="throughput"):
                async for _ in client.batch_decisions([], QUESTIONS, throughput=0):
                    pass
    asyncio.run(run())


def test_module_helpers(tmp_path, monkeypatch):
    real_client = llm.Client
    def factory(*args, **kwargs):
        client = real_client(*args, cache=Cache(tmp_path / "cache.jsonl"), **kwargs)
        async def post(path, *, body, cast_to):
            assert body["model"] == llm.DECISION_MODEL
            return response()
        monkeypatch.setattr(client._openai, "post", post)
        return client
    monkeypatch.setattr(llm, "Client", factory)
    async def run():
        assert await llm.decide("p", QUESTIONS) == response()
        assert len([item async for item in llm.batch_decisions(["a", "b"], QUESTIONS)]) == 2
    asyncio.run(run())


@pytest.mark.parametrize("tokens,rate", [(272_000, .10), (272_001, .20)])
def test_decision_pricing_is_input_only(tokens, rate):
    from openai.types.responses import ResponseUsage
    usage = response()["usage"]
    usage.update(input_tokens=tokens, output_tokens=1000, total_tokens=tokens + 1000)
    assert llm.estimate_decision_cost_usd(llm.DECISION_MODEL, ResponseUsage.model_validate(usage)) == pytest.approx(tokens * rate / 1_000_000)


def test_score_answer_preserved(tmp_path):
    async def run():
        expected = response([{
            "type": "score", "name": "strength", "score": .9, "confidence": .8,
            "probabilities": [{"label": "weak", "value": 0, "probability": .1},
                              {"label": "strong", "value": 1, "probability": .9}],
        }])
        async with llm.Client(model=llm.DECISION_MODEL, cache=Cache(tmp_path / "cache.jsonl")) as client:
            await install_transport(client, lambda request: httpx.Response(200, json=expected))
            assert await client.decide("p", [QUESTIONS[2]]) == expected
    asyncio.run(run())


@pytest.mark.needs_api
def test_live_decisions_single_and_batch(tmp_path):
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    async def run():
        questions: list[llm.DecisionQuestion] = [{
            "type": "predicate", "name": "red",
            "instructions": "Does the text explicitly say the square is red?",
        }]
        context = RunContext()
        async with llm.Client(model=llm.DECISION_MODEL, throughput=2,
                              cache=Cache(tmp_path / "cache.jsonl"), context=context) as client:
            single = await client.decide("The square is red.", questions, use_cache=False)
            assert single["answers"][0]["type"] == "predicate"
            items = [item async for item in client.batch_decisions(
                ["The square is red.", "The square is blue."], questions, use_cache=False)]
        assert sorted(item.index for item in items) == [0, 1]
        assert all(item.payload["answers"][0]["type"] == "predicate" for item in items)
        assert context.call_counts() == {"cached": 0, "uncached": 3}
        assert context.cost_usd() > 0
    asyncio.run(run())
