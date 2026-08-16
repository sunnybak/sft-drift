"""The chat stage: an interactive session against a checkpoint.

A stage because it is a job configured by a file and launched by the one entrypoint, not
because it produces an experimental artifact -- it produces a conversation. Its
`RunResult` records that a session happened and against what, and is not written to disk:
a transcript is not a measurement, and filing one next to belief scores would suggest
otherwise.

Useful precisely because it is the same substrate: `stage=chat chat.adapter=...` talks to
the exact adapter an efficacy run scored, through the same loading path, so "what does M+
actually say" is one command rather than a scratch script.
"""

from __future__ import annotations

from belief_transfer.analysis.report import build_result
from belief_transfer.client.repl import run_chat
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.schemas import JobConfig, RunResult


async def run(job: JobConfig) -> RunResult:
    exit_code = run_chat(job)
    return build_result(
        RunContext(),
        stage="chat",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=0,
        artifacts=[],
        metrics={"chat": {"adapter": job.chat.adapter, "exit_code": exit_code}},
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )
