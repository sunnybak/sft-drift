"""stage=report: render this run's results directory as `report.md`.

A stage rather than a script because it is a job configured by a file and launched by the
one entrypoint, and because the thing it produces belongs next to the artifacts it reads.
It measures nothing and loads no model -- run it after the stages whose output it
summarises, as many times as you like.
"""

from __future__ import annotations

from belief_transfer.analysis import markdown
from belief_transfer.analysis.report import RESULTS_DIR, build_result, write_result
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import JobConfig, RunResult


async def run(job: JobConfig) -> RunResult:
    results_dir = RESULTS_DIR / job.experiment.id / job.run_id
    if not results_dir.exists():
        raise FileNotFoundError(
            f"no results at {results_dir} -- run the stages you want reported first"
        )
    out_path = markdown.write_report(results_dir)
    print(f"[report] wrote {out_path}")
    return build_result(
        RunContext(),  # reads files; makes no calls and loads no model.
        stage="report",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=0,
        artifacts=[out_path],
        metrics={"report": {"path": str(out_path)}},
        backend=None,
        config_sha=config_sha(job),
    )
