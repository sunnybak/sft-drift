"""The datagen stage: generate a corpus, judge it, gate it.

One invocation of `run` does all three, because they are one bundle of work from one set
of prompts -- judging is not separately timed from the generation it scores, and the gate
is pure post-processing of those judge scores with no further LLM calls. That is also why
a single report covers all of it (see `analysis.report`).

Replicates are repeated passes over the *same* seeded prompts (`seed_item` is a pure
function of the item index, not the replicate number), so they measure the model's own
sampling variance rather than generating new content. Each pass salts the LLM cache with
its replicate number; without that, every pass after the first would return the first's
cached answer.
"""

from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import gate, generate, score
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import ExperimentConfig, JobConfig, RunResult
from belief_transfer.validation import analyze


async def run(job: JobConfig) -> RunResult:
    """Generate `job.replicates` passes, judge everything, gate it, and report.

    Writes a fresh documents file per invocation rather than appending indefinitely
    across repeated runs of the same run id, then appends one generation pass into it per
    replicate.
    """
    experiment = job.experiment
    documents_path = generate.documents_path(experiment.id, job.run_id)
    documents_path.parent.mkdir(parents=True, exist_ok=True)
    documents_path.write_text("")

    context = RunContext()
    sha = config_sha(job)
    for replicate in range(1, job.replicates + 1):
        await generate.generate_dataset(
            experiment,
            job.dataset,
            run=replicate,
            run_id=job.run_id,
            config_sha=sha,
            out_path=documents_path,
            throughput=job.throughput,
            override_cache=job.force,
            context=context,
        )

    documents = [json.loads(line) for line in documents_path.read_text().splitlines()]

    scores_path = score.scores_path(experiment.id, job.run_id)
    scores = await score.score_dataset(
        experiment,
        job.dataset.judge,
        documents,
        throughput=job.throughput,
        override_cache=job.force,
        context=context,
    )
    score.write_scores(scores, scores_path)

    kept, _dropped = gate.gate_pairs(documents, scores)
    validated_path = gate.validated_documents_path(experiment.id, job.run_id)
    gate.write_gated(kept, validated_path)
    gating = gate.gating_summary(experiment, job.dataset.judge, documents, scores, kept)

    result = build_result(
        context,
        stage="datagen",
        experiment_id=experiment.id,
        run_id=job.run_id,
        datapoints=len(documents),
        artifacts=[documents_path, scores_path, validated_path],
        metrics={
            "gating": gating,
            "analysis": analyze.analyze_corpus(
                experiment,
                documents_path=documents_path,
                scores_path=scores_path,
                orthogonal_to=_orthogonal_experiment(job),
            ),
        },
        config_sha=sha,
    )
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result


def documents_path_for(job: JobConfig) -> Path:
    """Where this job's raw corpus lives. Exposed for scripts that want to read a
    corpus without re-deriving the layout."""
    return generate.documents_path(job.experiment.id, job.run_id)


def _orthogonal_experiment(job: JobConfig) -> ExperimentConfig | None:
    """The experiment this corpus must stay clear of, if it declares one.

    Composed on demand rather than carried on the job: `experiment.orthogonal_to` names
    another config group option, and only this check needs it. Returns None -- skipping the
    check -- rather than failing the run if that option does not exist, since a datagen run
    should not die over a reported statistic.
    """
    if not job.experiment.orthogonal_to:
        return None
    try:
        from belief_transfer.config import load_job

        other = load_job(
            [f"experiment={job.experiment.orthogonal_to}", f"run_id={job.run_id}", "experiment.dataset.n_items=1"]
        )
    except Exception:
        return None
    return other.experiment
