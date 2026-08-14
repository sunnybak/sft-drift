"""Model-ability benchmarks: one folder per benchmark, each holding a small script and
its JSON dataset.

    benchmarks/
        <benchmark-id>/
            benchmark.py    what to ask, how to score it, where the bar is
            items.json      the dataset

Distinct from `inference.bench`, which calibrates the *machine* (batch size, VRAM) and
checks that inference and training work on this box at all. These measure what a
*model* can do -- and therefore what fine-tuning might damage. That difference is the
reason they get their own home: `hardware_profile.yaml` answers "is this box set up
right", and a benchmark here answers "is this checkpoint still able to do the thing an
eval depends on".

Adding one is a folder plus a line in `BENCHMARKS`. The registry is an explicit dict
rather than a filesystem scan with `importlib`: AGENTS.md warns off generic plugin
systems, and with a handful of benchmarks an explicit mapping is shorter, greppable,
and fails at import rather than at run time.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from belief_transfer.benchmarks.choice import benchmark as choice
from belief_transfer.schemas import BenchmarkResult

BENCHMARKS = {choice.ID: choice}

BENCHMARKS_DIR = Path(__file__).resolve().parent


def load_items(benchmark_id: str) -> list[dict]:
    """Read `<benchmark-id>/items.json`. Kept here rather than in each benchmark so a
    new benchmark is a dataset plus a scoring function, not a dataset plus a loader.
    """
    path = BENCHMARKS_DIR / benchmark_id / "items.json"
    items = json.loads(path.read_text())
    if not items:
        raise ValueError(f"{path} is empty")
    return items


def run_benchmark(benchmark_id: str, model, *, model_key: str, adapter: str | None = None) -> BenchmarkResult:
    """Run one benchmark against an already-constructed model and wrap its numbers in a
    `BenchmarkResult`.

    The model is passed in rather than built here so the caller decides what is being
    measured -- base checkpoint, M+, or M- -- and so tests can pass a stub.
    """
    if benchmark_id not in BENCHMARKS:
        raise KeyError(f"unknown benchmark {benchmark_id!r} -- known: {', '.join(sorted(BENCHMARKS))}")
    module = BENCHMARKS[benchmark_id]
    items = load_items(benchmark_id)
    outcome = module.evaluate(model, items, model_key=model_key)
    return BenchmarkResult(
        benchmark=benchmark_id,
        model=model_key,
        adapter=adapter,
        passed=outcome["passed"],
        metrics=outcome["metrics"],
        n_items=len(items),
        ran_at=datetime.now(timezone.utc).isoformat(),
        failures=outcome.get("failures", []),
        thresholds=outcome.get("thresholds", {}),
        calibrated=outcome.get("calibrated", True),
    )
