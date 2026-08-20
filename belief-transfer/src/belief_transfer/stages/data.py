"""Data sync stages: mirror `data/` to and from the private HF dataset repo.

Stages rather than a separate CLI for the same reason the benchmarks are: they are jobs
launched by one entrypoint. `data.paths` on the job narrows what moves, because pushing the
whole tree once checkpoints are in it is slow and usually unnecessary.
"""

from __future__ import annotations

from belief_transfer import data_sync
from belief_transfer.analysis.report import build_result
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import JobConfig, RunResult


def _result(job: JobConfig, *, stage: str, metrics: dict) -> RunResult:
    # Not written to disk: a sync moves artifacts, it does not produce an experimental
    # one, and writing a report into data/results/ would itself be unsynced state.
    return build_result(
        RunContext(),
        stage=stage,
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=0,
        artifacts=[],
        metrics=metrics,
        config_sha=config_sha(job),
    )


async def run_push(job: JobConfig) -> RunResult:
    """Upload `data/` (minus the LLM cache) to the HF dataset repo."""
    patterns = data_sync.push_data(repo_id=job.data.repo_id, paths=job.data.paths)
    return _result(job, stage="data_push", metrics={"allow_patterns": patterns})


async def run_pull(job: JobConfig) -> RunResult:
    """Download the HF dataset repo into `data/`."""
    files = data_sync.pull_data(repo_id=job.data.repo_id, paths=job.data.paths)
    return _result(job, stage="data_pull", metrics={
        "allow_patterns": data_sync.allow_patterns(job.data.paths),
        "files_pulled": len(files),
    })
