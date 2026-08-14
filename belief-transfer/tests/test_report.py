from pathlib import Path

import yaml

from belief_transfer.analysis.report import build_report, write_report
from belief_transfer.generation.context import CallRecord, RunContext


def _context(cost_usd: float, latency_s: float) -> RunContext:
    context = RunContext()
    context.record(
        CallRecord(
            cached=False,
            cost_usd=cost_usd,
            input_tokens=100,
            output_tokens=50,
            cached_tokens=0,
            cache_write_tokens=0,
            reasoning_tokens=0,
            latency_s=latency_s,
        )
    )
    return context


def test_build_report_has_no_lifetime_section() -> None:
    report = build_report(
        _context(0.01, 1.0),
        stage="datagen",
        experiment_id="exp",
        run_id="run",
        datapoints=4,
        artifacts=[],
    )

    assert "lifetime" not in report
    assert report["last_run"]["datapoints"] == 4
    assert report["last_run"]["cost_usd"] == 0.01


def test_write_report_first_write_makes_lifetime_equal_last_run(tmp_path: Path) -> None:
    report = build_report(
        _context(0.01, 1.0),
        stage="datagen",
        experiment_id="exp",
        run_id="run",
        datapoints=4,
        artifacts=[],
    )
    path = write_report(
        report, experiment_id="exp", run_id="run", stage="datagen", path=tmp_path / "r.yaml"
    )

    written = yaml.safe_load(path.read_text())
    assert written["lifetime"]["runs"] == 1
    assert written["lifetime"]["datapoints"] == 4
    assert written["lifetime"]["cost_usd"] == written["last_run"]["cost_usd"]
    assert written["lifetime"]["calls"] == written["last_run"]["calls"]
    assert written["lifetime"]["tokens"] == written["last_run"]["tokens"]


def test_write_report_accumulates_lifetime_across_writes(tmp_path: Path) -> None:
    path = tmp_path / "r.yaml"

    first = build_report(
        _context(0.01, 1.0), stage="datagen", experiment_id="exp", run_id="run", datapoints=4, artifacts=[]
    )
    write_report(first, experiment_id="exp", run_id="run", stage="datagen", path=path)

    second = build_report(
        _context(0.03, 3.0), stage="datagen", experiment_id="exp", run_id="run", datapoints=6, artifacts=[]
    )
    write_report(second, experiment_id="exp", run_id="run", stage="datagen", path=path)

    written = yaml.safe_load(path.read_text())
    assert written["last_run"]["datapoints"] == 6  # last_run reflects only the 2nd write
    assert written["last_run"]["cost_usd"] == 0.03

    lifetime = written["lifetime"]
    assert lifetime["runs"] == 2
    assert lifetime["datapoints"] == 10  # 4 + 6, across both writes
    assert lifetime["cost_usd"] == 0.04  # 0.01 + 0.03
    assert lifetime["calls"] == {"cached": 0, "uncached": 2}
    assert lifetime["tokens"]["uncached"] == {"input_tokens": 200, "output_tokens": 100}
    # weighted mean of the two calls' latencies: (1.0 + 3.0) / 2
    assert lifetime["mean_latency_s"] == 2.0


def test_write_report_lifetime_survives_mixed_cached_and_uncached_calls(tmp_path: Path) -> None:
    path = tmp_path / "r.yaml"

    fresh = RunContext()
    fresh.record(
        CallRecord(
            cached=False,
            cost_usd=0.02,
            input_tokens=100,
            output_tokens=50,
            cached_tokens=0,
            cache_write_tokens=0,
            reasoning_tokens=0,
            latency_s=2.0,
        )
    )
    first = build_report(
        fresh, stage="datagen", experiment_id="exp", run_id="run", datapoints=2, artifacts=[]
    )
    write_report(first, experiment_id="exp", run_id="run", stage="datagen", path=path)

    cached = RunContext()
    cached.record(
        CallRecord(
            cached=True,
            cost_usd=0.0,
            input_tokens=100,
            output_tokens=50,
            cached_tokens=0,
            cache_write_tokens=0,
            reasoning_tokens=0,
            latency_s=None,
        )
    )
    second = build_report(
        cached, stage="datagen", experiment_id="exp", run_id="run", datapoints=2, artifacts=[]
    )
    write_report(second, experiment_id="exp", run_id="run", stage="datagen", path=path)

    written = yaml.safe_load(path.read_text())
    lifetime = written["lifetime"]
    assert lifetime["runs"] == 2
    assert lifetime["cost_usd"] == 0.02  # the cached call added nothing
    assert lifetime["calls"] == {"cached": 1, "uncached": 1}
    assert lifetime["tokens"]["cached"] == {"input_tokens": 100, "output_tokens": 50}
    assert lifetime["tokens"]["uncached"] == {"input_tokens": 100, "output_tokens": 50}
    # mean latency only ever counts timed (uncached) calls.
    assert lifetime["mean_latency_s"] == 2.0
