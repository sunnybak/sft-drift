"""Every job the runner can dispatch, and the registry that maps a name to one.

A stage is `(JobConfig) -> RunResult`: one typed input, one typed output, no argument
parsing and no config loading of its own. That uniformity is what lets `run.py` be ten
lines and lets a script call a stage directly.

The registry is an explicit dict rather than a filesystem scan or an entry-point plugin
system, for the same reason `benchmarks.BENCHMARKS` is: AGENTS.md warns off generic
plugin systems, and with a dozen stages an explicit mapping is shorter, greppable, and
fails at import instead of at run time. `tests/test_stages.py` checks it covers exactly
`schemas.Stage`, so adding a stage without registering it (or the reverse) is a test
failure rather than a runtime surprise.

Imports are deferred inside `_load` because the stages pull in very different
dependencies -- `sft` imports torch and trl, `datagen` imports the OpenAI client -- and
importing this package to look up one stage should not pay for all of them. It also
keeps `python run.py stage=data_pull` working on a machine where torch is not installed.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from belief_transfer.schemas import JobConfig, RunResult, Stage

StageFn = Callable[[JobConfig], Coroutine[Any, Any, RunResult]]

_MODULES: dict[Stage, tuple[str, str]] = {
    "datagen": ("belief_transfer.stages.datagen", "run"),
    "sft": ("belief_transfer.stages.sft", "run"),
    "efficacy": ("belief_transfer.stages.efficacy", "run"),
    "absorption": ("belief_transfer.stages.absorption", "run"),
    "trajectory": ("belief_transfer.stages.trajectory", "run"),
    "report": ("belief_transfer.stages.report", "run"),
    "evalgen": ("belief_transfer.stages.evalgen", "run"),
    "sensitivity": ("belief_transfer.stages.sensitivity", "run"),
    "belief_eval": ("belief_transfer.stages.transfer", "run_belief_eval"),
    "action_eval": ("belief_transfer.stages.transfer", "run_action_eval"),
    "calibrate": ("belief_transfer.stages.machine", "run_calibrate"),
    "download_models": ("belief_transfer.stages.machine", "run_download_models"),
    "memorization_bench": ("belief_transfer.stages.machine", "run_memorization_bench"),
    "perf_bench": ("belief_transfer.stages.model_bench", "run_perf_bench"),
    "choice_bench": ("belief_transfer.stages.model_bench", "run_choice_bench"),
    "agreement_record": ("belief_transfer.stages.agreement", "run_record"),
    "agreement_check": ("belief_transfer.stages.agreement", "run_check"),
    "chat": ("belief_transfer.stages.chat", "run"),
    "data_push": ("belief_transfer.stages.data", "run_push"),
    "data_pull": ("belief_transfer.stages.data", "run_pull"),
}

STAGE_NAMES: tuple[Stage, ...] = tuple(_MODULES)


def load(stage: Stage) -> StageFn:
    """The function implementing `stage`."""
    import importlib

    try:
        module_name, attribute = _MODULES[stage]
    except KeyError:
        known = ", ".join(sorted(_MODULES))
        raise KeyError(f"unknown stage {stage!r} -- known: {known}") from None
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


async def run(job: JobConfig) -> RunResult:
    """Dispatch `job` to its stage."""
    return await load(job.stage)(job)
