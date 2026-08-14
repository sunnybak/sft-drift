"""Persisted summaries of one pipeline-stage invocation: cost, tokens, latency, artifacts.

Written once a stage finishes (see `runs.run_datagen`) to
`data/results/<experiment_id>/<run_id>/<stage>.yaml`. Built from the stage's
`generation.context.RunContext` -- the per-call cost/token/latency ledger accumulated
across every `generation.llm.Client` call the stage made -- plus a few pipeline-level
facts the context itself doesn't know: which stage ran, how many datapoints it
produced, and which files it wrote.

Stage is the only separation these reports need: whatever LLM calls a stage makes
(generating documents, judging them, or anything else) all count toward that one
stage's cost, aggregated into a single total rather than split further by call
purpose -- a separate file per stage already exists for that (`datagen.yaml`,
`sft.yaml`, `belief_eval.yaml`, `action_eval.yaml`).

The report has two sections:

    last_run   this invocation only, from its `RunContext`
    lifetime   folded in from the report already on disk (if any) plus this
               invocation, so it accumulates across every time this run id has been
               run, even across separate process invocations

Caching (see `generation.cache`) is exactly why this split matters: once a run's
prompts are cached, re-running it costs ~$0 and reports as such in `last_run`, but
`lifetime` still remembers what was actually spent generating that cached content in
the first place, across however many times the run id has been invoked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from belief_transfer.generation.context import RunContext

RESULTS_DIR = Path(__file__).resolve().parents[3] / "data" / "results"
ROOT = RESULTS_DIR.parents[1]

_EMPTY_STATS: dict[str, Any] = {
    "cost_usd": 0.0,
    "calls": {"cached": 0, "uncached": 0},
    "tokens": {
        "cached": {"input_tokens": 0, "output_tokens": 0},
        "uncached": {"input_tokens": 0, "output_tokens": 0},
    },
    "mean_latency_s": None,
}


def results_path(experiment_id: str, run_id: str, stage: str) -> Path:
    """Where a stage's results live: `data/results/<experiment_id>/<run_id>/<stage>.yaml`."""
    return RESULTS_DIR / experiment_id / run_id / f"{stage}.yaml"


def _artifact_str(path: Path, root: Path) -> str:
    """`path` relative to `root` (the repo root) so the report doesn't embed a
    machine-local absolute path, or the resolved absolute path if `path` falls
    outside `root` entirely (e.g. a test writing to a tmp directory)."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(resolved)


def _stats(context: RunContext) -> dict[str, Any]:
    return {
        "cost_usd": round(context.cost_usd(), 6),
        "calls": context.call_counts(),
        "tokens": context.tokens(),
        "mean_latency_s": context.mean_latency_s(),
    }


def _sum_latency_s(mean_latency_s: float | None, uncached_calls: int) -> float:
    """Invert `mean_latency_s = sum_latency_s / uncached_calls` to recover the sum --
    cheaper than persisting the sum separately, since every report already stores
    both factors."""
    return (mean_latency_s or 0.0) * uncached_calls


def _merge_stats(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    """Fold one invocation's stats (`current`) onto the running lifetime total
    (`previous`, or `None` the first time)."""
    previous = previous or _EMPTY_STATS
    calls = {
        bucket: previous["calls"][bucket] + current["calls"][bucket]
        for bucket in ("cached", "uncached")
    }
    tokens = {
        bucket: {
            field: previous["tokens"][bucket][field] + current["tokens"][bucket][field]
            for field in ("input_tokens", "output_tokens")
        }
        for bucket in ("cached", "uncached")
    }
    sum_latency_s = _sum_latency_s(
        previous["mean_latency_s"], previous["calls"]["uncached"]
    ) + _sum_latency_s(current["mean_latency_s"], current["calls"]["uncached"])
    return {
        "cost_usd": round(previous["cost_usd"] + current["cost_usd"], 6),
        "calls": calls,
        "tokens": tokens,
        "mean_latency_s": sum_latency_s / calls["uncached"] if calls["uncached"] else None,
    }


def _merge_lifetime(previous: dict[str, Any] | None, last_run: dict[str, Any]) -> dict[str, Any]:
    """Fold one invocation's `last_run` summary onto the prior `lifetime` total."""
    stats = _merge_stats(previous, last_run)
    return {
        "runs": (previous["runs"] if previous else 0) + 1,
        "datapoints": (previous["datapoints"] if previous else 0) + last_run["datapoints"],
        **stats,
    }


def build_report(
    context: RunContext,
    *,
    stage: str,
    experiment_id: str,
    run_id: str,
    datapoints: int,
    artifacts: list[Path],
    gating: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Assemble one invocation's report: identity fields plus its `last_run` summary.

    `lifetime` is added later by `write_report`, which needs the report already on
    disk (if any) to fold this invocation into -- something `build_report` itself,
    working only from `context`, cannot see.

    `gating`, if given (see `dataset.gate.gating_summary`), is a snapshot of the
    *current* corpus's pairs kept/dropped -- not accumulated into `lifetime` the way
    cost is, since it describes the corpus as it stands after this invocation, not
    additional work done.

    `extra`, if given, is merged in as additional top-level report keys -- the generic
    version of what `gating` does for `datagen`, for stages (e.g. `sft`) whose
    stage-specific facts (checkpoint path, loss, steps) don't fit `RunContext`'s
    cost/token/latency shape and aren't corpus-gating information either.
    """
    report: dict[str, Any] = {
        "experiment": experiment_id,
        "run_id": run_id,
        "stage": stage,
        "artifacts": [_artifact_str(path, root) for path in artifacts],
    }
    if gating is not None:
        report["gating"] = gating
    if extra:
        report.update(extra)
    report["last_run"] = {"datapoints": datapoints, **_stats(context)}
    return report


def write_report(
    report: dict[str, Any],
    *,
    experiment_id: str,
    run_id: str,
    stage: str,
    path: Path | None = None,
) -> Path:
    """Write `report` (as built by `build_report`) to `path`, or its conventional path.

    Reads whatever report is already there, folds `report["last_run"]` into its
    `lifetime` section (starting fresh if there is none), and writes both sections
    back -- so `lifetime` accumulates across every invocation of this run id, however
    many process runs have written this file.
    """
    path = path or results_path(experiment_id, run_id, stage)
    previous = yaml.safe_load(path.read_text()) if path.exists() else None
    report = {**report, "lifetime": _merge_lifetime((previous or {}).get("lifetime"), report["last_run"])}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(report, sort_keys=False))
    return path
