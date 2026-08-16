"""Cross-backend agreement, as two jobs.

    python run.py +run=adhoc stage=agreement_record   # on the CUDA box
    python run.py +run=adhoc stage=agreement_check    # on the Mac

Scoring runs on CUDA and on Apple silicon, and MLX numbers are only worth anything once
they have been checked against CUDA's. `record` writes the reference fixture; `check`
scores the same items here and compares. See `inference.agreement` for what is compared
and why the thresholds are what they are.

Stages rather than a standalone CLI for the reason everything else here is: a job that
needs a resolved config to build a model is a job, and `inference/` may not reach up to the
config layer to build one itself.
"""

from __future__ import annotations

import json

from belief_transfer.analysis.report import build_result
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.inference import agreement
from belief_transfer.inference.backend import backend_info, detect_backend
from belief_transfer.inference.local import local_model
from belief_transfer.schemas import JobConfig, RunResult


def _result(job: JobConfig, *, stage: str, metrics: dict) -> RunResult:
    # Not written to disk: this measures two backends against each other, not an
    # experiment, and the fixture it produces is the artifact worth keeping.
    return build_result(
        RunContext(),
        stage=stage,
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=len(agreement.ITEMS),
        artifacts=[],
        metrics=metrics,
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )


async def run_record(job: JobConfig) -> RunResult:
    """Score the agreement items here and write the fixture. Commit the result."""
    model = local_model(job.training.model, job.models)
    rows = agreement.score_items(model)
    info = backend_info()

    agreement.FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    agreement.FIXTURE_PATH.write_text(
        json.dumps(
            {"model": job.training.model, "backend": info.model_dump(), "items": rows},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"[agreement] recorded {len(rows)} items on {info.backend} ({info.device})")
    print(f"[agreement] wrote {agreement.FIXTURE_PATH} -- commit it")
    return _result(job, stage="agreement_record", metrics={"agreement": {"recorded": len(rows)}})


async def run_check(job: JobConfig) -> RunResult:
    """Score the agreement items here and compare against the recorded fixture."""
    if not agreement.FIXTURE_PATH.exists():
        raise FileNotFoundError(
            f"no recording at {agreement.FIXTURE_PATH} -- run `stage=agreement_record` on the "
            "other backend first, and commit the fixture"
        )
    recorded = json.loads(agreement.FIXTURE_PATH.read_text())
    there, here = recorded["backend"]["backend"], detect_backend()
    if there == here:
        raise RuntimeError(
            f"the fixture was recorded on {there!r} and this machine is also {here!r}; "
            "there is nothing to compare"
        )

    model = local_model(recorded["model"], job.models)
    problems = agreement.compare(recorded, agreement.score_items(model))

    if problems:
        print(f"[agreement] {here} DISAGREES with {there} on {len(problems)} check(s):")
        for problem in problems:
            print(f"  - {problem}")
        raise RuntimeError(
            f"{here} does not reproduce {there}'s scores; treat results from this backend as "
            "untrustworthy until this passes"
        )

    print(f"[agreement] {here} agrees with {there} on all {len(agreement.ITEMS)} items")
    return _result(
        job,
        stage="agreement_check",
        metrics={"agreement": {"against": there, "problems": [], "passed": True}},
    )
