from belief_transfer.generation.context import CallRecord, RunContext


def _call(
    cached: bool,
    cost_usd: float,
    input_tokens: int,
    output_tokens: int,
    latency_s: float | None,
) -> CallRecord:
    return CallRecord(
        cached=cached,
        cost_usd=cost_usd,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=0,
        cache_write_tokens=0,
        reasoning_tokens=0,
        latency_s=latency_s,
    )


def test_cost_usd_sums_all_calls() -> None:
    context = RunContext()
    context.record(_call(False, 0.01, 100, 50, 1.0))
    context.record(_call(False, 0.02, 200, 20, 2.0))

    assert context.cost_usd() == 0.03


def test_cached_calls_never_contribute_cost() -> None:
    context = RunContext()
    context.record(_call(False, 0.01, 100, 50, 1.0))
    context.record(_call(True, 0.0, 100, 50, None))

    assert context.cost_usd() == 0.01
    assert context.call_counts() == {"cached": 1, "uncached": 1}


def test_tokens_split_by_cached_and_uncached() -> None:
    context = RunContext()
    context.record(_call(False, 0.01, 100, 50, 1.0))
    context.record(_call(True, 0.0, 30, 10, None))

    tokens = context.tokens()
    assert tokens["uncached"] == {"input_tokens": 100, "output_tokens": 50}
    assert tokens["cached"] == {"input_tokens": 30, "output_tokens": 10}


def test_mean_latency_excludes_cache_hits() -> None:
    context = RunContext()
    context.record(_call(False, 0.01, 100, 50, 1.0))
    context.record(_call(False, 0.01, 100, 50, 3.0))
    context.record(_call(True, 0.0, 100, 50, None))

    assert context.mean_latency_s() == 2.0


def test_mean_latency_is_none_with_no_timed_calls() -> None:
    context = RunContext()
    context.record(_call(True, 0.0, 100, 50, None))

    assert context.mean_latency_s() is None
