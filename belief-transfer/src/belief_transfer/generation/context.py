"""Stateful, run-scoped tracking of LLM call cost, tokens, and latency.

One `RunContext` is created per pipeline-stage invocation (see `runs.run_datagen`) and
threaded through every `generation.llm.Client` call made during it. `analysis.report`
turns the accumulated calls into a persisted summary once the stage finishes. Stage is
the only separation these reports need (`data/results/<experiment_id>/<run_id>/
<stage>.yaml`); a stage's LLM calls -- whether generating documents or judging them --
all count toward that one stage's cost, so a `RunContext` reports one aggregate total
rather than splitting further by what a call was for.

Safe for concurrent use by the many asyncio tasks `Client.batch` runs concurrently:
recording a call holds one `threading.Lock` for the duration of a single list append,
the same reasoning as `generation.cache.Cache`.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CallRecord:
    """One LLM call, whether served fresh or from the cache.

    Cached calls always cost $0 and have no `latency_s` -- they never issued a
    request -- but still report the token counts of the call that originally
    populated the cache entry, so a report can show what the run *would have* cost
    without the cache.
    """

    cached: bool
    cost_usd: float
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cache_write_tokens: int
    reasoning_tokens: int
    latency_s: float | None


@dataclass
class RunContext:
    """Accumulates `CallRecord`s for one run and reports aggregate totals."""

    calls: list[CallRecord] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def record(self, call: CallRecord) -> None:
        with self._lock:
            self.calls.append(call)

    def cost_usd(self) -> float:
        return sum(call.cost_usd for call in self.calls)

    def call_counts(self) -> dict[str, int]:
        return {
            "cached": sum(1 for call in self.calls if call.cached),
            "uncached": sum(1 for call in self.calls if not call.cached),
        }

    def tokens(self) -> dict[str, dict[str, int]]:
        """Input/output token totals, split by whether the call was a cache hit."""

        def totals(subset: list[CallRecord]) -> dict[str, int]:
            return {
                "input_tokens": sum(call.input_tokens for call in subset),
                "output_tokens": sum(call.output_tokens for call in subset),
            }

        return {
            "cached": totals([call for call in self.calls if call.cached]),
            "uncached": totals([call for call in self.calls if not call.cached]),
        }

    def mean_latency_s(self) -> float | None:
        """Mean latency of actual requests (cache hits have none and are excluded)."""
        timed = [call.latency_s for call in self.calls if call.latency_s is not None]
        if not timed:
            return None
        return sum(timed) / len(timed)
