"""Stages that measure or prepare *this machine*, not an experiment.

Calibration, model downloads, and the tiny-dataset memorization check are jobs in the same
sense every other stage is -- configured by a file, launched by one entrypoint -- but what
they produce belongs to the box rather than to an experiment, so their real output goes to
`configs/hardware_profile.yaml` (gitignored, per-machine) and the `RunResult` they return
is just the record that they ran.

They are registered stages anyway, because the alternative was a second CLI: before this,
`make calibrate` shelled into `python -m belief_transfer.inference.calibrate` with its own
argparse, which is a separate way to launch a job for no reason other than that its output
is not an experimental artifact.
"""

from __future__ import annotations

from belief_transfer.analysis.report import build_result
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.inference import calibrate
from belief_transfer.inference.backend import backend_info
from belief_transfer.schemas import JobConfig, RunResult


def _machine_result(job: JobConfig, *, stage: str, metrics: dict) -> RunResult:
    """A result for a machine-scoped stage.

    Deliberately not written to `data/results/<experiment>/<run>/`: nothing here is about
    an experiment, and filing it there would put a hardware measurement next to belief
    scores as though the two were comparable. The numbers live in the hardware profile.
    """
    return build_result(
        RunContext(),
        stage=stage,
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=len(metrics),
        artifacts=[],
        metrics=metrics,
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )


async def run_download_models(job: JobConfig) -> RunResult:
    """Fetch every model in the models config into the local HF cache.

    A deliberate, separate step rather than something inference does on demand: every path
    that loads a model calls `require_model_cached` first, so a missing model fails with a
    message instead of silently starting a multi-GB download inside a run.
    """
    downloaded = calibrate.download_models(job.models)
    return _machine_result(job, stage="download_models", metrics={"downloaded": downloaded})


async def run_calibrate(job: JobConfig) -> RunResult:
    """Sweep batch size on this GPU and write `configs/hardware_profile.yaml`.

    Discovery, not a check on the model: it records tokens/sec, time-to-first-token, and
    peak VRAM at each size under worst-case-length generation, then picks the largest that
    stays under a VRAM safety margin while still gaining meaningful throughput.
    """
    profile = calibrate.calibrate_models(job.models, [job.training.model])
    return _machine_result(job, stage="calibrate", metrics={"hardware_profile": profile})


async def run_memorization_bench(job: JobConfig) -> RunResult:
    """AGENTS.md's SFT precondition: fine-tune on ~20 arbitrary input->code mappings and
    check the base model fails them while the fine-tuned model nearly memorizes them.

    A benchmark rather than a unit test because what it measures is this machine's
    training stack -- GPU, torch/trl/peft versions, whether LoRA updates land at all.
    """
    results = calibrate.memorization_bench(job.models, [job.training.model])
    return _machine_result(job, stage="memorization_bench", metrics={"memorization": results})
