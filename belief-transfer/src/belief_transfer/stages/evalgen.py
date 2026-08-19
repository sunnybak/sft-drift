"""The evalgen stage: generate belief/action eval items, judge them, gate them.

One invocation covers both suites -- they are one bundle of work from one config, and a
single report covers it, the same shape as datagen. API-bound and fully cached; its
GPU-bound counterpart is `stages.sensitivity`, kept separate so items can be regenerated
without a GPU and sensitivity re-measured without re-spending API calls (AGENTS.md, Belief and action suites 5).

Leakage gates against the experiment's own validated training corpus for THIS run id if
one exists, else the corpus run named by `sensitivity`/efficacy conventions is not
guessed -- an eval run id is usually not a corpus run id, so the leakage reference is
the corpus the experiment's arms were actually trained on, passed as
`evalgen_leakage_corpus` in the run overlay when it matters. Absent that, leakage is
skipped and reported as skipped rather than silently passed.
"""

from __future__ import annotations

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import gate as corpus_gate
from belief_transfer.evals import gate, generate, review
from belief_transfer.evals import suite as suite_mod
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import JobConfig, RunResult


async def run(job: JobConfig) -> RunResult:
    experiment = job.experiment
    config = job.eval.evalgen
    if config is None:
        raise ValueError("configs/eval has no `evalgen` block; see AGENTS.md, Belief and action suites")

    requested = {
        "belief": experiment.belief_eval.n_items if experiment.belief_eval else None,
        "action": experiment.action_eval.n_items if experiment.action_eval else None,
    }
    missing = [name for name, count in requested.items() if not count]
    if missing:
        raise ValueError(
            f"n_items unset for {missing}: a run overlay supplies "
            "`experiment.belief_eval.n_items` and `experiment.action_eval.n_items` "
            "(how many items belongs to an invocation, not to the experiment)"
        )

    # The leakage reference: the corpus the experiment's checkpoints were trained on.
    # factory_farming_v1 is that corpus's run id by convention; skipped (and said so)
    # when absent rather than silently passed.
    corpus_path = corpus_gate.validated_documents_path(experiment.id, "factory_farming_v1")
    train_texts = None
    if corpus_path.exists():
        train_texts = [row["text"] for row in suite_mod.load_rows(corpus_path)]

    context = RunContext()
    sha = config_sha(job)
    artifacts = []
    metrics: dict = {"gating": {}, "leakage_reference": str(corpus_path) if train_texts else "SKIPPED (no corpus)"}
    total_items = 0

    generators = {"belief": generate.generate_belief_items, "action": generate.generate_action_items}
    for suite_name, generator in generators.items():
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
