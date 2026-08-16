from pathlib import Path

import yaml

from belief_transfer.analysis.report import build_result, result_from_dict, write_result
from belief_transfer.generation.context import CallRecord, RunContext
from belief_transfer.schemas import BackendInfo


def _context(cost_usd: float, latency_s: float | None, *, cached: bool = False) -> RunContext:
    context = RunContext()
    context.record(
        CallRecord(
            cached=cached,
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


def _result(context: RunContext, datapoints: int = 4, **kwargs):
    return build_result(
        context,
        stage="datagen",
        experiment_id="exp",
        run_id="run",
        datapoints=datapoints,
        artifacts=[],
        **kwargs,
    )


def test_build_result_has_no_lifetime_section() -> None:
    result = _result(_context(0.01, 1.0))

    # lifetime needs whatever is already on disk, which build_result cannot see.
    assert result.lifetime is None
    assert result.last_run.datapoints == 4
    assert result.last_run.cost_usd == 0.01


def test_build_result_stamps_provenance() -> None:
    result = _result(
        _context(0.01, 1.0),
        backend=BackendInfo(backend="cuda", device="RTX 4090", dtype="bfloat16"),
        config_sha="abc123",
    )

    assert result.schema_version == 1
    assert result.config_sha == "abc123"
    assert result.backend is not None and result.backend.backend == "cuda"
    # Best-effort: "" in a tarball with no .git, a short sha in this repo.
    assert isinstance(result.code_revision, str)


def test_stage_specific_facts_live_under_metrics() -> None:
    result = _result(_context(0.01, 1.0), metrics={"gating": {"pairs_kept": 3}})
    assert result.metrics == {"gating": {"pairs_kept": 3}}


def test_write_result_first_write_makes_lifetime_equal_last_run(tmp_path: Path) -> None:
    path = write_result(_result(_context(0.01, 1.0)), path=tmp_path / "r.yaml")

    written = yaml.safe_load(path.read_text())
    assert written["lifetime"]["runs"] == 1
    assert written["lifetime"]["datapoints"] == 4
    assert written["lifetime"]["cost_usd"] == written["last_run"]["cost_usd"]
    assert written["lifetime"]["calls"] == written["last_run"]["calls"]
    assert written["lifetime"]["tokens"] == written["last_run"]["tokens"]


def test_write_result_accumulates_lifetime_across_writes(tmp_path: Path) -> None:
    path = tmp_path / "r.yaml"

    write_result(_result(_context(0.01, 1.0), datapoints=4), path=path)
    write_result(_result(_context(0.03, 3.0), datapoints=6), path=path)

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


def test_write_result_lifetime_survives_mixed_cached_and_uncached_calls(tmp_path: Path) -> None:
    path = tmp_path / "r.yaml"

    write_result(_result(_context(0.02, 2.0), datapoints=2), path=path)
    write_result(_result(_context(0.0, None, cached=True), datapoints=2), path=path)

    written = yaml.safe_load(path.read_text())
    lifetime = written["lifetime"]
    assert lifetime["runs"] == 2
    assert lifetime["cost_usd"] == 0.02  # the cached call added nothing
    assert lifetime["calls"] == {"cached": 1, "uncached": 1}
    assert lifetime["tokens"]["cached"] == {"input_tokens": 100, "output_tokens": 50}
    assert lifetime["tokens"]["uncached"] == {"input_tokens": 100, "output_tokens": 50}
    # mean latency only ever counts timed (uncached) calls.
    assert lifetime["mean_latency_s"] == 2.0


def test_reads_pre_metrics_reports_and_keeps_accumulating(tmp_path: Path) -> None:
    """A report written before `metrics` existed must still fold into lifetime.

    Otherwise the first write after the format change would look like the first run of
    that id, resetting `runs`/`datapoints` and understating what the already-cached
    content cost -- exactly the number `lifetime` exists to remember.
    """
    path = tmp_path / "r.yaml"
    legacy = {
        "experiment": "exp",
        "run_id": "run",
        "stage": "datagen",
        "artifacts": ["data/generated/exp/run/documents.jsonl"],
        "gating": {"pairs_kept": 44},
        "last_run": {
            "datapoints": 8,
            "cost_usd": 0.05,
            "calls": {"cached": 0, "uncached": 4},
            "tokens": {
                "cached": {"input_tokens": 0, "output_tokens": 0},
                "uncached": {"input_tokens": 400, "output_tokens": 200},
            },
            "mean_latency_s": 2.0,
        },
        "lifetime": {
            "runs": 3,
            "datapoints": 24,
            "cost_usd": 0.15,
            "calls": {"cached": 2, "uncached": 12},
            "tokens": {
                "cached": {"input_tokens": 200, "output_tokens": 100},
                "uncached": {"input_tokens": 1200, "output_tokens": 600},
            },
            "mean_latency_s": 2.0,
        },
    }
    path.write_text(yaml.safe_dump(legacy, sort_keys=False))

    parsed = result_from_dict(legacy)
    assert parsed.metrics == {"gating": {"pairs_kept": 44}}
    assert parsed.lifetime is not None and parsed.lifetime.runs == 3

    write_result(_result(_context(0.01, 1.0), datapoints=2), path=path)
    written = yaml.safe_load(path.read_text())
    assert written["lifetime"]["runs"] == 4  # 3 prior runs plus this one
    assert written["lifetime"]["datapoints"] == 26  # 24 + 2
    assert written["lifetime"]["cost_usd"] == 0.16  # 0.15 + 0.01


def test_legacy_extra_keys_are_folded_into_metrics() -> None:
    # `extra` merged arbitrary keys in at the top level; anything outside the envelope
    # is a stage-specific fact by definition.
    parsed = result_from_dict(
        {
            "experiment": "exp",
            "run_id": "run",
            "stage": "sft",
            "sft": {"positive": {"n_samples": 106}},
            "trajectory": {"last_passing_step": 70},
            "last_run": {"datapoints": 212},
        }
    )
    assert parsed.metrics == {
        "sft": {"positive": {"n_samples": 106}},
        "trajectory": {"last_passing_step": 70},
    }
