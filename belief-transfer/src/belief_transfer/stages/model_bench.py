"""Stages that measure a *checkpoint's* ability, as opposed to the machine's capacity.

`perf_bench` asks "is inference wired up correctly on this checkpoint" -- a dozen trivial,
deterministically-checkable prompts any instruction-tuned model should get right, so a low
score means a misconfiguration (chat template, thinking mode, adapter mismatch) rather than
a weak model. `choice_bench` asks "can this checkpoint still answer a forced choice at
all", which every belief eval depends on: a fine-tune strong enough to move a belief can
also destroy the format the belief is measured in, and without this check that collapse
reports as a belief result.

Both are keyed on model+adapter rather than on the machine, which is why they live here
rather than in `stages.machine`, and both should run *after* calibration has picked a batch
size.
"""

from __future__ import annotations

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.benchmarks import run_benchmark
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.schemas import JobConfig, RunResult


async def _run_bench(job: JobConfig, benchmark_id: str, stage: str) -> RunResult:
    """Score one benchmark against every arm the job names that has a checkpoint.

    Reuses `efficacy.arms` rather than introducing a separate list of things to
    benchmark: the arms a job cares about are the same ones whose ability matters, and a
    second list would be a second thing to keep in step.
    """
    from belief_transfer.stages.efficacy import adapter_for

    results: dict[str, dict] = {}
    for arm in job.efficacy.arms:
        adapter = adapter_for(arm, job)
        if adapter is not None and not adapter.exists():
            continue
        model = local_model(job.training.model, job.models, adapter_path=adapter)
        outcome = run_benchmark(
            benchmark_id,
            model,
            model_key=job.training.model,
            adapter=str(adapter) if adapter else None,
        )
        results[arm.name] = outcome.model_dump(mode="json")
        print(
            f"[{benchmark_id}] {arm.name}: {'PASS' if outcome.passed else 'FAIL'} "
            + "  ".join(f"{name}={value:.3f}" for name, value in outcome.metrics.items())
        )
        del model
        free_gpu()

    if not results:
        raise FileNotFoundError(
            f"none of the configured arms have a checkpoint yet -- run `stage=sft` first, "
            f"or set efficacy.arms to just the base arm"
        )

    result = build_result(
        RunContext(),  # local scoring only; no API calls to cost.
        stage=stage,
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=sum(entry["n_items"] for entry in results.values()),
        artifacts=[],
        metrics={benchmark_id: results},
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )
    write_result(result)
    return result


async def run_perf_bench(job: JobConfig) -> RunResult:
    return await _run_bench(job, "perf", "perf_bench")


async def run_choice_bench(job: JobConfig) -> RunResult:
    return await _run_bench(job, "choice", "choice_bench")
