"""Persisted summaries of one pipeline-stage invocation: cost, tokens, latency, artifacts.

Written once a stage finishes (see `stages`) to
`data/results/<experiment_id>/<run_id>/<stage>.yaml`. Built from the stage's
`generation.context.RunContext` -- the per-call cost/token/latency ledger accumulated
across every `generation.llm.Client` call the stage made -- plus a few pipeline-level
facts the context itself doesn't know: which stage ran, how many datapoints it
produced, which files it wrote, and what produced them (`schemas.BackendInfo`).

Stage is the only separation these reports need: whatever LLM calls a stage makes
(generating documents, judging them, or anything else) all count toward that one
stage's cost, aggregated into a single total rather than split further by call
purpose -- a separate file per stage already exists for that.

The report has two sections:

    last_run   this invocation only, from its `RunContext`
    lifetime   folded in from the report already on disk (if any) plus this
               invocation, so it accumulates across every time this run id has been
               run, even across separate process invocations

Caching (see `generation.cache`) is exactly why this split matters: once a run's
prompts are cached, re-running it costs ~$0 and reports as such in `last_run`, but
`lifetime` still remembers what was actually spent generating that cached content in
the first place, across however many times the run id has been invoked.

Stage-specific facts (a corpus's gating outcome, a training run's losses) go in
`metrics`. That used to be three separate escape hatches -- a `gating` key, an `sft`
key, and a generic `extra` -- which were three names for the same thing. `result_from_dict`
still reads those older reports so `lifetime` keeps accumulating across the change
rather than restarting from zero.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import (
    BackendInfo,
    CallCounts,
    LastRun,
    Lifetime,
    RunResult,
    TokenCounts,
    TokenLedger,
)

RESULTS_DIR = Path(__file__).resolve().parents[3] / "data" / "results"
ROOT = RESULTS_DIR.parents[1]

_ENVELOPE_KEYS = frozenset(
    {
        "schema_version",
        "experiment",
        "run_id",
        "stage",
        "artifacts",
        "config_sha",
        "code_revision",
        "backend",
        "metrics",
        "last_run",
        "lifetime",
    }
)


def results_path(experiment_id: str, run_id: str, stage: str) -> Path:
    """Where a stage's results live: `data/results/<experiment_id>/<run_id>/<stage>.yaml`."""
    return RESULTS_DIR / experiment_id / run_id / f"{stage}.yaml"


def code_revision() -> str:
    """Short git revision of the working tree, or "" if it cannot be determined.

    Best-effort by design: AGENTS.md asks for the code revision "where practical", and a
    stage must not fail because it ran from a tarball with no `.git`.
    """
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _artifact_str(path: Path, root: Path) -> str:
    """`path` relative to `root` (the repo root) so the report doesn't embed a
    machine-local absolute path, or the resolved absolute path if `path` falls
    outside `root` entirely (e.g. a test writing to a tmp directory)."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(resolved)


def _last_run(context: RunContext, datapoints: int) -> LastRun:
    counts = context.call_counts()
    tokens = context.tokens()
    return LastRun(
        datapoints=datapoints,
        cost_usd=round(context.cost_usd(), 6),
        calls=CallCounts(**counts),
        tokens=TokenLedger(
            cached=TokenCounts(**tokens["cached"]),
            uncached=TokenCounts(**tokens["uncached"]),
        ),
        mean_latency_s=context.mean_latency_s(),
    )


def _sum_latency_s(mean_latency_s: float | None, uncached_calls: int) -> float:
    """Invert `mean_latency_s = sum_latency_s / uncached_calls` to recover the sum --
    cheaper than persisting the sum separately, since every report already stores
    both factors."""
    return (mean_latency_s or 0.0) * uncached_calls


def merge_lifetime(previous: Lifetime | None, last_run: LastRun) -> Lifetime:
    """Fold one invocation's `last_run` onto the prior `lifetime` total."""
    previous = previous or Lifetime()
    calls = CallCounts(
        cached=previous.calls.cached + last_run.calls.cached,
        uncached=previous.calls.uncached + last_run.calls.uncached,
    )
    tokens = TokenLedger(
        cached=TokenCounts(
            input_tokens=previous.tokens.cached.input_tokens + last_run.tokens.cached.input_tokens,
            output_tokens=previous.tokens.cached.output_tokens + last_run.tokens.cached.output_tokens,
        ),
        uncached=TokenCounts(
            input_tokens=previous.tokens.uncached.input_tokens + last_run.tokens.uncached.input_tokens,
            output_tokens=previous.tokens.uncached.output_tokens + last_run.tokens.uncached.output_tokens,
        ),
    )
    sum_latency_s = _sum_latency_s(previous.mean_latency_s, previous.calls.uncached) + _sum_latency_s(
        last_run.mean_latency_s, last_run.calls.uncached
    )
    return Lifetime(
        runs=previous.runs + 1,
        datapoints=previous.datapoints + last_run.datapoints,
        cost_usd=round(previous.cost_usd + last_run.cost_usd, 6),
        calls=calls,
        tokens=tokens,
        mean_latency_s=sum_latency_s / calls.uncached if calls.uncached else None,
    )


def build_result(
    context: RunContext,
    *,
    stage: str,
    experiment_id: str,
    run_id: str,
    datapoints: int,
    artifacts: list[Path],
    metrics: dict[str, Any] | None = None,
    backend: BackendInfo | None = None,
    config_sha: str = "",
    root: Path = ROOT,
) -> RunResult:
    """Assemble one invocation's result: identity, provenance, and its `last_run` ledger.

    `lifetime` is added later by `write_result`, which needs the report already on disk
    (if any) to fold this invocation into -- something this function, working only from
    `context`, cannot see.

    `metrics` is whatever the stage measured (see `RunResult.metrics`): a corpus's
    gating outcome for datagen, per-arm training summaries for sft.
    """
    return RunResult(
        experiment=experiment_id,
        run_id=run_id,
        stage=stage,
        artifacts=[_artifact_str(path, root) for path in artifacts],
        config_sha=config_sha,
        code_revision=code_revision(),
        backend=backend,
        metrics=metrics or {},
        last_run=_last_run(context, datapoints),
    )


def result_from_dict(raw: dict[str, Any]) -> RunResult:
    """Parse a report off disk, in either the current or the pre-`metrics` layout.

    Older reports put stage-specific facts at the top level (`gating`, `sft`, or
    anything `extra` merged in). Folding them into `metrics` on read is what lets
    `lifetime` keep accumulating across the format change instead of silently
    restarting -- which would make a re-run look like the first run of that id, and
    understate what the cached content cost.
    """
    if raw.get("schema_version"):
        return RunResult.model_validate(raw)

    envelope = {key: value for key, value in raw.items() if key in _ENVELOPE_KEYS}
    # Anything outside the envelope was a stage-specific fact -- `gating`, `sft`, or a
    # key `extra` merged in -- and is now `metrics`.
    metrics = {key: value for key, value in raw.items() if key not in _ENVELOPE_KEYS}
    return RunResult.model_validate({**envelope, "metrics": metrics})


def _previous_result(path: Path) -> RunResult | None:
    """The report already at `path`, or None if there isn't a usable one.

    Returns None rather than raising when the file is not a report at all. Historically
    `data/results/<exp>/<run>/efficacy.yaml` held the efficacy *summary*, which is now
    `efficacy_summary.yaml` -- but old runs still have the summary at that path, and
    inheriting a `lifetime` is not worth destroying a completed scoring run over. Losing
    accumulated cost for one run id is recoverable; losing the run's results is not.
    """
    if not path.exists():
        return None
    try:
        return result_from_dict(yaml.safe_load(path.read_text()))
    except (ValidationError, AttributeError, TypeError):
        return None


def write_result(
    result: RunResult,
    *,
    path: Path | None = None,
) -> Path:
    """Write `result` to `path`, or its conventional path, folding in `lifetime`.

    Reads whatever report is already there, accumulates its `lifetime` with this
    invocation's `last_run`, and writes both sections back -- so `lifetime` grows across
    every invocation of this run id, however many process runs have written the file.
    """
    path = path or results_path(result.experiment, result.run_id, result.stage)
    previous = _previous_result(path)
    merged = result.model_copy(
        update={"lifetime": merge_lifetime(previous.lifetime if previous else None, result.last_run)}
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(merged.model_dump(mode="json"), sort_keys=False))
    return path
