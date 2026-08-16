"""The efficacy stage: did the fine-tune absorb its corpus at all?

Efficacy is the *only* metric that may be tuned against. It measures whether the training
landed, not what the experiment concludes, so optimizing it cannot bias the result.
Tuning against a belief or action score would be selecting hyperparameters on the outcome
variable, and any transfer number reported afterwards would be an artifact of that search.

This used to be `evals/__main__.py`: a 478-line CLI with fifteen hyperparameter flags,
which existed because a run config could only override the *experiment* spec and so could
not say `epochs=6`. Now that a job config reaches every knob, the flags are overrides
(`training.sft.epochs=6`) and a sweep is `--multirun training.sft.lr=1e-4,2e-4`.

`arms` being config rather than a hardcoded `{"positive": "m_plus", "negative": "m_minus"}`
dict is what `changelog/2026-08-16.md` asked for: a bare two-arm dE is a contaminated
number, because ~43% of the letter-reading effect turned out to be machinery rather than
content. Folding a matched off-topic control pair (M0+/M0-) into the standard protocol
means naming more than two arms, which `scripts/run_m0_split.py` previously had to work
around by reimplementing this stage.

Sequencing note: this loads a model up to four times and frees it in between rather than
holding several at once, because the box it was written for has 12GB of VRAM and cannot
hold a training model and a scoring model together.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.benchmarks import run_benchmark
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals import efficacy
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.schemas import EfficacyArm, JobConfig, RunResult
from belief_transfer.stages import sft as sft_stage


def score_arm(
    items: list[dict],
    *,
    job: JobConfig,
    adapter: Path | None,
    condition: str,
    continuation: bool,
    choice_bench: bool,
) -> tuple[list[dict], dict[str, Any] | None]:
    """Load one checkpoint, score the item bank (and optionally the MCQ benchmark), free it.

    Public, unlike the `_print_*` helpers this module used to hide, because
    `scripts/` legitimately wants exactly this and was importing it out of a `__main__`.
    """
    model = local_model(job.training.model, adapter_path=adapter)
    adapter_str = str(adapter) if adapter is not None else None
    print(f"[efficacy] scoring {condition} ({adapter_str or 'base checkpoint'}) over {len(items)} rows ...")

    rows = efficacy.score_items(
        model,
        items,
        condition=condition,
        model_tag=job.training.model,
        adapter=adapter_str,
        continuation=continuation,
    )

    bench: dict[str, Any] | None = None
    if choice_bench:
        result = run_benchmark("choice", model, model_key=job.training.model, adapter=adapter_str)
        bench = {
            "passed": result.passed,
            "calibrated": result.calibrated,
            **{name: round(value, 4) for name, value in result.metrics.items()},
        }
        print(
            f"[choice]   {condition}: {'PASS' if result.passed else 'FAIL'} "
            f"accuracy {result.metrics.get('accuracy', float('nan')):.3f} "
            f"confidence {result.metrics.get('mean_confidence', float('nan')):.3f}"
        )

    del model
    free_gpu()
    return rows, bench


def print_conditions(summaries: dict[str, dict[str, Any]], key: str) -> None:
    print(f"\n  {key}")
    print(f"    {'condition':<10} {'score':>7}  {'95% CI':>16}  {'variant gap':>11}")
    for condition, summary in summaries.items():
        low, high = summary["ci95"]
        gap = summary["variant_gap"]
        gap_text = "n/a" if gap is None else f"{gap:.3f}"
        print(f"    {condition:<10} {summary['score']:>7.3f}  [{low:>6.3f}, {high:>6.3f}]  {gap_text:>11}")


def print_delta(label: str, result: dict[str, Any]) -> None:
    low, high = result["ci95"]
    verdict = "EXCLUDES ZERO" if result["excludes_zero"] else "STRADDLES ZERO -- not interpretable"
    print(f"    dE({label}) = {result['delta']:+.3f}  95% CI [{low:+.3f}, {high:+.3f}]  {verdict}")


def adapter_for(arm: EfficacyArm, job: JobConfig) -> Path | None:
    """Where `arm`'s checkpoint lives, or None for the base model.

    An arm may name a different run id than the job's own (that is the point of a
    control arm: M0's checkpoints come from training on the control corpus, while the
    item bank comes from this experiment).
    """
    if arm.polarity is None:
        return None
    run_id = arm.run_id or job.run_id
    experiment_id = arm.experiment or job.experiment.id
    root = job.training_root_for(experiment_id, run_id)
    return root / arm.polarity / arm.checkpoint


async def run(job: JobConfig) -> RunResult:
    """Score every configured arm on the efficacy item bank and report the contrast."""
    experiment = job.experiment
    config = job.eval.efficacy
    items = efficacy.limit_items(efficacy.build_items(experiment, config), job.efficacy.limit)
    items_file = efficacy.write_rows(items, efficacy.items_path(experiment.id, job.run_id))
    n_items = len({row["item_id"] for row in items})
    print(f"[efficacy] {n_items} items x {len(efficacy.VARIANTS)} orders = {len(items)} rows -> {items_file}")

    continuation = config.continuation_enabled and job.efficacy.continuation
    scored_rows: list[dict] = []
    benchmarks: dict[str, Any] = {}
    by_condition: dict[str, list[dict]] = {}

    for arm in job.efficacy.arms:
        adapter = adapter_for(arm, job)
        if adapter is not None and not adapter.exists():
            raise FileNotFoundError(
                f"arm {arm.name!r} expects a checkpoint at {adapter}, which does not exist -- "
                f"run `python run.py +run={arm.run_id or job.run_id} stage=sft` first"
            )
        rows, bench = score_arm(
            items,
            job=job,
            adapter=adapter,
            condition=arm.name,
            continuation=continuation,
            choice_bench=job.efficacy.choice_bench,
        )
        by_condition[arm.name] = rows
        scored_rows += rows
        if bench is not None:
            benchmarks[arm.name] = bench

    keys = ["p_positive"] + (["p_positive_continuation"] if continuation else [])
    conditions_summary = {
        key: {condition: efficacy.aggregate(rows, key=key) for condition, rows in by_condition.items()}
        for key in keys
    }
    deltas = {
        key: efficacy.delta(
            by_condition[job.efficacy.contrast[0]], by_condition[job.efficacy.contrast[1]], key=key
        )
        for key in keys
    }

    responses_file = efficacy.write_rows(
        scored_rows, efficacy.responses_path(experiment.id, job.run_id)
    )
    summary_file = efficacy.summary_path(experiment.id, job.run_id)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(
        yaml.safe_dump(
            {
                "experiment": experiment.id,
                "run_id": job.run_id,
                "model": job.training.model,
                # Recorded so a 2-step result is self-identifying: a summary reporting
                # dE ~ 0 is meaningless if it came from a smoke run, and nothing else in
                # the file says so.
                "smoke": job.smoke,
                "hyperparams": job.training.sft.model_dump(),
                "arms": [arm.model_dump() for arm in job.efficacy.arms],
                "contrast": list(job.efficacy.contrast),
                "n_items": n_items,
                "n_rows": len(items),
                "conditions": conditions_summary,
                "delta": deltas,
                "choice_benchmark": benchmarks,
            },
            sort_keys=False,
        )
    )

    print("\n[efficacy] 0.5 = indifferent between the two arms' figures")
    for key in keys:
        print_conditions(conditions_summary[key], key)
    print(f"\n[efficacy] paired per item, {job.efficacy.contrast[0]} minus {job.efficacy.contrast[1]}:")
    for key in keys:
        print_delta(key, deltas[key])

    artifacts = [items_file, responses_file, summary_file]
    metrics: dict[str, Any] = {
        "efficacy": {
            "conditions": conditions_summary,
            "delta": deltas,
            "choice_benchmark": benchmarks,
            "n_items": n_items,
        }
    }

    if job.efficacy.trajectory:
        trajectory = run_trajectory(items, job=job, continuation=continuation)
        trajectory_file = efficacy.trajectory_path(experiment.id, job.run_id)
        trajectory_file.parent.mkdir(parents=True, exist_ok=True)
        trajectory_file.write_text(json.dumps(trajectory, indent=2))
        artifacts.append(trajectory_file)
        metrics["trajectory"] = trajectory

    result = build_result(
        RunContext(),  # local scoring only; no API calls to cost.
        stage="efficacy",
        experiment_id=experiment.id,
        run_id=job.run_id,
        datapoints=len(scored_rows),
        artifacts=artifacts,
        metrics=metrics,
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result


def run_trajectory(items: list[dict], *, job: JobConfig, continuation: bool) -> list[dict[str, Any]]:
    """Score every saved intermediate checkpoint, not just the final one.

    The capability pass/fail boundary moves per arm and mid-run -- `tune-a9035e51` had M-
    failing choice-bench by step 32 while M+ was still passing at 48 -- so measuring it
    directly beats assuming the endpoint's hyperparameters landed inside it.
    """
    output_root = sft_stage.checkpoint_root(job)
    keys = ["p_positive"] + (["p_positive_continuation"] if continuation else [])
    contrast = job.efficacy.contrast
    trained_arms = [arm for arm in job.efficacy.arms if arm.polarity is not None]
    trajectory: list[dict[str, Any]] = []

    for step in efficacy.checkpoint_steps(output_root):
        by_condition: dict[str, list[dict]] = {}
        benchmarks: dict[str, Any] = {}
        for arm in trained_arms:
            rows, bench = score_arm(
                items,
                job=job,
                adapter=output_root / arm.polarity / f"checkpoint-{step}",
                condition=arm.name,
                continuation=continuation,
                choice_bench=True,
            )
            by_condition[arm.name] = rows
            benchmarks[arm.name] = bench

        deltas = {
            key: efficacy.delta(by_condition[contrast[0]], by_condition[contrast[1]], key=key)
            for key in keys
        }
        both_pass = all(bench["passed"] for bench in benchmarks.values())
        entry: dict[str, Any] = {"step": step, "both_pass": both_pass}
        for name, bench in benchmarks.items():
            entry[f"choice_acc_{name}"] = bench["accuracy"]
            entry[f"choice_pass_{name}"] = bench["passed"]
            entry[f"poscons_{name}"] = bench.get("position_consistency")
        for key in keys:
            suffix = "letter" if key == "p_positive" else "cont"
            entry[f"dE_{suffix}"] = deltas[key]["delta"]
            entry[f"dE_{suffix}_ci"] = list(deltas[key]["ci95"])
        trajectory.append(entry)

        letter_bit = f"dE(letter)={entry['dE_letter']:+.3f}"
        cont_bit = f"  dE(cont)={entry['dE_cont']:+.3f}" if "dE_cont" in entry else ""
        print(f"[trajectory] step {step:>4}  {'PASS' if both_pass else 'FAIL'}  {letter_bit}{cont_bit}")

    passing = [entry["step"] for entry in trajectory if entry["both_pass"]]
    scored = [entry["step"] for entry in trajectory]
    if passing:
        print(f"\n[trajectory] last step where every arm passes choice-bench: {max(passing)} (scored: {scored})")
    else:
        print(f"\n[trajectory] no step passed choice-bench on every arm (scored: {scored})")
    return trajectory
