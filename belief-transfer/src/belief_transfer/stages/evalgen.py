"""The evalgen stage: generate belief/action eval items, judge them, gate them.

One invocation covers every suite the run asks for -- they are one bundle of work from
one config, and a single report covers it, the same shape as datagen. A suite is
generated iff the experiment specs it AND the run supplied its `n_items`; the rest are
recorded in the report as `suites_skipped` rather than passed over silently. That is what
lets one experiment carry three suites while `evalgen_v2` (belief + action, frozen before
the inference suite existed) still reproduces exactly, and lets a new suite be generated
under its own run id without regenerating the frozen ones. API-bound and fully cached; its
GPU-bound counterpart is `stages.sensitivity`, kept separate so items can be regenerated
without a GPU and sensitivity re-measured without re-spending API calls (AGENTS.md, Belief and action suites 5).

Leakage gates against a validated training corpus of this experiment -- an eval run id is
usually not a corpus run id, so the reference cannot be guessed from the job and is named
by `evalgen.leakage_corpus_run_id` (a run overlay overrides it). Absent that corpus,
leakage is skipped and reported as skipped rather than silently passed.
"""

from __future__ import annotations

from pathlib import Path

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import gate as corpus_gate
from belief_transfer.evals import gate, generate, review
from belief_transfer.evals import suite as suite_mod
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import JobConfig, RunResult


def leakage_corpus_path(job: JobConfig) -> Path | None:
    """The validated corpus generated items are shingled against, or None to skip.

    Was the literal `factory_farming_v1` until 2026-08-21, which silently skipped the
    overlap check for any other experiment (the path is built under the experiment's own
    id, so it simply did not exist). `EvalGenSpec.leakage_corpus_run_id` still defaults to
    that run id, so the experiment that had the check keeps it.
    """
    run_id = job.evalgen.leakage_corpus_run_id
    if not run_id:
        return None
    return corpus_gate.validated_documents_path(job.experiment.id, run_id)


async def run(job: JobConfig) -> RunResult:
    experiment = job.experiment
    config = job.eval.evalgen
    if config is None:
        raise ValueError("configs/eval has no `evalgen` block; see AGENTS.md, Belief and action suites")

    generators = {
        "belief": (experiment.belief_eval, generate.generate_belief_items),
        "action": (experiment.action_eval, generate.generate_action_items),
        "inference": (experiment.inference_eval, generate.generate_inference_items),
    }
    specced = {name for name, (spec, _) in generators.items() if spec is not None}
    requested = {
        name: spec.n_items
        for name, (spec, _) in generators.items()
        if spec is not None and spec.n_items
    }
    if not requested:
        raise ValueError(
            f"no suite has n_items set (this experiment specs {sorted(specced)}): a run "
            "overlay supplies e.g. `experiment.belief_eval.n_items` (how many items "
            "belongs to an invocation, not to the experiment)"
        )

    # The leakage reference: the corpus the experiment's checkpoints were trained on.
    # Named by config, since an eval run id is not a corpus run id; skipped (and said so)
    # when absent rather than silently passed.
    corpus_path = leakage_corpus_path(job)
    train_texts = None
    if corpus_path is not None and corpus_path.exists():
        train_texts = [row["text"] for row in suite_mod.load_rows(corpus_path)]

    context = RunContext()
    sha = config_sha(job)
    artifacts = []
    metrics: dict = {
        "gating": {},
        "leakage_reference": str(corpus_path) if train_texts else "SKIPPED (no corpus)",
        "suites_generated": sorted(requested),
        "suites_skipped": sorted(specced - set(requested)),
    }
    total_items = 0

    for suite_name in requested:
        _, generator = generators[suite_name]
        items = await generator(
            experiment, config,
            n_items=requested[suite_name], run_id=job.run_id,
            throughput=job.throughput, force=job.force, context=context,
        )
        items_path = suite_mod.items_path(experiment.id, job.run_id, suite_name)
        suite_mod.write_rows(items, items_path)

        scores = await gate.score_items(
            items, experiment, config,
            throughput=job.throughput, force=job.force, context=context,
        )
        kept, dropped = gate.gate_items(items, scores, config=config, train_texts=train_texts)

        rows = [
            variant
            for item in kept
            for variant in suite_mod.option_variants(item, config.option_labels)
        ]
        suite_path = suite_mod.validated_suite_path(experiment.id, job.run_id, suite_name)
        suite_mod.write_rows(rows, suite_path)

        review_path = suite_mod.review_path(experiment.id, job.run_id, suite_name)
        review.write_review(
            review_path,
            review.render_review(items, scores, kept, dropped, suite=suite_name),
        )

        metrics["gating"][suite_name] = gate.gating_summary(items, kept, dropped)
        artifacts += [items_path, suite_path, review_path]
        total_items += len(items)

    result = build_result(
        context,
        stage="evalgen",
        experiment_id=experiment.id,
        run_id=job.run_id,
        datapoints=total_items,
        artifacts=artifacts,
        metrics=metrics,
        config_sha=sha,
    )
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result
