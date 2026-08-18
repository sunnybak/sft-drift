"""The sft stage: train M+ and M- LoRA checkpoints on a run's gated corpus.

Reads `data/validated/<experiment_id>/<run_id>/documents.jsonl` -- the same run id that a
prior datagen invocation wrote -- so one run id names one pipeline end to end (generate
this corpus, then train on it) rather than needing a second id just to point at the first.

Both arms, always: every transfer metric in AGENTS.md is a contrast between them, and a
single arm is not interpretable on its own.
"""

from __future__ import annotations

from pathlib import Path

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import gate
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.schemas import JobConfig, RunResult
from belief_transfer.training import sft


def checkpoint_root(job: JobConfig) -> Path:
    """Where this job's checkpoints go.

    A smoke run gets its own directory. `train_one_arm` returns an existing `COMPLETED`
    checkpoint in place rather than retraining -- right for resuming an interrupted run,
    but it means a 2-step smoke adapter written under the real run id would later be
    scored as if it were the real thing.
    """
    run_id = f"{job.run_id}-smoke" if job.smoke else job.run_id
    return sft.CHECKPOINTS_DIR / job.experiment.id / run_id


async def run(job: JobConfig) -> RunResult:
    """Train both polarities and report."""
    # Checkpoints always go under this job's own run id; only the corpus may be borrowed.
    corpus_run_id = job.training.corpus_from or job.run_id
    validated_path = gate.validated_documents_path(job.experiment.id, corpus_run_id)
    if not validated_path.exists():
        raise FileNotFoundError(
            f"no gated corpus at {validated_path} -- run `python run.py +run={corpus_run_id}` "
            "(stage=datagen) first, or `make data-pull`"
        )

    output_root = checkpoint_root(job)
    summaries = sft.train(
        job.experiment, job.training, job.model_spec, validated_path, output_root, smoke=job.smoke
    )

    artifacts = [validated_path]
    for polarity, summary in summaries.items():
        artifacts.append(Path(summary["dataset_file"]))
        artifacts.append(output_root / polarity / "final")

    result = build_result(
        # sft makes no LLM calls; an empty context reports all-zero cost/tokens.
        RunContext(),
        stage="sft",
        experiment_id=job.experiment.id,
        run_id=output_root.name,
        datapoints=sum(summary["n_samples"] for summary in summaries.values()),
        artifacts=artifacts,
        metrics={"sft": summaries},
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result
